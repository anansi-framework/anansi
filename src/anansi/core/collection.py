"""Define Collection class."""
import asyncio
from typing import Any, Type

from .context import (
    ReturnType,
    make_context,
    make_record_context,
    reverse_order
)
from ..exceptions import ReadOnly

UNDEFINED = -1


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
        self._first = UNDEFINED
        self._last = UNDEFINED
        self._count = UNDEFINED

    def __getitem__(self, index):
        """Return records based on Python get item syntax."""
        if type(index) == slice:
            if self._records:
                return self.clone(records=self._records[index])
            elif index.start is not None and index.stop is not None:
                return self.refine(
                    limit=(index.stop - index.start),
                    start=index.start
                )
            elif index.start is not None:
                return self.refine(start=index.start)
            else:
                return self.refine(limit=index.stop)
        elif self._records:
            return self._records[index]

    def __len__(self):
        """Return length of this collection."""
        if self._records is not None:
            return len(self._records)
        return 0

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
        return await self.context.store.delete_collection(self, delete_context)

    async def distinct(self, *keys, default: Any=None) -> set:
        """Return distinct values for the given fields."""
        if not self._records:
            await self.get_records()  # TODO(replace with backend distinct)
        if len(keys) > 1:
            values = await self.gather_values(*keys, default=default)
            return set(tuple(v) for v in values)
        return set(await self.get_values(keys[0], default=default))

    async def gather_values(self, *keys, default: Any=None) -> tuple:
        """Return a list of values from each record in the collection."""
        if self._records is not None:
            return await asyncio.gather(*(
                record.gather(*keys) for record in self._records
            ))
        return []

    async def get_count(self) -> int:
        """Return the size of the collection."""
        if self._count is not UNDEFINED:
            return self._count
        elif self._records is not None:
            return len(self._records)
        else:
            count_context = make_context(context=self.context)
            self._count = await self.context.store.get_count(
                self.model,
                count_context
            )
            return self._count

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
        if self._first is not UNDEFINED:
            return self._first
        elif self._records is not None:
            try:
                return self._records[0]
            except IndexError:
                return None
        else:
            context = self.context
            model = self.model
            first_context = make_context(
                context=context,
                order_by=context.order_by or model.__schema__.default_order,
                limit=1
            )
            store_records = await self.context.store.get_records(
                model,
                first_context
            )
            records = make_records(
                model,
                store_records,
                first_context
            )
            try:
                self._first = records[0]
            except IndexError:
                self._first = None
            return self._first
        return None

    async def get_last(self) -> Any:
        """Return the last record in the collection."""
        if self._last is not UNDEFINED:
            return self._last
        if self._records is not None:
            try:
                return self._records[-1]
            except IndexError:
                return None
        else:
            model = self.model
            context = self.context
            last_context = make_context(
                limit=1,
                order_by=reverse_order(
                    context.order_by or
                    model.__schema__.default_order
                ),
                context=context
            )
            store_records = await self.context.store.get_records(
                model,
                last_context
            )
            records = make_records(
                model,
                store_records,
                last_context
            )
            try:
                self._last = records[0]
            except IndexError:
                self._last = None
            return self._last

    async def get_records(self):
        """Return the records for this collection."""
        if self._records is not None:
            return self._records

        context = self.context
        model = self.model
        store_records = await context.store.get_records(model, context)
        self._records = make_records(model, store_records, context)
        return self._records

    async def get_state(self) -> list:
        """Return the state of this collection as a simple list."""
        context = self.context

        if context.returning is ReturnType.Count:
            count = await self.get_count()
            return {
                'count': count,
            }

        elif self._records is not None:
            return await asyncio.gather(
                *(record.get_state() for record in self._records)
            )

        model = self.model
        store_records = await context.store.get_records(model, context)
        return [dict(record) for record in store_records]

    async def get_values(self, key: str, default: Any=None) -> tuple:
        """Return a list of values from each record in the collection."""
        if self._records is not None:
            return await asyncio.gather(*(
                record.get(key, default) for record in self._records
            ))
        return []

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
        return await self.context.store.save_collection(self, save_context)

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


def make_records(
    model: Type['Model'],
    store_records: list,
    context: 'Context'
) -> list:
    """Convert store records to models."""
    if context.returning == ReturnType.Records:
        model_context = make_record_context(context=context)
        return [
            model(state=dict(record), context=model_context)
            for record in store_records
        ]
    return [dict(record) for record in store_records]
