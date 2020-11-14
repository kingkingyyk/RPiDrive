import graphene, traceback
from graphene_django import DjangoObjectType
from .utils.indexer import LocalStorageProviderIndexer
from .models import *

class StorageProviderQType(DjangoObjectType):
    class Meta:
        model = StorageProvider
        fields = ('id', 'name', 'type', 'path')

class LocalFileObjectQType(DjangoObjectType):
    class Meta:
        model = LocalFileObject
        fields = ('id', 'name', 'obj_type', 'parent', 'children', 'storage_provider', 'type')

class Query(graphene.ObjectType):
    storage_providers = graphene.List(StorageProviderQType)
    local_file_objects = graphene.List(LocalFileObjectQType)

    def resolve_category_by_name(root, info, name):
        return {'name', name}

schema = graphene.Schema(query=Query)