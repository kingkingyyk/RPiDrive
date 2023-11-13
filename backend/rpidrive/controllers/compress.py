from typing import List
from pydantic import BaseModel
from rpidrive.models import File, Job, JobKind, JobStatus


class CompressDataModel(BaseModel):
    """Data model for job"""

    files: List[str]
    parent: str
    name: str


def create_compress_job(file_pks: List[str], parent: File, name: str) -> Job:
    """Create compress job"""
    return Job.objects.create(
        kind=JobKind.ZIP,
        description=name,
        data=CompressDataModel(
            files=file_pks,
            parent=str(parent.pk),
            name=name,
        ).model_dump(),
        volume_id=parent.volume_id,
        status=JobStatus.IN_QUEUE,
    )
