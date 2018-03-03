"""Define store action types."""
from typing import Any, Type


class DeleteCollection:
    """DeleteCollection action."""

    def __init__(self, collection: 'Collection'=None, context: 'Contex'=None):
        self.collection = collection
        self.context = context


class DeleteRecord:
    """DeleteRecord action."""

    def __init__(self, record: 'Model'=None, context: 'Context'=None):
        self.context = context
        self.record = record


class GetCount:
    """GetCount action."""

    def __init__(self, model: Type['Model'], context: 'Context'=None):
        self.context = context
        self.model = model


class GetRecords:
    """GetRecords action."""

    def __init__(self, model: Type['Model']=None, context: 'Context'=None):
        self.context = context
        self.model = model


class FetchRecord:
    """FetchRecord action."""

    def __init__(self, model: Type['Model']=None, context: 'Context'=None):
        self.context = context
        self.model = model


class SaveCollection:
    """SaveCollection action."""

    def __init__(self, collection: 'Collection'=None, context: 'Context'=None):
        self.collection = collection
        self.context = context


class SaveRecord:
    """SaveRecord action."""

    def __init__(
        self,
        record: 'Model'=None,
        context: 'Context'=None,
    ):
        self.context = context
        self.record = record


class MakeStoreValue:
    """StoreValue action."""

    def __init__(self, value: Any=None, context: 'Context'=None):
        self.context = context
        self.value = value
