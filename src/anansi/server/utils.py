"""Server utility functions."""
from anansi.core.context import (
    Context,
    ReturnType,
    make_context,
)
from anansi.core.query import Query


async def make_context_from_request(request: 'aiohttp.web.Request') -> Context:
    """Make new context from a request."""
    request_params = dict(request.GET)
    param_context = {}

    fields = request_params.pop('fields', [])
    if fields:
        param_context['fields'] = fields.split(',')

    returning = request_params.pop('returning', None)
    if returning is not None:
        param_context['returning'] = ReturnType(returning)

    limit = request_params.pop('limit', None)
    if limit is not None:
        param_context['limit'] = int(limit)

    if request_params:
        where = Query()
        for key, value in request_params.items():
            where &= Query(key) == value
        param_context['where'] = where

    return make_context(**param_context)


async def serialize_collection(collection: 'orb.Collection') -> list:
    """Serialize collection records into basic objects."""
    return await collection.get_state()


async def serialize_model(model: 'Model') -> dict:
    """Serialize record into a basic dictionary."""
    return await model.get_state()
