import json

from app.schemas import ContentPart, MessageContent


def serialize_message_text(text: str) -> str:
    return json.dumps({"parts": [{"type": "text", "text": text}]}, ensure_ascii=False)


def parse_message_content(content_json: str) -> MessageContent:
    data = json.loads(content_json)
    parts = [ContentPart(**part) for part in data.get("parts", [])]
    return MessageContent(parts=parts)


def message_text(content_json: str) -> str:
    try:
        content = parse_message_content(content_json)
    except (json.JSONDecodeError, ValueError, TypeError):
        return content_json

    texts = [part.text for part in content.parts if part.type == "text"]
    return "\n".join(texts)
