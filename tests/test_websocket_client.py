import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from tabichan.websocket_client import TabichanWebSocket


class TestTabichanWebSocket:
    def test_init_with_user_id_and_api_key(self):
        """Test initialization with user_id and api_key"""
        client = TabichanWebSocket("test_user", "test_api_key")
        assert client.user_id == "test_user"
        assert client.api_key == "test_api_key"
        assert client.base_url == "wss://tabichan.podtech-ai.com/v1"
        assert client.is_connected is False
        assert client.current_question_id is None

    def test_init_without_user_id_raises_error(self):
        """Test that missing user_id raises ValueError"""
        with pytest.raises(ValueError, match="user_id is required"):
            TabichanWebSocket("", "test_api_key")

    @patch.dict("os.environ", {"TABICHAN_API_KEY": "env_api_key"})
    def test_init_with_env_api_key(self):
        """Test initialization with API key from environment"""
        client = TabichanWebSocket("test_user")
        assert client.api_key == "env_api_key"

    def test_init_without_api_key_raises_error(self):
        """Test that missing API key raises ValueError"""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key is not set"):
                TabichanWebSocket("test_user")

    def test_event_handlers(self):
        """Test event handler registration and removal"""
        client = TabichanWebSocket("test_user", "test_api_key")

        handler1 = Mock()
        handler2 = Mock()

        # Add handlers
        client.on("test_event", handler1)
        client.on("test_event", handler2)

        # Emit event
        client.emit("test_event", "arg1", kwarg1="value1")

        # Check handlers were called
        handler1.assert_called_once_with("arg1", kwarg1="value1")
        handler2.assert_called_once_with("arg1", kwarg1="value1")

        # Remove specific handler
        client.off("test_event", handler1)
        handler1.reset_mock()
        handler2.reset_mock()

        client.emit("test_event", "arg2")
        handler1.assert_not_called()
        handler2.assert_called_once_with("arg2")

        # Remove all handlers
        client.off("test_event")
        handler2.reset_mock()

        client.emit("test_event", "arg3")
        handler2.assert_not_called()

    def test_handle_message_question(self):
        """Test handling question message"""
        client = TabichanWebSocket("test_user", "test_api_key")

        message_handler = Mock()
        question_handler = Mock()

        client.on("message", message_handler)
        client.on("question", question_handler)

        message = {
            "type": "question",
            "data": {"question_id": "q123", "text": "What is your name?"},
        }

        client.handle_message(message)

        message_handler.assert_called_once_with(message)
        question_handler.assert_called_once_with(message["data"])
        assert client.current_question_id == "q123"

    def test_handle_message_result(self):
        """Test handling result message"""
        client = TabichanWebSocket("test_user", "test_api_key")

        result_handler = Mock()
        client.on("result", result_handler)

        message = {"type": "result", "data": {"answer": "My name is Tabichan"}}

        client.handle_message(message)
        result_handler.assert_called_once_with(message["data"])

    def test_handle_message_complete(self):
        """Test handling complete message"""
        client = TabichanWebSocket("test_user", "test_api_key")
        client.current_question_id = "q123"

        complete_handler = Mock()
        client.on("complete", complete_handler)

        message = {"type": "complete"}

        client.handle_message(message)
        complete_handler.assert_called_once()
        assert client.current_question_id is None

    def test_handle_message_error(self):
        """Test handling error message"""
        client = TabichanWebSocket("test_user", "test_api_key")

        error_handler = Mock()
        client.on("chat_error", error_handler)

        message = {"type": "error", "data": "Something went wrong"}

        client.handle_message(message)
        error_handler.assert_called_once()
        # Check that an Exception was passed
        args = error_handler.call_args[0]
        assert isinstance(args[0], Exception)
        assert str(args[0]) == "Something went wrong"

    def test_handle_message_unknown(self):
        """Test handling unknown message type"""
        client = TabichanWebSocket("test_user", "test_api_key")

        unknown_handler = Mock()
        client.on("unknown_message", unknown_handler)

        message = {"type": "unknown_type", "data": "some data"}

        client.handle_message(message)
        unknown_handler.assert_called_once_with(message)

    def test_get_connection_state(self):
        """Test connection state reporting"""
        client = TabichanWebSocket("test_user", "test_api_key")

        # No WebSocket
        assert client.get_connection_state() == "disconnected"

        # Mock WebSocket
        client.ws = Mock()
        client.ws.closed = True
        assert client.get_connection_state() == "closed"

        client.ws.closed = False
        client.is_connected = True
        assert client.get_connection_state() == "connected"

        client.is_connected = False
        assert client.get_connection_state() == "connecting"

    def test_has_active_question(self):
        """Test active question detection"""
        client = TabichanWebSocket("test_user", "test_api_key")

        assert client.has_active_question() is False

        client.current_question_id = "q123"
        assert client.has_active_question() is True

        client.current_question_id = None
        assert client.has_active_question() is False

    def test_set_base_url(self):
        """Test setting base URL"""
        client = TabichanWebSocket("test_user", "test_api_key")

        # Should work when not connected
        client.set_base_url("wss://custom.example.com")
        assert client.base_url == "wss://custom.example.com"

        # Should raise error when connected
        client.is_connected = True
        with pytest.raises(Exception, match="Cannot change base URL while connected"):
            client.set_base_url("wss://another.example.com")

    @pytest.mark.asyncio
    async def test_start_chat_not_connected(self):
        """Test start_chat when not connected"""
        client = TabichanWebSocket("test_user", "test_api_key")

        with pytest.raises(Exception, match="WebSocket is not connected"):
            await client.start_chat("Hello")

    @pytest.mark.asyncio
    async def test_start_chat_connected(self):
        """Test start_chat when connected"""
        client = TabichanWebSocket("test_user", "test_api_key")
        client.is_connected = True
        client.send_message = AsyncMock()

        await client.start_chat(
            "Hello", [{"role": "user", "content": "Hi"}], {"lang": "en"}
        )

        expected_message = {
            "type": "chat_request",
            "query": "Hello",
            "history": [{"role": "user", "content": "Hi"}],
            "preferences": {"lang": "en"},
        }

        client.send_message.assert_called_once_with(expected_message)

    @pytest.mark.asyncio
    async def test_send_response_not_connected(self):
        """Test send_response when not connected"""
        client = TabichanWebSocket("test_user", "test_api_key")

        with pytest.raises(Exception, match="WebSocket is not connected"):
            await client.send_response("Yes")

    @pytest.mark.asyncio
    async def test_send_response_no_active_question(self):
        """Test send_response when no active question"""
        client = TabichanWebSocket("test_user", "test_api_key")
        client.is_connected = True

        with pytest.raises(Exception, match="No active question to respond to"):
            await client.send_response("Yes")

    @pytest.mark.asyncio
    async def test_send_response_with_active_question(self):
        """Test send_response with active question"""
        client = TabichanWebSocket("test_user", "test_api_key")
        client.is_connected = True
        client.current_question_id = "q123"
        client.send_message = AsyncMock()

        await client.send_response("Yes")

        expected_message = {
            "type": "response",
            "question_id": "q123",
            "response": "Yes",
        }

        client.send_message.assert_called_once_with(expected_message)
        assert client.current_question_id is None

    @pytest.mark.asyncio
    async def test_send_message_not_open(self):
        """Test send_message when WebSocket is not open"""
        client = TabichanWebSocket("test_user", "test_api_key")

        with pytest.raises(Exception, match="WebSocket is not open"):
            await client.send_message({"type": "test"})

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test successful send_message"""
        client = TabichanWebSocket("test_user", "test_api_key")
        client.ws = AsyncMock()
        client.ws.closed = False

        message = {"type": "test", "data": "hello"}
        await client.send_message(message)

        expected_json = json.dumps(message)
        client.ws.send.assert_called_once_with(expected_json)

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnect method"""
        client = TabichanWebSocket("test_user", "test_api_key")
        mock_ws = AsyncMock()
        mock_ws.closed = False
        client.ws = mock_ws
        client.is_connected = True
        client.current_question_id = "q123"
        client.connection_task = Mock()

        await client.disconnect()

        mock_ws.close.assert_called_once_with(code=1000, reason="Client disconnecting")
        assert client.ws is None
        assert client.is_connected is False
        assert client.current_question_id is None
        assert client.connection_task is None

    def test_emit_handler_exception(self):
        """Test emit handles exceptions in event handlers"""
        client = TabichanWebSocket("test_user", "test_api_key")

        def error_handler(*args, **kwargs):
            raise Exception("Handler error")

        def good_handler(*args, **kwargs):
            good_handler.called = True

        good_handler.called = False

        client.on("test_event", error_handler)
        client.on("test_event", good_handler)

        # Should not raise exception, but should continue to other handlers
        with patch("builtins.print") as mock_print:
            client.emit("test_event", "test_arg")
            mock_print.assert_called_once_with(
                "Error in event handler for test_event: Handler error"
            )

        # Good handler should still be called
        assert good_handler.called is True

    def test_off_nonexistent_event(self):
        """Test removing handler for non-existent event"""
        client = TabichanWebSocket("test_user", "test_api_key")

        # Should not raise error
        client.off("nonexistent_event")
        client.off("nonexistent_event", Mock())

    @pytest.mark.asyncio
    async def test_connect_already_connecting(self):
        """Test connect when already connecting"""
        client = TabichanWebSocket("test_user", "test_api_key")

        # Mock connection task that returns None
        async def mock_connection():
            return None

        mock_task = asyncio.create_task(mock_connection())
        client.connection_task = mock_task

        result = await client.connect()

        # Should return the existing task result
        assert result is None

    @pytest.mark.asyncio
    async def test_connect_timeout(self):
        """Test connection timeout"""
        client = TabichanWebSocket("test_user", "test_api_key")

        with patch("websockets.connect") as mock_connect:
            mock_connect.side_effect = asyncio.TimeoutError()

            with patch("asyncio.wait_for") as mock_wait_for:
                mock_wait_for.side_effect = asyncio.TimeoutError()

                with pytest.raises(Exception, match="Connection timeout"):
                    await client.connect()

                assert client.connection_task is None

    @pytest.mark.asyncio
    async def test_connect_general_error(self):
        """Test connection general error"""
        client = TabichanWebSocket("test_user", "test_api_key")

        error_handler = Mock()
        client.on("error", error_handler)

        test_error = Exception("Connection failed")

        with patch("websockets.connect") as mock_connect:
            mock_connect.side_effect = test_error

            with patch("asyncio.wait_for") as mock_wait_for:
                mock_wait_for.side_effect = test_error

                with pytest.raises(Exception, match="Connection failed"):
                    await client.connect()

                assert client.connection_task is None
                error_handler.assert_called_once_with(test_error)

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection"""
        client = TabichanWebSocket("test_user", "test_api_key")

        connected_handler = Mock()
        client.on("connected", connected_handler)

        mock_ws = AsyncMock()

        with patch("asyncio.wait_for", return_value=mock_ws):
            with patch.object(client, "_message_handler", new_callable=AsyncMock):
                await client.connect()

                assert client.ws == mock_ws
                assert client.is_connected is True
                connected_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_handler_general_exception(self):
        """Test message handler with general exception"""
        client = TabichanWebSocket("test_user", "test_api_key")
        client.is_connected = True
        client.current_question_id = "q123"
        client.connection_task = Mock()

        error_handler = Mock()
        client.on("error", error_handler)

        test_error = Exception("General error")

        # Mock WebSocket that raises general exception
        mock_ws = Mock()
        mock_ws.__aiter__ = Mock(side_effect=test_error)
        client.ws = mock_ws

        await client._message_handler()

        assert client.is_connected is False
        assert client.current_question_id is None
        assert client.connection_task is None

        error_handler.assert_called_once_with(test_error)

    @pytest.mark.asyncio
    async def test_send_message_ws_send_error(self):
        """Test send_message when WebSocket send fails"""
        client = TabichanWebSocket("test_user", "test_api_key")
        client.ws = AsyncMock()
        client.ws.closed = False
        client.ws.send.side_effect = Exception("Send failed")

        message = {"type": "test", "data": "hello"}

        with pytest.raises(Exception, match="Failed to send message: Send failed"):
            await client.send_message(message)

    @pytest.mark.asyncio
    async def test_disconnect_ws_already_closed(self):
        """Test disconnect when WebSocket is already closed"""
        client = TabichanWebSocket("test_user", "test_api_key")
        mock_ws = AsyncMock()
        mock_ws.closed = True
        client.ws = mock_ws
        client.is_connected = True
        client.current_question_id = "q123"
        client.connection_task = Mock()

        await client.disconnect()

        # Should not call close on already closed WebSocket
        mock_ws.close.assert_not_called()
        assert client.ws is None
        assert client.is_connected is False
        assert client.current_question_id is None
        assert client.connection_task is None

    @pytest.mark.asyncio
    async def test_disconnect_no_ws(self):
        """Test disconnect when no WebSocket exists"""
        client = TabichanWebSocket("test_user", "test_api_key")
        client.ws = None
        client.is_connected = True
        client.current_question_id = "q123"
        client.connection_task = Mock()

        await client.disconnect()

        assert client.ws is None
        assert client.is_connected is False
        assert client.current_question_id is None
        assert client.connection_task is None
