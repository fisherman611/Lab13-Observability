from __future__ import annotations

import os
from typing import Any

try:
    from langfuse import observe, get_client

    def langfuse_context_update_trace(**kwargs: Any) -> None:
        try:
            client = get_client()
            client.update_current_trace(**kwargs)
        except Exception:
            pass

    def langfuse_context_update_observation(**kwargs: Any) -> None:
        try:
            client = get_client()
            client.update_current_observation(**kwargs)
        except Exception:
            pass

    class _LangfuseContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            langfuse_context_update_trace(**kwargs)

        def update_current_observation(self, **kwargs: Any) -> None:
            langfuse_context_update_observation(**kwargs)

    langfuse_context = _LangfuseContext()

    def get_langfuse_client():
        return get_client()

except Exception as e:  # pragma: no cover
    print(f"Langfuse import failed: {e}")

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_observation(self, **kwargs: Any) -> None:
            return None

    langfuse_context = _DummyContext()

    def get_langfuse_client():
        return None


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
