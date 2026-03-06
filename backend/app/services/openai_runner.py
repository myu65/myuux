import json
import mimetypes
import os
from dataclasses import dataclass, field
from typing import Protocol


class OpenAIClientProtocol(Protocol):
    def create_response(self, payload: dict) -> dict: ...

    def upload_file(self, *, filename: str, content: bytes, content_type: str | None) -> str: ...

    def delete_file(self, file_id: str) -> None: ...


@dataclass
class OpenAIResult:
    text: str
    warnings: list[str] = field(default_factory=list)


class OpenAIResponsesClient:
    def __init__(self, sdk_client=None):
        if sdk_client is not None:
            self._client = sdk_client
            return
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("openai package is required for OpenAIResponsesClient") from exc
        self._client = OpenAI()

    def create_response(self, payload: dict) -> dict:
        response = self._client.responses.create(**payload)
        return response.model_dump()

    def upload_file(self, *, filename: str, content: bytes, content_type: str | None) -> str:
        upload = self._client.files.create(file=(filename, content, content_type), purpose="assistants")
        return upload.id

    def delete_file(self, file_id: str) -> None:
        self._client.files.delete(file_id)


class StubOpenAIClient:
    def create_response(self, payload: dict) -> dict:
        user_text = payload.get("input", "")
        return {"output_text": f"MVP assistant response: {user_text}"}

    def upload_file(self, *, filename: str, content: bytes, content_type: str | None) -> str:
        _ = (content, content_type)
        return f"stub-{filename}"

    def delete_file(self, file_id: str) -> None:
        _ = file_id


def _is_text_like(content_type: str | None, filename: str) -> bool:
    if content_type:
        return content_type.startswith("text/") or content_type in {
            "application/json",
            "application/xml",
            "application/x-yaml",
        }
    guessed, _ = mimetypes.guess_type(filename)
    return bool(guessed and guessed.startswith("text/"))


def _decode_text(content: bytes) -> str | None:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return None


class OpenAIRunner:
    INLINE_TEXT_MAX_BYTES = 32_000

    def __init__(self, client: OpenAIClientProtocol | None = None, model_name: str | None = None):
        self.client = client or self._build_default_client()
        self.model_name = model_name or os.getenv("OPENAI_MODEL", "gpt-5.4")

    def _build_default_client(self) -> OpenAIClientProtocol:
        try:
            return OpenAIResponsesClient()
        except Exception:  # noqa: BLE001
            return StubOpenAIClient()

    def chat(self, *, prompt: str, files: list[dict]) -> OpenAIResult:
        uploaded_ids: list[str] = []
        warnings: list[str] = []
        input_parts: list[dict] = [{"type": "input_text", "text": prompt}]
        try:
            for file_obj in files:
                filename = file_obj["filename"]
                content = file_obj["content"]
                content_type = file_obj.get("content_type")
                if _is_text_like(content_type, filename) and len(content) <= self.INLINE_TEXT_MAX_BYTES:
                    decoded = _decode_text(content)
                    if decoded is not None:
                        input_parts.append(
                            {
                                "type": "input_text",
                                "text": f"\nIncluded file: {filename}\n{decoded}",
                            }
                        )
                        continue
                file_id = self.client.upload_file(filename=filename, content=content, content_type=content_type)
                uploaded_ids.append(file_id)
                input_parts.append({"type": "input_file", "file_id": file_id})

            payload = {
                "model": self.model_name,
                "store": False,
                "input": [{"role": "user", "content": input_parts}],
            }
            response = self.client.create_response(payload)
            text = response.get("output_text") or json.dumps(response, ensure_ascii=False)
            return OpenAIResult(text=text, warnings=warnings)
        finally:
            for file_id in uploaded_ids:
                try:
                    self.client.delete_file(file_id)
                except Exception as exc:  # noqa: BLE001
                    warnings.append(f"cleanup failed for {file_id}: {exc}")
