"""Server utility functions."""
from typing import Any, Callable, Union
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


async def dump_model(model: 'Model') -> dict:
    """Serialize record into a basic dictionary."""
    return await model.get_state()


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


def load_param(param: str) -> Any:
    """Convert param string to Python value."""
    try:
        return json.loads(param)
    except json.JSONDecodeError:
        return param


def make_context_from_request(request: 'aiohttp.web.Request') -> Context:
    """Make new context from a request."""
    get_params = dict(request.GET)
    param_context = {}
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
