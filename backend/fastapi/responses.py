class StreamingResponse:
    def __init__(self, content, media_type: str):
        self.content = content
        self.media_type = media_type
