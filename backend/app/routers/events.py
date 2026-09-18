from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
import asyncio
from ..core.event_bus import event_bus

router = APIRouter(prefix="/api/events", tags=["events"])

@router.get("/stream")
async def stream_events():
    """SSE 事件流 - 实时推送智能体动态"""

    async def event_generator():
        # 发送历史事件
        for event in event_bus.get_history(10):
            yield f"data: {json.dumps({'type': 'history', 'event': {'type': event.type, 'data': event.data, 'source': event.source, 'timestamp': event.timestamp}})}\n\n"
            await asyncio.sleep(0.1)

        # 监听新事件
        last_count = len(event_bus._event_history)
        while True:
            await asyncio.sleep(0.5)
            current_count = len(event_bus._event_history)
            if current_count > last_count:
                new_events = event_bus._event_history[last_count:]
                for event in new_events:
                    yield f"data: {json.dumps({'type': 'event', 'event': {'type': event.type, 'data': event.data, 'source': event.source, 'timestamp': event.timestamp}})}\n\n"
                last_count = current_count

    return StreamingResponse(event_generator(), media_type="text/event-stream")