"""Define Model resource endpoints."""
from aiohttp.web import HTTPForbidden, json_response
from typing import Callable, Type, Union
import logging

from .utils import (
    dump_collection,
    dump_model,
    error_response,
    make_context_from_request,
    test_permit,
)

log = logging.getLogger(__name__)


def add_resource(
    app: 'aiohttp.UrlDispatcher',
    model: Type['Model'],
    path: str=None,
    permits: dict=None,
):
    """Add resource for anansi models."""
    model_path = path or '/{}'.format(model.__schema__.resource_name)
    record_path = '{}/{{key}}'.format(model_path)

    add_record_resource(app, model, path=record_path, permits=permits)
    add_model_resource(app, model, path=model_path, permits=permits)


def add_model_resource(
    app: 'aiohttp.UrlDispatcher',
    model: Type['Model'],
    path: str=None,
    permits: dict=None,
):
    """Add resource endpoint for anansi model."""
    permits = permits or {}
    path = path or '/{}/'.format(model.__schema__.resource_name)

    resource = app.router.add_resource(path)

    resource.add_route(
        'BATCH',
        batch_records_factory(model, permit=permits.get('BATCH')),
    )
    resource.add_route(
        'GET',
        get_records_factory(model, permit=permits.get('GET')),
    )
    resource.add_route(
        'POST',
        post_records_factory(model, permit=permits.get('POST')),
    )

    return resource


def add_record_resource(
    app: 'aiohttp.UrlDispatcher',
    model: Type['Model'],
    path: str=None,
    permits: dict=None,
):
    """Add resource endpoint for aiob records."""
    permits = permits or {}
    path = path or '/{}/{{key}}'.format(model.__schema__.resource_name)
    resource = app.router.add_resource(path)

    resource.add_route(
        'DELETE',
        delete_record_factory(model, permit=permits.get('DELETE')),
    )
    resource.add_route(
        'GET',
        get_record_factory(model, permit=permits.get('GET')),
    )
    resource.add_route(
        'PATCH',
        patch_record_factory(model, permit=permits.get('PATCH')),
    )
    resource.add_route(
        'PUT',
        put_record_factory(model, permit=permits.get('PUT')),
    )


def batch_records_factory(
    model: Type['Model'],
    permit: Union[Callable, str]=None,
):
    """Handle BATCH requests on a model endpoint."""
    async def handler(request):
        pass
    return handler


def delete_record_factory(
    model: Type['Model'],
    permit: Union[Callable, str]=None
):
    """Hanlde DELETE requests on a model endpoint by it's key."""
    async def handler(request):
        pass
    return handler


def get_records_factory(
    model: Type['Model'],
    permit: Union[Callable, str]=None,
):
    """Handle GET requests on a model endpoint."""
    async def handler(request):
        try:
            context = make_context_from_request(request)
            if not await test_permit(request, permit, context=context):
                raise HTTPForbidden()
            records = model.select(context=context)
            response = await dump_collection(records)
            return json_response(response)
        except Exception as e:
            log.exception('Failed: %s', request.path)
            return error_response(e)
    return handler


def get_record_factory(
    model: Type['Model'],
    permit: Union[Callable, str]=None,
):
    """Handle GET requests on a model endpoint by it's key."""
    async def handler(request):
        try:
            key = request.match_info['key']
            if key.isdigit():
                key = int(key)

            context = make_context_from_request(request)
            if not await test_permit(request, permit, context=context):
                raise HTTPForbidden()
            record = await model.fetch(key, context=context)
            response = await dump_model(record)
            return json_response(response)
        except Exception as e:
            log.exception('Failed: GET %s', request.path)
            return error_response(e)
    return handler


def patch_record_factory(
    model: Type['Model'],
    permit: Union[Callable, str]=None,
):
    """Handle PATCH requests on a model endpoint by it's key."""
    async def handler(request):
        pass
    return handler


def post_records_factory(
    model: Type['Model'],
    permit: Union[Callable, str]=None,
):
    """Handle POST requests on a model endpoint."""
    async def handler(request):
        pass
    return handler


def put_record_factory(
    model: Type['Model'],
    permit: Union[Callable, str]=None,
):
    """Handle PUT requests on a model endpoint by it's key."""
    async def handler(request):
        pass
    return handler
