#!/usr/bin/env python3
"""
WebSocket Test Script for Tabichan Python SDK

This script demonstrates how to use the TabichanWebSocket client to:
1. Connect to the WebSocket server
2. Start a chat session
3. Handle questions and responses
4. Manage the connection lifecycle

Requirements:
- Set TABICHAN_API_KEY environment variable
"""

import asyncio
import sys
from tabichan import TabichanWebSocket


class WebSocketTester:
    def __init__(self, user_id: str, api_key: str = None):
        self.user_id = user_id
        self.client = TabichanWebSocket(user_id, api_key)
        self.setup_event_handlers()

    def setup_event_handlers(self):
        """Set up event handlers for WebSocket events"""
        self.client.on("connected", self.on_connected)
        self.client.on("disconnected", self.on_disconnected)
        self.client.on("error", self.on_error)
        self.client.on("auth_error", self.on_auth_error)
        self.client.on("message", self.on_message)
        self.client.on("question", self.on_question)
        self.client.on("result", self.on_result)
        self.client.on("complete", self.on_complete)
        self.client.on("chat_error", self.on_chat_error)
        self.client.on("unknown_message", self.on_unknown_message)

    def on_connected(self):
        print("✅ Connected to WebSocket server")

    def on_disconnected(self, event):
        print(f"❌ Disconnected from server: {event}")

    def on_error(self, error):
        print(f"🚨 Error: {error}")

    def on_auth_error(self, error):
        print(f"🔒 Authentication error: {error}")

    def on_message(self, message):
        print(f"📨 Raw message: {message}")

    def on_question(self, data):
        print(f"❓ Question received: {data}")
        # Auto-respond to questions for demo purposes
        asyncio.create_task(self.auto_respond(data.get("question_id")))

    def on_result(self, data):
        print(f"📝 Result received: {data}")

    def on_complete(self):
        print("✅ Chat session completed")

    def on_chat_error(self, error):
        print(f"💬 Chat error: {error}")

    def on_unknown_message(self, message):
        print(f"❓ Unknown message type: {message}")

    async def auto_respond(self, question_id):
        """Auto-respond to questions for demo purposes"""
        if question_id:
            await asyncio.sleep(1)  # Brief delay
            try:
                await self.client.send_response("Yes, that sounds good!")
                print("✅ Auto-response sent")
            except Exception as e:
                print(f"❌ Failed to send response: {e}")

    async def run_test(self):
        """Run the complete WebSocket test"""
        try:
            print(f"🚀 Starting WebSocket test for user: {self.user_id}")
            print(f"🔗 Base URL: {self.client.base_url}")

            # Connect to WebSocket
            print("\n1. Connecting to WebSocket...")
            await self.client.connect()

            # Wait a moment for connection to stabilize
            await asyncio.sleep(1)

            # Start a chat session
            print("\n2. Starting chat session...")
            await self.client.start_chat(
                query="Plan a 2-day trip to Tokyo for this weekend",
                history=[],
                preferences={"language": "en", "currency": "USD"},
            )

            # Wait for chat to complete
            print("\n3. Waiting for chat completion...")
            await asyncio.sleep(10)  # Wait for responses

            # Check connection status
            print(f"\n4. Connection state: {self.client.get_connection_state()}")
            print(f"   Has active question: {self.client.has_active_question()}")

        except Exception as e:
            print(f"❌ Test failed: {e}")
        finally:
            print("\n6. Disconnecting...")
            await self.client.disconnect()
            print("🔌 Disconnected")


async def main():
    """Main function to run the WebSocket test"""

    print("🎯 Tabichan WebSocket Test Script")
    print("=" * 50)

    # Create and run the tester
    tester = WebSocketTester("user123")
    await tester.run_test()

    print("\n🏁 Test completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
