import logging
import time
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send, Message
import json

PRIVATE_FIELDS = {"password", "token", "access_token", "refresh_token"}

def filter_private_data(data):
    if isinstance(data, dict):
        return {k: ("***" if k in PRIVATE_FIELDS else filter_private_data(v)) for k, v in data.items()}
    elif isinstance(data, list):
        return [filter_private_data(i) for i in data]
    return data

class LoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
        self.logger = logging.getLogger("uvicorn.access")

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        method = scope.get("method")
        path = scope.get("path")
        start_time = time.time()
        request_body = None
        # Читаем тело запроса только для POST/PUT/PATCH
        if method in ("POST", "PUT", "PATCH"):
            body_bytes = b""
            more_body = True
            # Считываем всё тело запроса
            while more_body:
                message = await receive()
                if message["type"] == "http.request":
                    body_bytes += message.get("body", b"")
                    more_body = message.get("more_body", False)
            if body_bytes:
                try:
                    request_body = json.loads(body_bytes.decode())
                    request_body = filter_private_data(request_body)
                except Exception:
                    request_body = "<non-json body>"
            # Подменяем receive, чтобы downstream мог снова прочитать body
            body_consumed = False
            async def replay_receive():
                nonlocal body_consumed
                if not body_consumed:
                    body_consumed = True
                    return {"type": "http.request", "body": body_bytes, "more_body": False}
                return {"type": "http.request", "body": b"", "more_body": False}
            receive = replay_receive
        response_status = None
        process_time = None
        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                status = message.get("status")
                if isinstance(status, int):
                    response_status = status
                elif isinstance(status, str) and status.isdigit():
                    response_status = int(status)
                else:
                    response_status = None
            await send(message)
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            process_time = (time.time() - start_time) * 1000
            self.logger.error("%s %s - ERROR: %s - %.2fms - body: %s", method, path, exc, process_time, request_body)
            raise
        process_time = (time.time() - start_time) * 1000
        # safe_status — только строка с числовым статусом или '-'
        if isinstance(response_status, int):
            safe_status = str(response_status)
        else:
            safe_status = "-"
        self.logger.info("%s %s - %s - %.2fms - body: %s", method, path, safe_status, process_time, request_body)
