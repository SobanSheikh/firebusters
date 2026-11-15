import asyncio
import hashlib
import time
from collections import deque

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app import assistant_service
from app.core.config import settings

router = APIRouter()
global_recent: deque[float] = deque()
client_recent: dict[str, deque[float]] = {}
active = 0
rate_lock = asyncio.Lock()


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=1500)
    experiment_ids: list[str] = Field(default_factory=list, max_length=4)
    chart_id: str | None = Field(default=None, max_length=150)


def client_key(request: Request) -> str:
    """Use Render's forwarded client address without retaining raw addresses in memory."""
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    address = forwarded or (request.client.host if request.client else "unknown")
    return hashlib.blake2s(address[:200].encode(), digest_size=12).hexdigest()


def purge(queue: deque[float], now: float) -> None:
    while queue and queue[0] <= now - 60:
        queue.popleft()


@router.post("/ask")
async def ask(payload: Question, request: Request, response: Response):
    global active
    if len(payload.question.strip()) < 3 or any(len(item) > 100 for item in payload.experiment_ids):
        raise HTTPException(422, "Question or context is invalid")
    now = time.monotonic()
    key = client_key(request)
    async with rate_lock:
        purge(global_recent, now)
        queue = client_recent.setdefault(key, deque())
        purge(queue, now)
        if not queue and len(client_recent) > 2048:
            stale = [client for client, values in client_recent.items() if not values]
            for client in stale:
                client_recent.pop(client, None)
        if (
            len(global_recent) >= settings.assistant_global_requests_per_minute
            or len(queue) >= settings.assistant_client_requests_per_minute
            or active >= settings.assistant_max_concurrency
        ):
            raise HTTPException(
                429,
                "Assistant request limit reached. Inspect existing evidence or try again shortly.",
                headers={"Retry-After": "20"},
            )
        global_recent.append(now)
        queue.append(now)
        active += 1
        remaining = max(0, settings.assistant_client_requests_per_minute - len(queue))
    response.headers["X-RateLimit-Limit"] = str(settings.assistant_client_requests_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["Cache-Control"] = "no-store"
    try:
        return await assistant_service.answer(
            payload.question.strip(), payload.experiment_ids, payload.chart_id
        )
    except TimeoutError:
        raise HTTPException(
            504,
            "Research request timed out. Try a narrower question; charts and source records remain available.",
        ) from None
    except asyncio.CancelledError:
        raise
    except Exception:
        raise HTTPException(503, "Research evidence is temporarily unavailable.") from None
    finally:
        async with rate_lock:
            active -= 1
