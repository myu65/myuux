from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class _FieldInfo:
    default: Any = None
    default_factory: Callable[[], Any] | None = None
    primary_key: bool = False


class _Metadata:
    def create_all(self, _engine: Any) -> None:
        return None

    def clear(self) -> None:
        return None


class Condition:
    def __init__(self, field_name: str, value: Any):
        self.field_name = field_name
        self.value = value


class Order:
    def __init__(self, field_name: str, descending: bool):
        self.field_name = field_name
        self.descending = descending


class QueryField:
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other: Any) -> Condition:  # type: ignore[override]
        return Condition(self.name, other)

    def desc(self) -> Order:
        return Order(self.name, descending=True)


class SQLModel:
    metadata = _Metadata()

    def __init_subclass__(cls, table: bool = False, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        cls.__field_defaults__ = {}
        for name in getattr(cls, "__annotations__", {}):
            value = getattr(cls, name, None)
            if isinstance(value, _FieldInfo):
                cls.__field_defaults__[name] = value
            else:
                cls.__field_defaults__[name] = _FieldInfo(default=value)
            setattr(cls, name, QueryField(name))

    def __init__(self, **data: Any):
        for name, info in self.__class__.__field_defaults__.items():
            if name in data:
                value = data[name]
            elif info.default_factory is not None:
                value = info.default_factory()
            else:
                value = info.default
            setattr(self, name, value)


class Engine:
    def __init__(self, url: str):
        self.url = url
        self.storage: dict[type[SQLModel], list[SQLModel]] = {}
        self.counters: dict[type[SQLModel], int] = {}


def create_engine(database_url: str, echo: bool = False) -> Engine:
    _ = echo
    return Engine(database_url)


class SelectQuery:
    def __init__(self, model: type[SQLModel]):
        self.model = model
        self.conditions: list[Condition] = []
        self.order: Order | None = None

    def where(self, condition: Condition) -> SelectQuery:
        self.conditions.append(condition)
        return self

    def order_by(self, order: Order) -> SelectQuery:
        self.order = order
        return self


class Result:
    def __init__(self, rows: list[SQLModel]):
        self._rows = rows

    def all(self) -> list[SQLModel]:
        return self._rows


class Session:
    def __init__(self, engine: Engine):
        self.engine = engine
        self._pending: list[SQLModel] = []

    def __enter__(self) -> Session:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)

    def add(self, obj: SQLModel) -> None:
        self._pending.append(obj)

    def commit(self) -> None:
        for obj in self._pending:
            model = type(obj)
            rows = self.engine.storage.setdefault(model, [])
            if getattr(obj, "id", None) is None:
                next_id = self.engine.counters.get(model, 0) + 1
                self.engine.counters[model] = next_id
                setattr(obj, "id", next_id)
            if obj not in rows:
                rows.append(obj)
        self._pending.clear()

    def refresh(self, _obj: SQLModel) -> None:
        return None

    def get(self, model: type[SQLModel], row_id: int) -> SQLModel | None:
        for row in self.engine.storage.get(model, []):
            if getattr(row, "id", None) == row_id:
                return row
        return None

    def exec(self, query: SelectQuery) -> Result:
        rows = list(self.engine.storage.get(query.model, []))
        for condition in query.conditions:
            rows = [row for row in rows if getattr(row, condition.field_name) == condition.value]
        if query.order is not None:
            rows.sort(key=lambda row: getattr(row, query.order.field_name), reverse=query.order.descending)
        return Result(rows)


def Field(
    *,
    default: Any = None,
    default_factory: Callable[[], Any] | None = None,
    primary_key: bool = False,
) -> _FieldInfo:
    return _FieldInfo(default=default, default_factory=default_factory, primary_key=primary_key)


def select(model: type[SQLModel]) -> SelectQuery:
    return SelectQuery(model)
