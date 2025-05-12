from typing import List
from pydantic import BaseModel
from rpidrive.models import File, Job, JobKind, JobStatus


class NoFileException(Exception):
    """No file exception"""


class InvalidFileNameException(Exception):
    """Invalid file name exception"""


class CompressDataModel(BaseModel):
    """Data model for job"""

    files: List[str]
    parent: str
    name: str


def create_compress_job(file_pks: List[str], parent: File, name: str) -> Job:
    """Create compress job"""
    if not file_pks or not parent:
        raise NoFileException()

    name = name.strip()
    if not name:
        raise InvalidFileNameException()

    return Job.objects.create(
        kind=JobKind.ZIP,
        description=name,
        data=CompressDataModel(
            files=file_pks,
            parent=str(parent.id),
            name=name,
        ).model_dump(),
        volume_id=parent.volume_id,
        status=JobStatus.IN_QUEUE,
    )
