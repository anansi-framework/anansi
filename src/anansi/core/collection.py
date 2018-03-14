"""Define Collection class."""
import asyncio
from typing import Any, Generator, Type, Union

from ..actions import (
    DeleteCollection,
    FetchCollection,
    FetchCount,
    SaveCollection,
)
from .context import (
    ReturnType,
    make_context,
    make_record_context,
    reverse_order
)
from ..exceptions import (
    CollectionIsNull,
    ReadOnly,
)


class Collection:
    """Collection of model instances."""

    RESERVED_WORDS = {
        'count',
        'first',
        'last',
    }

    def __init__(
        self,
        *,
        collector=None,
        model=None,
        records=None,
        source=None,
        target=None,
        **context
    ):
        self.context = make_context(**context)
        self.collector = collector
        self.source = source
        self.target = target

        self._model = model
        self._records = records

    async def _fetch_from_store(
        self,
        reverse: bool=False,
    ):
        model = self.model
        default_order = model.__schema__.default_order

        context = self.context
        order_by = context.order_by or default_order
        if reverse:
            order_by = reverse_order(order_by)

        record_context = make_context(
            context=context,
            order_by=order_by,
            limit=1,
        )
        action = FetchCollection(model=model, context=record_context)
        store_records = await self.dispatch(action)
        records = make_records(
            model,
            store_records,
            record_context
        )
        try:
            return next(records)
        except StopIteration:
            pass

    async def _gather_from_records(
        self,
        keys,
        default: Any=None,
    ):
        single_key = len(keys) == 1
        for record in self._records:
            values = await record.gather(*keys)
            if single_key:
                yield values[0]
            else:
                yield tuple(values)

    async def _gather_from_store(
        self,
        keys,
        distinct=False,
    ):
        model = self.model
        if model is None:
            raise CollectionIsNull

        values_context = make_context(
            context=self.context,
            distinct=keys if distinct else None,
            fields=keys,
            returning='data',
        )
        action = FetchCollection(model=model, context=values_context)
        records = await self.dispatch(action)

        first_key = keys[0]
        single_key = len(keys) == 1
        for record in records:
            if single_key:
                yield record[first_key]
            else:
                yield tuple(record[key] for key in keys)

    async def _get_record_state(self):
        """Return record states for this collection."""
        if self._records is not None:
            return [await record.dump() for record in self._records]

        action = FetchCollection(model=self.model, context=self.context)
        store_records = await self.dispatch(action)
        return list(map(dict, store_records))

    async def at(self, index: int) -> 'Model':
        """Return the model at a given index."""
        if self._records:
            return self._records[index]
        elif self.model:
            records = await self.get_records()
            return records[index]
        raise IndexError

    def clone(self, **options):
        """Create copy of this collection with any overrides."""
        options.setdefault('context', self.context)
        options.setdefault('collector', self.collector)
        options.setdefault('source', self.source)
        options.setdefault('target', self.target)
        options.setdefault('model', self._model)
        options.setdefault('records', self._records)
        return Collection(**options)

    async def delete(self, **context) -> int:
        """Delete the records in this collection from the store."""
        context.setdefault('context', self.context)
        delete_context = make_context(**context)
        action = DeleteCollection(collection=self, context=delete_context)
        return await self.dispatch(action)

    async def dispatch(self, action: 'Action') -> Any:
        """Dispatch action through the collection store."""
        store = self.context.store
        return await store.dispatch(action)

    async def distinct(self, *keys, default: Any=None) -> set:
        """Return distinct values for the given fields."""
        if self._records:
            task = self._gather_from_records(keys, default=default)
        else:
            task = self._gather_from_store(keys, distinct=True)
        return {value async for value in task}

    async def dump(self) -> list:
        """Return the state of this collection as a simple list."""
        context = self.context
        include = dict(context.include)

        if context.returning is ReturnType.Count:
            include = {'count': None}
        elif not include:
            include = {'records': None}

        state = {}
        if 'count' in include:
            state['count'] = await self.get_count()
        if 'records' in include:
            state['records'] = await self._get_record_state()
        if 'first' in include:
            first = await self.get_first()
            first_state = await first.dump() if first else None
            state['first'] = first_state
        if 'last' in include:
            last = await self.get_last()
            last_state = await last.dump() if last else None
            state['last'] = last_state

        if len(state) == 1 and 'records' in state:
            return state['records']
        return state

    async def gather(self, *keys, default: Any=None) -> list:
        """Return a list of values from each record in the collection."""
        if self._records is not None:
            task = self._gather_from_records(keys, default=default)
        else:
            task = self._gather_from_store(keys)
        return [value async for value in task]

    async def get_count(self) -> int:
        """Return the size of the collection."""
        try:
            return getattr(self, '_count')
        except AttributeError:
            pass

        if self._records is not None:
            count = len(self._records)
        else:
            action = FetchCount(model=self.model, context=self.context)
            count = await self.dispatch(action)

        setattr(self, '_count', count)
        return count

    async def get(self, key: str, default: Any=None) -> Any:
        """Get a value from the collection."""
        curr_key, _, next_key = key.partition('.')

        if curr_key == 'count':
            out = await self.get_count()
        elif curr_key == 'first':
            out = await self.get_first()
        elif curr_key == 'last':
            out = await self.get_last()
        elif curr_key == 'records':
            out = await self.get_records()
        else:
            return await self.get_values(key, default)

        if next_key and out:
            return await out.get(next_key, default)
        return out

    async def get_first(self) -> Any:
        """Return the first record in the collection."""
        try:
            return getattr(self, '_first')
        except AttributeError:
            pass

        if self._records is not None:
            first = self._records[0] if self._records else None
        else:
            first = await self._fetch_from_store()

        setattr(self, '_first', first)
        return first

    async def get_last(self) -> Any:
        """Return the last record in the collection."""
        try:
            return getattr(self, '_last')
        except AttributeError:
            pass

        if self._records is not None:
            last = self._records[-1] if self._records else None
        else:
            last = await self._fetch_from_store(reverse=True)

        setattr(self, '_last', last)
        return last

    async def get_records(self):
        """Return the records for this collection."""
        if self._records is not None:
            return self._records

        context = self.context
        model = self.model
        action = FetchCollection(model=model, context=context)
        store_records = await self.dispatch(action)
        iter_records = make_records(model, store_records, context)
        self._records = list(iter_records)
        return self._records

    async def get_values(self, key: str, default: Any=None) -> tuple:
        """Return a list of values from each record in the collection."""
        records = await self.get_records()
        return [await record.get(key, default) for record in records]

    def refine(self, **context):
        """Refine this collection down with a new context."""
        context.setdefault('context', self.context)
        new_context = make_context(**context)
        return self.clone(context=new_context)

    @property
    def model(self):
        """Return the model the records in this collection represent."""
        from .model import Model
        if type(self._model) is str:
            return Model.find_model(self._model)
        return self._model

    async def save(self, **context) -> int:
        """Delete the records in this collection from the store."""
        context.setdefault('context', self.context)
        save_context = make_context(**context)
        action = SaveCollection(collection=self, context=save_context)
        return await self.dispatch(action)

    async def set(self, key: str, value: Any):
        """Set the value for a given key on each record in the collection."""
        if key in Collection.RESERVED_WORDS:
            raise ReadOnly(key)
        elif self._records:
            is_iterable = type(value) in (list, tuple)
            await asyncio.gather(*(
                record.set(key, value[i] if is_iterable else value)
                for i, record in enumerate(self._records)
            ))
        else:
            raise NotImplementedError('TODO(issue-#11)')

    async def update(self, values: dict, **context):
        """Update records within this collection."""
        if self._records:
            for record in await self.get_records():
                await record.update(values)
                await record.save()
        else:
            raise NotImplementedError('TODO(issue-#10)')


def make_records(
    model: Type['Model'],
    store_records: list,
    context: 'Context'
) -> Generator[Union['Model', dict], None, None]:
    """Convert store records to models."""
    if context.returning == ReturnType.Data:
        for record in map(dict, store_records):
            yield record
    else:
        model_context = make_record_context(context=context)
        for record in store_records:
            yield model(state=dict(record), context=model_context)
