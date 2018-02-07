"""Define Model resource endpoints."""
from typing import List, Type

from aiohttp.web import json_response

from .utils import (
    make_context_from_request,
    serialize_collection,
    serialize_model,
)


def batch_records(model: Type['Model']):
    """Handle BATCH requests on a model endpoint."""
    async def handler(request):
        pass
    return handler


def delete_record(model: Type['Model']):
    """Hanlde DELETE requests on a model endpoint by it's key."""
    async def handler(request):
        pass
    return handler


def get_records(model: Type['Model']):
    """Handle GET requests on a model endpoint."""
    async def handler(request):
        context = await make_context_from_request(request)
        records = model.select(context=context)
        response = await serialize_collection(records)
        return json_response(response)
    return handler


def get_record(model: Type['Model']):
    """Handle GET requests on a model endpoint by it's key."""
    async def handler(request):
        key = request.match_info['key']
        if key.isdigit():
            key = int(key)

        context = await make_context_from_request(request)
        record = await model.fetch(key, context=context)
        response = await serialize_model(record)
        return json_response(response)
    return handler


def patch_record(model: Type['Model']):
    """Handle PATCH requests on a model endpoint by it's key."""
    async def handler(request):
        pass
    return handler


def post_records(request):
    """Handle POST requests on a model endpoint."""
    async def handler(request):
        pass
    return handler


def put_record(request):
    """Handle PUT requests on a model endpoint by it's key."""
    async def handler(request):
        pass
    return handler


def add_model_resource(
    app: 'aiohttp.UrlDispatcher',
    model: Type['Model'],
    path: str=None,
):
    """Add resource endpoint for anansi model."""
    path = path or '/{}/'.format(model.__schema__.resource_name)

    resource = app.router.add_resource(path)

    resource.add_route('BATCH', batch_records(model))
    resource.add_route('GET', get_records(model))
    resource.add_route('POST', post_records(model))

    return resource


def add_record_resource(
    app: 'aiohttp.UrlDispatcher',
    model: Type['Model'],
    path: str=None,
):
    """Add resource endpoint for aiob records."""
    path = path or '/{}/{{key}}'.format(model.__schema__.resource_name)
    resource = app.router.add_resource(path)

    resource.add_route('DELETE', delete_record(model))
    resource.add_route('GET', get_record(model))
    resource.add_route('PATCH', patch_record(model))
    resource.add_route('PUT', put_record(model))


def add_resource(
    app: 'aiohttp.UrlDispatcher',
    model: Type['Model'],
    path: str=None,
):
    """Add resource for anansi models."""
    path = path or '/{}'.format(model.__schema__.resource_name)
    add_record_resource(app, model, path='{}/{{key}}'.format(path))
    add_model_resource(app, model, path=path)


def add_resources(app: 'aiohttp.UrlDispatcher', models: List[Type['Model']]):
    """Add multiple resources at once to the application."""
    for model in models:
        add_resource(app, model)
