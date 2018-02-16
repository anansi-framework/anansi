"""Server utility functions."""
from aiohttp.web import (
    HTTPException,
    HTTPForbidden,
    HTTPUnauthorized,
    json_response,
)
from aiohttp_security import (
    authorized_userid,
    permits,
)
from typing import Any, Callable, Type, Union
import inspect
import json

from anansi.core.context import (
    Context,
    make_context,
)
from anansi.core.query import Query

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


async def dump_collection(collection: 'orb.Collection') -> list:
    """Serialize collection records into basic objects."""
    return await collection.get_state()


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
    return await model.fetch(key, context=context)


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
