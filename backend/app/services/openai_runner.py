import json
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


class StubOpenAIClient:
    def create_response(self, payload: dict) -> dict:
        user_text = payload.get("input", "")
        return {"output_text": f"MVP assistant response: {user_text}"}

    def upload_file(self, *, filename: str, content: bytes, content_type: str | None) -> str:
        return f"stub-{filename}"

    def delete_file(self, file_id: str) -> None:
        _ = file_id


class OpenAIRunner:
    def __init__(self, client: OpenAIClientProtocol | None = None, model_name: str | None = None):
        self.client = client or StubOpenAIClient()
        self.model_name = model_name or os.getenv("OPENAI_MODEL", "gpt-5.4")

    def chat(self, *, prompt: str, files: list[dict]) -> OpenAIResult:
        uploaded_ids: list[str] = []
        warnings: list[str] = []
        try:
            for file_obj in files:
                file_id = self.client.upload_file(
                    filename=file_obj["filename"],
                    content=file_obj["content"],
                    content_type=file_obj.get("content_type"),
                )
                uploaded_ids.append(file_id)

            payload = {
                "model": self.model_name,
                "store": False,
                "input": prompt,
                "metadata": {"file_ids": uploaded_ids},
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
