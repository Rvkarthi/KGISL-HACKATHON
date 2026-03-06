from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import PageNumberPagination, paginate
from ninja_jwt.authentication import JWTAuth

from ats.models import JobDescription
from ats.schemas import (
    ErrorOut,
    JobDescriptionIn,
    JobDescriptionOut,
    JobFilterIn,
    JobListOut,
    MessageOut,
)

router = Router(tags=["Job Descriptions"])
auth = JWTAuth()


# ══════════════════════════════════════════════
# Helper
# ══════════════════════════════════════════════


def _get_own_job(hr, job_id: int) -> JobDescription:
    """Fetch a JD that belongs to the requesting HR — auto 404 otherwise."""
    return get_object_or_404(JobDescription, id=job_id, hr=hr)


def _base_qs(hr):
    """Base queryset: only HR's own jobs, annotated with submission count."""
    return (
        JobDescription.objects.filter(hr=hr)
        .annotate(total_submissions=Count("submissions"))
        .order_by("-created_at")
    )


# ══════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════


@router.post(
    "/",
    response={201: JobDescriptionOut, 400: ErrorOut},
    auth=auth,
    summary="Create a new Job Description",
)
def create_job(request, payload: JobDescriptionIn):
    job = JobDescription.objects.create(
        hr=request.user,
        **payload.model_dump(),
    )
    # re-fetch with annotation
    job = _base_qs(request.user).get(id=job.id)
    return 201, JobDescriptionOut.from_job(job)


@router.get(
    "/",
    response=list[JobListOut],
    auth=auth,
    summary="List all Job Descriptions owned by the authenticated HR",
)
@paginate(PageNumberPagination, page_size=20)
def list_jobs(request, filters: JobFilterIn = JobFilterIn()):
    qs = _base_qs(request.user)

    if filters.is_active is not None:
        qs = qs.filter(is_active=filters.is_active)

    if filters.search:
        qs = qs.filter(
            Q(title__icontains=filters.search) | Q(about__icontains=filters.search)
        )

    return [JobListOut.from_job(job) for job in qs]


@router.get(
    "/{job_id}/",
    response={200: JobDescriptionOut, 404: ErrorOut},
    auth=auth,
    summary="Get a single Job Description",
)
def get_job(request, job_id: int):
    job = _get_own_job(request.user, job_id)
    job = _base_qs(request.user).get(id=job.id)
    return 200, JobDescriptionOut.from_job(job)


@router.put(
    "/{job_id}/",
    response={200: JobDescriptionOut, 400: ErrorOut, 404: ErrorOut},
    auth=auth,
    summary="Full update of a Job Description",
)
def update_job(request, job_id: int, payload: JobDescriptionIn):
    job = _get_own_job(request.user, job_id)

    for field, value in payload.model_dump().items():
        setattr(job, field, value)
    job.save()

    job = _base_qs(request.user).get(id=job.id)
    return 200, JobDescriptionOut.from_job(job)


@router.delete(
    "/{job_id}/",
    response={200: MessageOut, 404: ErrorOut},
    auth=auth,
    summary="Delete a Job Description",
)
def delete_job(request, job_id: int):
    job = _get_own_job(request.user, job_id)
    title = job.title
    job.delete()
    return 200, {"message": f'Job "{title}" deleted successfully'}
