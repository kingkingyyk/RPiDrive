from os import stat


from django.core.cache import cache
from django.db.models import Model

class ModelCache:

    @classmethod
    def construct_key(cls, obj: Model) -> str:
        cls_name = ".".join([obj.__module__, obj.__class__.__name__])
        return f'{cls_name}@{obj.pk}'

    @classmethod
    def clear(cls, obj: Model):
        cache.delete(cls.construct_key(obj))

    @classmethod
    def exists(cls, obj: Model) -> bool:
        return cache.has_key(cls.construct_key(obj))

    @classmethod
    def set(cls, obj: Model, data):
        cache.set(cls.construct_key(obj), data)

    @classmethod
    def get(cls, obj: Model):
        return cache.get(cls.construct_key(obj))
