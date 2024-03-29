from django.core.cache import cache
from django.db.models import Model

class ModelCache:
    """Class for handling Model object cache"""

    @classmethod
    def _construct_key(cls, obj: Model) -> str:
        cls_name = ".".join([obj.__module__, obj.__class__.__name__])
        return f'{cls_name}@{obj.pk}'

    @classmethod
    def clear(cls, obj: Model):
        """Clear data by object"""
        cache.delete(cls._construct_key(obj))

    @classmethod
    def exists(cls, obj: Model) -> bool:
        """Exists object"""
        return cache.has_key(cls._construct_key(obj))

    @classmethod
    def set(cls, obj: Model, data):
        """Set data to object"""
        cache.set(cls._construct_key(obj), data)

    @classmethod
    def get(cls, obj: Model):
        """Get data by object"""
        return cache.get(cls._construct_key(obj))
