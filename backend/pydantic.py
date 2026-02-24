from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class FieldInfo:
    default: Any = None
    default_factory: Callable[[], Any] | None = None


def Field(*, default: Any = None, default_factory: Callable[[], Any] | None = None) -> FieldInfo:
    return FieldInfo(default=default, default_factory=default_factory)


class BaseModel:
    def __init__(self, **data: Any) -> None:
        annotations = getattr(self.__class__, "__annotations__", {})
        for name in annotations:
            if name in data:
                value = data[name]
            else:
                default = getattr(self.__class__, name, None)
                if isinstance(default, FieldInfo):
                    if default.default_factory is not None:
                        value = default.default_factory()
                    else:
                        value = default.default
                else:
                    value = default
            setattr(self, name, value)

    def model_dump(self) -> dict[str, Any]:
        return dict(self.__dict__)
