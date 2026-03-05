from typing import Optional

from ninja import Schema


class FileResult(Schema):
    file_id: str
    filename: str
    status: str  # "success" | "error" | "timeout"
    result: Optional[dict] = None
    error: Optional[str] = None


class BulkScreeningResponse(Schema):
    total: int
    succeeded: int
    failed: int
    results: list[FileResult]
