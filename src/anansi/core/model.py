"""Define Model class."""

from collections import OrderedDict
from typing import Any, Callable, Dict, Tuple, Union
import asyncio

from ..exceptions import (
    CollectorNotFound,
    FieldNotFound,
    ReferenceNotFound,
)
from ..utils import is_equal
from .collector import Collector
from .collection import Collection
from .context import ReturnType, make_context
from .field import Field
from .model_type import ModelType
from .reference import Reference
from ..exceptions import ReadOnly


class Model(metaclass=ModelType):
    """Define Model class."""

    __abstract__ = True
    __schema__ = None
    __store__ = None
    __view__ = False

    def __init__(
        self,
        values: dict=None,
        state: dict=None,
        **context
    ):
        context.setdefault('store', type(self).__store__)
        self.context = make_context(**context)
        self._state = {}
        self._changes = {}
        self._collections = {}
        self._references = {}

        # apply base state
        self._init_state(state)
        self._init_changes(values)

    def _parse_values(
        self,
        values: dict,
        constructor: Callable=None,
    ) -> Tuple[dict, dict, dict]:
        fields = {}
        references = {}
        collections = {}
        schema = self.__schema__
        for key, value in values.items():
            schema_object = schema[key]

            if isinstance(schema_object, Field):
                if not schema_object.test_flag(Field.Flags.Virtual):
                    fields[key] = value

            elif isinstance(schema_object, Collector):
                collections[key] = schema_object.make_collection(
                    constructor=constructor,
                    records=value,
                    source=self
                )

            elif isinstance(schema_object, Reference):
                model = schema_object.model
                if not isinstance(value, model):
                    references[key] = model(values=value)
                else:
                    references[key] = value

        return fields, references, collections

    def _init_changes(self, values: dict):
        if self.is_new:
            self._changes.update(self.__schema__.default_values)

        if values:
            model = type(self)

            def make_record(values):
                return model(values=values)

            fields, references, collections = self._parse_values(
                values,
                constructor=make_record,
            )
            self._changes.update(fields)
            self._references.update(references)
            self._collections.update(collections)

    def _init_state(self, state: dict):
        if state:
            model = type(self)

            def make_record(state):
                return model(state=state)

            fields, references, collections = self._parse_values(
                state,
                constructor=make_record,
            )
            self._state.update(fields)
            self._references.update(references)
            self._collections.update(collections)

    async def delete(self, **context):
        """Delete this record from it's store."""
        if type(self).__view__:
            raise ReadOnly(type(self).__name__)
        else:
            context.setdefault('context', self.context)
            delete_context = make_context(**context)
            return await self.context.store.delete_record(self, delete_context)

    async def dump(self) -> dict:
        """Return the state of this model as a dictionary."""
        fields = self.__schema__.fields.keys()
        values = await self.gather(*fields)
        return dict(zip(fields, values))

    async def gather(self, *keys, state: dict=None) -> tuple:
        """Return a list of values for the given keys."""
        state = state or {}
        return await asyncio.gather(*(
            self.get(key, default=state.get(key))
            for key in keys
        ))

    async def get(self, key: str, default: Any=None) -> Any:
        """Return a single value from this record."""
        curr_key, _, next_key = key.partition('.')
        try:
            schema_object = self.__schema__[curr_key]
        except KeyError:
            raise FieldNotFound(type(self), curr_key)

        if isinstance(schema_object, Reference):
            result = await self.get_reference(curr_key, default)
        elif isinstance(schema_object, Collector):
            result = await self.get_collection(curr_key, default)
        else:
            result = await self.get_value(curr_key, default)

        if next_key and result is not None:
            return await result.get(next_key)
        return result

    async def get_collection(self, key: str, default: Any=None) -> Any:
        """Return a collection from this record."""
        try:
            collector = self.__schema__.collectors[key]
        except KeyError:
            raise CollectorNotFound(type(self), key)

        try:
            return self._collections[key]
        except KeyError:
            pass

        collection = await collector.collect(self)
        self._collections[key] = collection
        return collection

    async def get_key(self) -> Any:
        """Return the unique key for this model."""
        out = await self.gather(*(f.name for f in self.__schema__.key_fields))
        if len(out) == 1:
            return out[0]
        return out

    async def get_key_dict(self, key_property: str='name') -> dict:
        """Return the key values for this record."""
        out = OrderedDict()
        for field in sorted(self.__schema__.key_fields):
            out[getattr(field, key_property)] = await self.get(field.name)
        return out

    async def get_reference(self, key: str, default: 'Model'=None) -> 'Model':
        """Return the reference for the given key."""
        try:
            ref = self.__schema__.references[key]
        except KeyError:
            raise ReferenceNotFound(type(self), key)

        try:
            return self._references[key]
        except KeyError:
            pass

        field = self.__schema__[ref.source]
        ref_model = field.refers_to_model
        ref_field = field.refers_to_field
        value = await self.get(ref.source)
        if value is not None:
            reference = await ref_model.fetch({ref_field: value})
        else:
            reference = None
        self._references[key] = reference
        return reference

    async def get_value(self, key: str, default: Any=None) -> Any:
        """Return the record's value for a given field."""
        try:
            field = self.__schema__.fields[key]
        except KeyError:
            raise FieldNotFound(type(self), key)

        if field.gettermethod is not None:
            return await field.gettermethod(self)
        else:
            try:
                return self._changes[key]
            except KeyError:
                pass

            return self._state.get(key, default)

    @property
    def local_changes(self) -> Dict[str, Tuple[Any, Any]]:
        """Return a set of changes for this model.

        This method will gather all the local changes for the record,
        modifications that have been made to the original state,
        and return them as a key / value pair for the name of
        the field, and the (old, new) value.
        """
        return {
            key: (self._state.get(key), self._changes[key])
            for key in self._changes
        }

    @property
    def is_new(self) -> bool:
        """Return whether or not this record is new or not."""
        for field in self.__schema__.key_fields:
            if self._state.get(field.name) is not None:
                return False
        return True

    def mark_loaded(self):
        """Stash changes to the local state."""
        self._state.update(self._changes)
        self._changes.clear()

    async def reset(self):
        """Reset the local changes on this model."""
        self._changes.clear()

    async def save(self, **context):
        """Save this model to the store."""
        if type(self).__view__:
            raise ReadOnly(type(self).__name__)
        elif self._changes:
            context.setdefault('context', self.context)
            save_context = make_context(**context)
            values = await self.context.store.save_record(self, save_context)
            self._changes.update(values)
            self.mark_loaded()
            return True
        return False

    async def set(self, key: str, value: Any, ignore_method: bool=False):
        """Set the value for the given key."""
        target_key, _, field_key = key.rpartition('.')
        if target_key:
            target = await self.get(target_key)
            await target.set(field_key, value)
        else:
            schema = self.__schema__
            schema_object = schema[field_key]
            settermethod = schema_object.settermethod
            await schema_object.assert_valid(value)

            if settermethod and not ignore_method:
                await settermethod(self, value)
            elif isinstance(schema_object, Reference):
                self._references[field_key] = value
            elif isinstance(schema_object, Collector):
                self._collections[field_key] = value
            elif not is_equal(self._state.get(field_key), value):
                self._changes[field_key] = value
            else:
                self._changes.pop(field_key, None)

    async def update(self, values: dict):
        """Update a number of values by the given dictionary."""
        await asyncio.gather(*(self.set(*item) for item in values.items()))

    @classmethod
    async def create(cls, values: dict, **context) -> object:
        """Create a new record in the store with the given state."""
        if cls.__view__:
            raise ReadOnly(cls.__name__)
        else:
            record = cls(values=values, **context)
            await record.save()
            return record

    @classmethod
    async def ensure_exists(
        cls,
        values: dict,
        defaults: dict=None,
        **context,
    ) -> 'Model':
        """Find or create a model with the given values."""
        record = await cls.fetch(values, **context)
        if not record:
            data = {}
            data.update(defaults or {})
            data.update(values)
            record = cls(state=data)
            await record.save()
        return record

    @classmethod
    async def fetch(cls, key: Any, **context) -> 'Model':
        """Fetch a single record from the store for the given key."""
        context['where'] = cls.make_fetch_query(key) & context.get('where')
        context['limit'] = 1
        context.setdefault('store', cls.__store__)
        fetch_context = make_context(**context)
        records = await fetch_context.store.get_records(cls, fetch_context)
        data = dict(records[0]) if records else None
        if data and fetch_context.returning == ReturnType.Records:
            return cls(state=data)
        return data

    @classmethod
    def make_fetch_query(cls, key: Any) -> 'Query':
        """Create query for the key."""
        from .query import make_query_from_values

        if type(key) is dict:
            return make_query_from_values(key)
        elif type(key) not in (list, tuple):
            return cls.make_keyable_query(key)

        return cls.make_key_query(key)

    @classmethod
    def make_key_query(cls, values: Union[list, tuple]) -> 'Query':
        """Generate query for specific key of this model."""
        from .query import Query

        key_fields = cls.__schema__.key_fields
        if len(values) != len(key_fields):
            raise RuntimeError('Invalid key provided.')

        q = Query()
        for i, field in enumerate(key_fields):
            q &= Query(field.name) == values[i]
        return q

    @classmethod
    def make_keyable_query(cls, value: Any) -> 'Query':
        """Generate query for all keyable fields of this model."""
        from .query import Query

        key_fields = cls.__schema__.key_fields

        q = Query()
        if len(key_fields) == 1:
            q |= Query(key_fields[0].name) == value

        for field in cls.__schema__.fields.values():
            if field.test_flag(field.Flags.Keyable):
                q |= Query(field.name) == value
        return q

    @classmethod
    async def select(cls, **context) -> Collection:
        """Lookup a collection of records from the store."""
        context.setdefault('store', cls.__store__)
        return Collection(
            context=make_context(**context),
            model=cls,
        )

    @classmethod
    def find_model(cls, name):
        """Find subclass model by name."""
        sub_model = cls.registry.get(name)
        if sub_model and issubclass(sub_model, cls):
            return sub_model
        return None
