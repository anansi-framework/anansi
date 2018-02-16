"""Route factories."""
from aiohttp.web import HTTPForbidden, json_response
from typing import Callable, Type, Union
import logging

from .utils import (
    error_response,
    fetch_record_from_request,
    make_context_from_request,
    test_permit,
)

log = logging.getLogger(__name__)


def model_route_handler(func: Callable):
    """Generate a factory for defining endpoints to process models."""
    def factory(
        model: Type['Model'],
        *,
        context_factory: Callable=None,
        permit: Union[Callable, str]=None,
    ):
        context_factory = context_factory or make_context_from_request

        async def handler(request):
            try:
                context = context_factory(request)
                if not await test_permit(request, permit, context=context):
                    raise HTTPForbidden()
                response = await func(model, context=context)
                return json_response(response)
            except Exception as e:
                msg = 'Failed request. method=%s path=%s'
                log.exception(msg, request.method, request.path)
                return error_response(e)
        return handler
    return factory


def record_route_handler(func: Callable):
    """Generate a factory for defining endpoints to process records."""
    def factory(
        model: Type['Model'],
        *,
        context_factory: Callable=None,
        match_key: str='key',
        permit: Union[Callable, str]=None,
    ):
        context_factory = context_factory or make_context_from_request

        async def handler(request):
            try:
                context = context_factory(request)
                if not await test_permit(request, permit, context=context):
                    raise HTTPForbidden()

                record = await fetch_record_from_request(
                    request,
                    model,
                    match_key=match_key
                )
                response = await func(record, context=context)
                return json_response(response)
            except Exception as e:
                msg = 'Failed request. method=%s path=%s'
                log.exception(msg, request.method, request.path)
                return error_response(e)
        return handler
    return factory
