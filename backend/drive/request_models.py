from enum import Enum
from typing import List

from pydantic import BaseModel

class MoveFileStrategy(str, Enum):
    """Strategy available for file move"""
    OVERWRITE = 'overwrite'
    RENAME = 'rename'

class MoveFileRequest(BaseModel):
    """Request data for file move"""
    files: List[str]
    destination: str
    strategy: MoveFileStrategy

class ZipFileRequest(BaseModel):
    """Request data for zipping files"""
    files: List[str]
    destination: str
    filename: str
