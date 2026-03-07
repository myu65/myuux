import inspect
from dataclasses import asdict, is_dataclass
from types import GeneratorType
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel


class _Response:
    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class TestClient:
    __test__ = False
    def __init__(self, app):
        self.app = app

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        _ = (exc_type, exc, tb)
        return False

    def get(self, path: str) -> _Response:
        return self._request("GET", path, None)

    def post(self, path: str, json: dict | None = None) -> _Response:
        return self._request("POST", path, json)

    def _request(self, method: str, path: str, json_body: dict | None) -> _Response:
        try:
            route, path_params = self._find_route(method, path)
            result = self._invoke(route.handler, path_params, json_body)
            return _Response(status_code=200, payload=self._serialize(result))
        except HTTPException as exc:
            return _Response(status_code=exc.status_code, payload={"detail": exc.detail})

    def _find_route(self, method: str, path: str):
        path_parts = [part for part in path.strip("/").split("/") if part]
        for route in self.app.routes:
            if route.method != method:
                continue
            template_parts = [part for part in route.path.strip("/").split("/") if part]
            if len(path_parts) != len(template_parts):
                continue
            params: dict[str, str] = {}
            matched = True
            for actual, template in zip(path_parts, template_parts):
                if template.startswith("{") and template.endswith("}"):
                    params[template[1:-1]] = actual
                elif actual != template:
                    matched = False
                    break
            if matched:
                return route, params
        raise HTTPException(status_code=404, detail="not found")

    def _invoke(self, handler, path_params: dict[str, str], json_body: dict | None):
        signature = inspect.signature(handler)
        kwargs: dict[str, Any] = {}
        dependency_generators: list[GeneratorType] = []

        for name, parameter in signature.parameters.items():
            if name in path_params:
                kwargs[name] = path_params[name]
                continue

            annotation = parameter.annotation
            default = parameter.default

            if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
                kwargs[name] = annotation(**(json_body or {}))
                continue

            dependency = getattr(default, "dependency", None)
            if callable(dependency):
                value = dependency()
                if isinstance(value, GeneratorType):
                    generator = value
                    dependency_generators.append(generator)
                    kwargs[name] = next(generator)
                else:
                    kwargs[name] = value
                continue

            if parameter.default is inspect._empty:
                kwargs[name] = None

        try:
            return handler(**kwargs)
        finally:
            for generator in dependency_generators:
                try:
                    next(generator)
                except StopIteration:
                    pass

    def _serialize(self, result: Any) -> Any:
        if isinstance(result, BaseModel):
            if hasattr(result, "model_dump"):
                return self._serialize(result.model_dump())
            return self._serialize(result.dict())
        if isinstance(result, list):
            return [self._serialize(item) for item in result]
        if isinstance(result, dict):
            return {key: self._serialize(value) for key, value in result.items()}
        if is_dataclass(result):
            return asdict(result)
        if hasattr(result, "model_dump"):
            return result.model_dump()
        if hasattr(result, "dict"):
            return result.dict()
        if hasattr(result, "__dict__") and not isinstance(result, (str, bytes, dict)):
            return {
                key: self._serialize(value)
                for key, value in vars(result).items()
                if not key.startswith("_")
            }
        return result
