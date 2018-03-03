"""JSON utility methods."""
from typing import Any, Callable
import datetime
import json

serializers = []


def dumps(obj: Any, default: Callable=None, **kwargs) -> str:
    """Define custom dump method to default serialization."""
    return json.dumps(obj, default=default or serialize, **kwargs)


def serializer(method: Callable) -> Callable:
    """Add method to serialize JSON objects."""
    serializers.append(method)
    return method


def serialize(obj: Any) -> Any:
    """Serialize the given object into a JSON compatible type."""
    for method in serializers:
        obj = method(obj)
    return obj


@serializer
def datetime_serializer(obj: Any) -> str:
    """Serialize datetime objects as string for JSON."""
    if type(obj) is datetime.datetime:
        return obj.strftime('%Y-%m-%dT%H:%M:%S')
    elif type(obj) is datetime.date:
        return obj.strftime('%Y-%m-%d')
    elif type(obj) is datetime.time:
        return obj.strftime('%H:%M:%S')
    return obj
