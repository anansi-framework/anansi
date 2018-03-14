"""Collection based actions."""
from typing import Type


class DeleteCollection:
    """DeleteCollection action."""

    def __init__(self, collection: 'Collection'=None, context: 'Contex'=None):
        self.collection = collection
        self.context = context


class FetchCollection:
    """GetRecords action."""

    def __init__(self, model: Type['Model']=None, context: 'Context'=None):
        self.context = context
        self.model = model


class FetchCount:
    """GetCount action."""

    def __init__(self, model: Type['Model'], context: 'Context'=None):
        self.context = context
        self.model = model


class SaveCollection:
    """SaveCollection action."""

    def __init__(self, collection: 'Collection'=None, context: 'Context'=None):
        self.collection = collection
        self.context = context
