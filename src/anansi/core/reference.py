"""Define Reference class."""
from typing import Any, Callable, Type, Union


class Reference:
    """Define Reference class."""

    def __init__(
        self,
        *,
        gettermethod: Callable=None,
        model: Union[Type['Model'], str]=None,
        name: str=None,
        settermethod: Callable=None,
        source: Union[Type['Model'], str]=None,
    ):
        self._model = model
        self.gettermethod = gettermethod
        self.name = name
        self.settermethod = settermethod
        self.source = source

    async def assert_valid(self, value: Any):
        """Assert the given value can be assigned to this reference."""
        pass

    def getter(self, func: callable) -> callable:
        """Assign gettermethod via decorator."""
        self.gettermethod = func
        return func

    def get_model(self) -> Type['Model']:
        """Return model instance associated with this reference."""
        if type(self._model) is str:
            from .model import Model
            return Model.find_model(self._model)
        return self._model

    def setter(self, func: callable) -> callable:
        """Assign settermethod via decorator."""
        self.settermethod = func
        return func

    def set_model(self, model: Union[Type['Model'], str]):
        """Set model instance or name associated with this reference."""
        self._model = model

    model = property(get_model, set_model)
