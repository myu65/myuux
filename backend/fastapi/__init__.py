from dataclasses import dataclass
from typing import Any, Callable


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class UploadFile:
    def __init__(self, filename: str):
        self.filename = filename


@dataclass
class _Route:
    method: str
    path: str
    handler: Callable[..., Any]


class FastAPI:
    def __init__(self, title: str, version: str):
        self.title = title
        self.version = version
        self.routes: list[_Route] = []

    def add_middleware(self, _middleware: type, **_kwargs: Any) -> None:
        return None

    def on_event(self, _event: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator

    def get(self, path: str, **_kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(_Route(method="GET", path=path, handler=func))
            return func

        return decorator

    def post(self, path: str, **_kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(_Route(method="POST", path=path, handler=func))
            return func

        return decorator


class _Dependency:
    def __init__(self, dependency: Callable[..., Any]):
        self.dependency = dependency


def Depends(dependency: Callable[..., Any]) -> _Dependency:
    return _Dependency(dependency)


def File(_default: Any) -> Any:
    return _default
