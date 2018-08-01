"""Define Model resource endpoints."""
from typing import Callable, Type
import logging

from .factories import (
    model_route_factory,
    record_route_factory,
)
from .request_helpers import get_values_from_request

log = logging.getLogger(__name__)


def add_resource(
    app: 'aiohttp.UrlDispatcher',
    model: Type['Model'],
    *,
    base_url: str='',
    context_factory: Callable=None,
    dumps: Callable=None,
    path: str=None,
    permits: dict=None,
    store: 'Store'=None,
):
    """Add resource for anansi models."""
    model_path = path or '{}/{}'.format(
        base_url,
        model.__schema__.resource_name,
    )
    record_path = '{}/{{key}}'.format(model_path)

    add_record_resource(
        app,
        model,
        base_url=base_url,
        context_factory=context_factory,
        dumps=dumps,
        path=record_path,
        permits=permits,
        store=store,
    )
    add_model_resource(
        app,
        model,
        base_url=base_url,
        context_factory=context_factory,
        dumps=dumps,
        path=model_path,
        permits=permits,
        store=store,
    )


def add_model_resource(
    app: 'aiohttp.UrlDispatcher',
    model: Type['Model'],
    *,
    base_url: str='',
    context_factory: Callable=None,
    dumps: Callable=None,
    path: str=None,
    permits: dict=None,
    store: 'Store'=None,
):
    """Add resource endpoint for anansi model."""
    permits = permits or {}
    path = path or '{}/{}'.format(base_url, model.__schema__.resource_name)

    resource = app.router.add_resource(path)
    get_route = resource.add_route('GET', get_records(
        model,
        context_factory=context_factory,
        dumps=dumps,
        permit=permits.get('GET'),
        store=store,
    ))
    post_route = resource.add_route('POST', create_record(
        model,
        context_factory=context_factory,
        dumps=dumps,
        permit=permits.get('POST'),
        store=store,
    ))
    patch_route = resource.add_route('PATCH', update_records(
        model,
        context_factory=context_factory,
        dumps=dumps,
        permit=permits.get('PATCH'),
        store=store,
    ))
    put_route = resource.add_route('PUT', update_records(
        model,
        context_factory=context_factory,
        dumps=dumps,
        permit=permits.get('PUT'),
        store=store,
    ))

    try:
        cors = app['aiohttp_cors']
    except KeyError:
        pass
    else:
        cors.add(resource)
        cors.add(get_route)
        cors.add(post_route)
        cors.add(patch_route)
        cors.add(put_route)

    return resource


def add_record_resource(
    app: 'aiohttp.UrlDispatcher',
    model: Type['Model'],
    *,
    base_url: str='',
    context_factory: Callable=None,
    dumps: Callable=None,
    path: str=None,
    permits: dict=None,
    store: 'Store'=None,
):
    """Add resource endpoint for aiob records."""
    permits = permits or {}
    path = path or '{}/{}/{{key}}'.format(
        base_url,
        model.__schema__.resource_name,
    )

    resource = app.router.add_resource(path)
    delete_route = resource.add_route('DELETE', delete_record(
        model,
        context_factory=context_factory,
        dumps=dumps,
        permit=permits.get('DELETE'),
        store=store,
    ))
    get_route = resource.add_route('GET', get_record(
        model,
        context_factory=context_factory,
        dumps=dumps,
        permit=permits.get('GET'),
        store=store,
    ))
    patch_route = resource.add_route('PATCH', update_record(
        model,
        context_factory=context_factory,
        dumps=dumps,
        permit=permits.get('PATCH'),
        store=store,
    ))
    put_route = resource.add_route('PUT', update_record(
        model,
        context_factory=context_factory,
        dumps=dumps,
        permit=permits.get('PUT'),
        store=store,
    ))

    try:
        cors = app['aiohttp_cors']
    except KeyError:
        pass
    else:
        cors.add(resource)
        cors.add(delete_route)
        cors.add(get_route)
        cors.add(patch_route)
        cors.add(put_route)


@model_route_factory
async def create_record(
    model: Type['Model'],
    context: 'anansi.Context'=None,
) -> dict:
    """Create a new record based on request values."""
    values = await get_values_from_request(
        context.scope['request'],
        model,
    )
    record = model(values, context=context)
    await record.save()
    return await record.dump()


@record_route_factory
async def delete_record(record, context=None):
    """Handle DELETE request for a record."""
    await record.delete()
    return {'status': 'ok'}


@model_route_factory
async def get_records(
    model: Type['Model'],
    context: 'anansi.Context'=None,
) -> list:
    """Handle GET endpoint for models."""
    collection = await model.select(context=context)
    return await collection.dump()


@record_route_factory
async def get_record(record: 'Model', context: 'anansi.Context'=None) -> dict:
    """Serialize a record and return it."""
    return await record.dump()


@record_route_factory
async def update_record(
    record: 'Model',
    context: 'anansi.Context'=None,
) -> dict:
    """Update a record in the database and return it."""
    values = await get_values_from_request(
        context.scope['request'],
        type(record),
    )
    await record.update(values)
    await record.save()
    return await record.dump()


@model_route_factory
async def update_records(
    model: Type['Model'],
    context: 'anansi.Context'=None,
) -> list:
    """Update a set of records to a set of values."""
    values = await get_values_from_request(
        context.scope['request'],
        model,
    )
    collection = await model.select(context=context)
    await collection.update(values)
    return await collection.dump()
