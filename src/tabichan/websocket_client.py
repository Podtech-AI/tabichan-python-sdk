import os
import json
import asyncio
from typing import Optional, Dict, List, Any, Callable
import websockets
from websockets.exceptions import ConnectionClosed


class TabichanWebSocket:
    def __init__(self, user_id: str, api_key: Optional[str] = None):
        if not user_id:
            raise ValueError("user_id is required")

        if api_key is None:
            api_key = os.getenv("TABICHAN_API_KEY")

        if not api_key:
            raise ValueError(
                "API key is not set. Please set the TABICHAN_API_KEY environment variable or pass it as an argument."
            )

        self.user_id = user_id
        self.api_key = api_key
        self.ws = None
        self.is_connected = False
        self.current_question_id = None
        self.base_url = "wss://tabichan.podtech-ai.com/v1"
        self.connection_task = None

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}

    def on(self, event: str, handler: Callable):
        """Add event handler"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)

    def off(self, event: str, handler: Callable = None):
        """Remove event handler"""
        if event in self.event_handlers:
            if handler is None:
                self.event_handlers[event] = []
            else:
                self.event_handlers[event] = [
                    h for h in self.event_handlers[event] if h != handler
                ]

    def emit(self, event: str, *args, **kwargs):
        """Emit event to all handlers"""
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    print(f"Error in event handler for {event}: {e}")

    async def connect(self):
        """Connect to WebSocket"""
        if self.connection_task:
            return await self.connection_task

        self.connection_task = asyncio.create_task(self._connect())
        return await self.connection_task

    async def _connect(self):
        """Internal connection method"""
        ws_url = f"{self.base_url}/ws/chat/{self.user_id}?api_key={self.api_key}"

        try:
            # Connect with 10 second timeout
            self.ws = await asyncio.wait_for(websockets.connect(ws_url), timeout=10.0)

            self.is_connected = True
            self.emit("connected")

            # Start message handler
            asyncio.create_task(self._message_handler())

        except asyncio.TimeoutError:
            self.connection_task = None
            raise Exception("Connection timeout")
        except Exception as error:
            self.connection_task = None
            self.emit("error", error)
            raise error

    async def _message_handler(self):
        """Handle incoming messages"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    self.handle_message(data)
                except json.JSONDecodeError as e:
                    self.emit("error", Exception(f"Failed to parse message: {e}"))
        except ConnectionClosed as e:
            self.is_connected = False
            self.current_question_id = None
            self.connection_task = None

            if e.code == 1008:
                self.emit(
                    "auth_error", Exception("Authentication failed: Invalid API key")
                )
            else:
                self.emit("disconnected", {"code": e.code, "reason": e.reason or ""})
        except Exception as e:
            self.is_connected = False
            self.current_question_id = None
            self.connection_task = None
            self.emit("error", e)

    def handle_message(self, message: Dict[str, Any]):
        """Handle parsed message"""
        self.emit("message", message)

        message_type = message.get("type")

        if message_type == "question":
            self.current_question_id = message["data"]["question_id"]
            self.emit("question", message["data"])
        elif message_type == "result":
            self.emit("result", message["data"])
        elif message_type == "error":
            self.emit("chat_error", Exception(message["data"]))
        elif message_type == "complete":
            self.current_question_id = None
            self.emit("complete")
        else:
            self.emit("unknown_message", message)

    async def start_chat(
        self, query: str, history: List[Dict] = None, preferences: Dict = None
    ):
        """Start a chat session"""
        if not self.is_connected:
            raise Exception("WebSocket is not connected. Call connect() first.")

        message = {
            "type": "chat_request",
            "query": query,
            "history": history or [],
            "preferences": preferences or {},
        }

        await self.send_message(message)

    async def send_response(self, response: str):
        """Send response to active question"""
        if not self.is_connected:
            raise Exception("WebSocket is not connected")

        if not self.current_question_id:
            raise Exception("No active question to respond to")

        message = {
            "type": "response",
            "question_id": self.current_question_id,
            "response": response,
        }

        await self.send_message(message)
        self.current_question_id = None

    async def send_message(self, message: Dict[str, Any]):
        """Send message to WebSocket"""
        if not self.ws or (hasattr(self.ws, "closed") and self.ws.closed):
            raise Exception("WebSocket is not open")

        try:
            await self.ws.send(json.dumps(message))
        except Exception as e:
            raise Exception(f"Failed to send message: {e}")

    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.ws and not (hasattr(self.ws, "closed") and self.ws.closed):
            await self.ws.close(code=1000, reason="Client disconnecting")

        self.ws = None
        self.is_connected = False
        self.current_question_id = None
        self.connection_task = None

    def get_connection_state(self) -> str:
        """Get current connection state"""
        if not self.ws:
            return "disconnected"

        if hasattr(self.ws, "closed") and self.ws.closed:
            return "closed"
        elif self.is_connected:
            return "connected"
        else:
            return "connecting"

    def has_active_question(self) -> bool:
        """Check if there's an active question"""
        return self.current_question_id is not None

    def set_base_url(self, base_url: str):
        """Set base URL for WebSocket connection"""
        if self.is_connected:
            raise Exception("Cannot change base URL while connected")
        self.base_url = base_url
