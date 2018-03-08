"""Server utility functions."""
from aiohttp.web import HTTPNotFound
from typing import Any, Type
import json
import logging

from anansi.core.context import (
    Context,
    make_context,
)
from anansi.core.query import Query

log = logging.getLogger(__name__)

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


async def get_values_from_request(
    request: 'aiohttp.web.Request',
    model: Type['Model'],
) -> dict:
    """Extract value data from the request object for the model."""
    request_values = {}
    request_values.update({
        k: load_param(v)
        for k, v in (await request.post()).items()
    })

    try:
        json_body = await request.json()
    except json.JSONDecodeError:
        pass
    except Exception:  # pragma: no cover
        log.exception('Failed to parse json body.')
    else:
        request_values.update(json_body)

    schema = model.__schema__
    values = {
        field: request_values[field]
        for field in schema.fields
        if field in request_values
    }
    return values


async def fetch_record_from_request(
    request: 'aiohttp.web.Request',
    model: Type['Model'],
    *,
    context: 'anansi.Context'=None,
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
    query_params = dict(request.query)
    param_context = {
        'scope': {'request': request},
    }
    for word in RESERVED_PARAMS:
        try:
            value = query_params.pop(word)
        except KeyError:
            pass
        else:
            param_context[word] = load_param(value)

    if query_params:
        where = Query()
        for key, value in query_params.items():
            where &= Query(key) == load_param(value)
        param_context['where'] = where

    return make_context(**param_context)
