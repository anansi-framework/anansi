"""Server utility functions."""
from aiohttp.web import (
    HTTPException,
    HTTPForbidden,
    HTTPNotFound,
    HTTPUnauthorized,
    json_response,
)
from aiohttp_security import (
    authorized_userid,
    permits,
)
from typing import Any, Callable, Type, Union
import datetime
import inspect
import json

from anansi.core.context import (
    Context,
    make_context,
)
from anansi.core.query import Query

SERIALIZERS = {
    datetime.datetime: lambda x: x.strftime('%Y-%m-%dT%H:%M:%S'),
    datetime.date: lambda x: x.strftime('%Y-%m-%d'),
    datetime.time: lambda x: x.strftime('%H:%M:%S'),
}

RESERVED_PARAMS = (
    'distinct',
    'fields',
    'include',
    'limit',
    'locale',
    'namespace',
    'order_by',
    'page_size',
    'page',
    'returning',
    'start',
    'timezone',
)


def add_serializer(typ_: Type, func: Callable):
    """Register a method for a given python type for JSON serialization."""
    SERIALIZERS[typ_] = func


async def dump_collection(collection: 'orb.Collection') -> list:
    """Serialize collection records into basic objects."""
    return await collection.get_state()


def dump_json(obj, default=None, **kwargs):
    """Convert objects to JSON."""
    return json.dumps(obj, default=default or serialize_object, **kwargs)


async def dump_record(record: 'Model') -> dict:
    """Serialize record into a basic dictionary."""
    return await record.get_state()


async def get_values_from_request(
    request: 'aiohttp.web.Request',
    model: Type['Model'],
) -> dict:
    """Extract value data from the request object for the model."""
    request_values = {}
    try:
        request_values.update({
            k: load_param(v)
            for k, v in (await request.post()).items()
        })
    except AttributeError:
        pass

    try:
        request_values.update(await request.json())
    except json.JSONDecodeError:
        pass

    schema = model.__schema__
    values = {
        field: request_values[field]
        for field in schema.fields
        if field in request_values
    }
    return values


def error_response(exception, **kw):
    """Create JSON error response."""
    if isinstance(exception, HTTPException):
        response = {
            'error': type(exception).__name__,
            'description': str(exception)
        }
        status = getattr(exception, 'status', 500)
    else:
        response = {
            'error': 'UnknownServerException',
            'description': 'Unknown server error.'
        }
        status = 500
    return json_response(response, status=status)


async def fetch_record_from_request(
    request: 'aiohttp.web.Request',
    model: Type['Model'],
    *,
    context: 'orb.Context'=None,
    match_key: str='key',
) -> 'Model':
    """Extract record from request path."""
    key = request.match_info[match_key]
    if key.isdigit():
        key = int(key)
    record = await model.fetch(key, context=context)
    if record is None:
        raise HTTPNotFound()
    return record


def load_param(param: str) -> Any:
    """Convert param string to Python value."""
    try:
        return json.loads(param)
    except json.JSONDecodeError:
        return param


async def make_context_from_request(request: 'aiohttp.web.Request') -> Context:
    """Make new context from a request."""
    get_params = dict(request.GET)
    param_context = {
        'scope': {'request': request},
    }
    for word in RESERVED_PARAMS:
        try:
            value = get_params.pop(word)
        except KeyError:
            pass
        else:
            param_context[word] = load_param(value)

    if get_params:
        where = Query()
        for key, value in get_params.items():
            where &= Query(key) == load_param(value)
        param_context['where'] = where

    return make_context(**param_context)


def serialize_object(obj: Any):
    """Convert object to JSON serializable format."""
    func = getattr(obj, '__json__', None)
    if func:
        return func(obj)
    serializer = SERIALIZERS.get(type(obj))
    if serializer:
        return serializer(obj)
    return obj


async def test_permit(
    request: 'aiohttp.web.Request',
    permit: Union[Callable, str],
    context: Context=None,
):
    """Assert the request is properly permitted."""
    if inspect.iscoroutinefunction(permit):
        return await permit(request, context)
    elif callable(permit):
        return permit(request, context)
    elif permit:
        user_id = await authorized_userid(request)
        permitted = await permits(request, permit, context=context)
        if permitted is False:
            if user_id is None:
                raise HTTPUnauthorized()
            raise HTTPForbidden()
    return True
