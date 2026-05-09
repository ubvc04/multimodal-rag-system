"""Streaming utilities for SSE responses."""

from __future__ import annotations

import json
from typing import Any


def sse_event(payload: dict[str, Any]) -> str:
	"""Serialize a payload to an SSE data event string."""
	data = json.dumps(payload, ensure_ascii=True)
	return f"data: {data}\n\n"
