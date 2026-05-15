"""DRF renderers for SSE chat (``Accept: text/event-stream`` content negotiation)."""

from __future__ import annotations

import json

from rest_framework.renderers import BaseRenderer


class TextEventStreamRenderer(BaseRenderer):
    """Allows DRF to accept streaming clients without raising ``406 Not Acceptable``."""

    media_type = "text/event-stream"
    format = "sse"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""
        if isinstance(data, bytes | bytearray | memoryview):
            return bytes(data)
        if isinstance(data, str):
            return data.encode(self.charset)
        return json.dumps(data).encode(self.charset)
