import os
import re

# https://stackoverflow.com/questions/33208849/python-django-streaming-video-mp4-file-using-httpresponse/33964547

range_re = re.compile(r"bytes\s*=\s*(\d+)\s*-\s*(\d*)", re.I)


class RangeFileWrapper:
    """Wrapper for files returned in a byte range"""

    def __init__(self, filelike, chunk_size=8192, offset=0, length=None):
        self.filelike = filelike
        self.filelike.seek(offset, os.SEEK_SET)
        self.remaining = length
        self.chunk_size = chunk_size

    def close(self):
        """Close response"""
        if hasattr(self.filelike, "close"):
            self.filelike.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining is None:
            data = self.filelike.read(self.chunk_size)
            if data:
                return data
            raise StopIteration()

        if self.remaining <= 0:
            raise StopIteration()
        data = self.filelike.read(min(self.remaining, self.chunk_size))
        if not data:
            raise StopIteration()
        self.remaining -= len(data)
        return data
