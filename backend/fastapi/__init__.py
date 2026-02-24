from typing import Any, Callable


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class UploadFile:
    def __init__(self, filename: str):
        self.filename = filename


class FastAPI:
    def __init__(self, title: str, version: str):
        self.title = title
        self.version = version

    def add_middleware(self, _middleware: type, **_kwargs: Any) -> None:
        return None

    def on_event(self, _event: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator

    def get(self, _path: str, **_kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator

    def post(self, _path: str, **_kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator


def Depends(dependency: Callable[..., Any]) -> Callable[..., Any]:
    return dependency


def File(_default: Any) -> Any:
    return _default
