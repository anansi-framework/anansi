"""Route factories."""
from aiohttp.web import HTTPException, HTTPForbidden, json_response
from aiohttp_security import permits
from typing import Callable, Type, Union
import logging

from .request_helpers import (
    fetch_record_from_request,
    make_context_from_request,
)
from ..utils import json

log = logging.getLogger(__name__)


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


def model_route_factory(func: Callable):
    """Generate a factory for defining endpoints to process models."""
    def factory(
        model: Type['Model'],
        *,
        context_factory: Callable=None,
        dumps: Callable=None,
        permit: Union[Callable, str]=None,
    ):
        context_factory = context_factory or make_context_from_request
        dumps = dumps or json.dumps

        async def handler(request):
            try:
                context = await context_factory(request)
                permitted = (
                    permit is None or
                    await permits(request, permit, context=context)
                )
                if not permitted:
                    raise HTTPForbidden()
                response = await func(model, context=context)
                return json_response(response, dumps=dumps)
            except Exception as e:
                msg = 'Failed request. method=%s path=%s'
                log.exception(msg, request.method, request.path)
                return error_response(e)
        return handler
    return factory


def record_route_factory(func: Callable):
    """Generate a factory for defining endpoints to process records."""
    def factory(
        model: Type['Model'],
        *,
        context_factory: Callable=None,
        dumps: Callable=None,
        match_key: str='key',
        permit: Union[Callable, str]=None,
    ):
        context_factory = context_factory or make_context_from_request
        dumps = dumps or json.dumps

        async def handler(request):
            try:
                context = await context_factory(request)
                permitted = (
                    permit is None or
                    await permits(request, permit, context=context)
                )
                if not permitted:
                    raise HTTPForbidden()

                record = await fetch_record_from_request(
                    request,
                    model,
                    match_key=match_key,
                    context=context,
                )
                response = await func(record, context=context)
                return json_response(response, dumps=dumps)
            except Exception as e:
                msg = 'Failed request. method=%s path=%s'
                log.exception(msg, request.method, request.path)
                return error_response(e)
        return handler
    return factory
