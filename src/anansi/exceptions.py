"""Defines the common anansi exception types."""
from typing import Type


class OrbException(Exception):
    """Base exception class."""

    pass


class CollectionIsNull(OrbException):
    """Raised when accessing values from an empty collection."""

    pass


class CollectorNotFound(OrbException):
    """Raised when accessing a collector but none is available."""

    def __init__(self, model: Type['Model'], collector: str):
        self.collector = collector
        self.model = model


class FieldNotFound(OrbException):
    """Raised when accessing a field but none is available."""

    def __init__(self, model: Type['Model'], field: str):
        self.field = field
        self.model = model


class ModelNotFound(OrbException):
    """Raised when a model is looked up and not found."""

    def __init__(self, model: str):
        self.model = model


class ReadOnly(OrbException):
    """Raised when a read-only field is attempting to be modified."""

    def __init__(self, field: str):
        self.field = field


class ReferenceNotFound(OrbException):
    """Raised when accessing a reference but none is available."""

    def __init__(self, model: Type['Model'], reference: str):
        self.model = model
        self.reference = reference


class StoreNotFound(OrbException):
    """Raised when accessing a store but none is available."""

    pass
