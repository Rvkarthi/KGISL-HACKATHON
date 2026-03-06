# concurent
import json
import os
import uuid
from concurrent.futures import (
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    TimeoutError,
    as_completed,
)

from ats_engine.parser.main import parse

# custom
from ats_engine.parser.mparser import parse_resume
from ats_engine.parser.sparser import ResumeParser
from ninja import File, Router
from ninja.errors import HttpError
from ninja.files import UploadedFile
from ninja_jwt.authentication import JWTAuth

from ats.schemas import BulkScreeningResponse, FileResult, HRRequest

router = Router()


@router.post("/parser", response={200: dict, 400: dict})
def parser_pdf(request, pdf_file: UploadedFile = File(...)) -> dict:

    try:
        half_parser = parse_resume(pdf_file.read())
        result = ResumeParser(half_parser).parse()
        return result
    except Exception as error:
        raise HttpError(status_code=500, message=str(error))


@router.post("/screening", response={200: dict, 400: dict})
def resume_screening(
    request, hr_req: HRRequest, pdf_file: UploadedFile = File(...)
) -> dict:

    try:
        hr_req = hr_req.dict()
        result = parse(pdf_file.read(), hr_req)
        return result
    except Exception as error:
        raise HttpError(status_code=500, message=str(error))


# --------------------------------------------------------------------------------------------------
#                         Bulk screeing
# --------------------------------------------------------------------------------------------------

# ── Config ────────────────────────────────────────────────────────────────────
MAX_WORKERS = 4
MAX_FILES = 20
MAX_FILE_SIZE_MB = 10
TASK_TIMEOUT_SEC = 60
USE_MULTIPROCESS = os.name != "nt"


def _process_one(
    file_bytes: bytes, filename: str, file_id: str, hr_req: dict
) -> FileResult:
    """
    Worker function — safe for both ProcessPoolExecutor and ThreadPoolExecutor.

    On Windows with spawn, Django is NOT initialized in child processes.
    We call django.setup() here before touching any Django import.
    On Linux (fork) or in threads, django.setup() is already done — the try/except
    RuntimeError handles the "already configured" case safely.
    """
    if USE_MULTIPROCESS:
        import django

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")  # ← adjust
        try:
            django.setup()
        except RuntimeError:
            pass

    try:
        result = parse(file_bytes, hr_req=hr_req)
        return FileResult(
            file_id=file_id,
            filename=filename,
            status="success",
            result=result,
        )
    except Exception as exc:
        return FileResult(
            file_id=file_id,
            filename=filename,
            status="error",
            error=str(exc),
        )


def _get_executor(n_workers: int):
    """
    ProcessPoolExecutor on Linux/macOS → true parallelism, bypasses GIL.
    ThreadPoolExecutor on Windows      → Django-safe, still parallel for I/O.
    """
    if USE_MULTIPROCESS:
        return ProcessPoolExecutor(max_workers=n_workers)
    return ThreadPoolExecutor(max_workers=n_workers)


# ── Endpoint ──────────────────────────────────────────────────────────────────
@router.post(
    "/screening/bulk",
    response={200: BulkScreeningResponse, 400: dict},
    summary="Screen multiple resumes in parallel",
)
def bulk_resume_screening(
    request,
    hr_req: HRRequest,
    pdf_files: list[UploadedFile] = File(...),
) -> BulkScreeningResponse:
    hr_req = hr_req.dict()
    # ── Validation ────────────────────────────────────────────────────────────
    if not pdf_files:
        raise HttpError(400, "No files uploaded.")
    if len(pdf_files) > MAX_FILES:
        raise HttpError(400, f"Too many files. Maximum allowed: {MAX_FILES}.")

    oversized = [
        f.name for f in pdf_files if f.size and f.size > MAX_FILE_SIZE_MB * 1024 * 1024
    ]
    if oversized:
        raise HttpError(
            400, f"Files exceed {MAX_FILE_SIZE_MB} MB limit: {', '.join(oversized)}"
        )

    # ── Read bytes in main process (UploadedFile is NOT picklable) ────────────
    tasks: list[tuple[bytes, str, str, dict]] = []
    for upload in pdf_files:
        try:
            raw = upload.read()
        except Exception as exc:
            raise HttpError(400, f"Could not read file '{upload.name}': {exc}")
        tasks.append((raw, upload.name, str(uuid.uuid4()), hr_req))

    # ── Parallel execution ────────────────────────────────────────────────────
    results: list[FileResult] = []
    n_workers = min(MAX_WORKERS, len(tasks))
    # added job dis
    with _get_executor(n_workers) as executor:
        future_map = {
            executor.submit(_process_one, raw, name, fid, hr_req=jd): (name, fid)
            for raw, name, fid, jd in tasks
        }

        for future in as_completed(future_map, timeout=TASK_TIMEOUT_SEC * len(tasks)):
            name, fid = future_map[future]
            try:
                file_result: FileResult = future.result(timeout=TASK_TIMEOUT_SEC)
            except TimeoutError:
                file_result = FileResult(
                    file_id=fid,
                    filename=name,
                    status="timeout",
                    error=f"Processing exceeded {TASK_TIMEOUT_SEC}s timeout.",
                )
            except Exception as exc:
                file_result = FileResult(
                    file_id=fid,
                    filename=name,
                    status="error",
                    error=str(exc),
                )

            results.append(file_result)

    # ── Aggregate ─────────────────────────────────────────────────────────────
    succeeded = sum(1 for r in results if r.status == "success")
    return BulkScreeningResponse(
        total=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
    )
