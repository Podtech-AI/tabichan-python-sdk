import os
import pytest
import requests
import responses
from unittest.mock import patch
from tabichan.client import TabichanClient


class TestTabichanClient:
    def test_client_initialization_with_api_key(self):
        """Test client initialization with direct API key"""
        api_key = "test-api-key"
        client = TabichanClient(api_key)
        assert client.api_key == api_key
        assert client.base_url == "https://tourism-api.podtech-ai.com/v1"
        assert client.alternative_base_url == "https://tabichan.podtech-ai.com/v1"

    @patch.dict(os.environ, {"TABICHAN_API_KEY": "env-api-key"})
    def test_client_initialization_with_env_var(self):
        """Test client initialization using API key from environment variable"""
        api_key = os.getenv("TABICHAN_API_KEY")
        client = TabichanClient(api_key)
        assert client.api_key == "env-api-key"

    @patch.dict(os.environ, {}, clear=True)
    def test_client_initialization_missing_env_var(self):
        """Test client initialization when environment variable is not set"""
        api_key = os.getenv("TABICHAN_API_KEY")
        with pytest.raises(TypeError):
            TabichanClient(api_key)

    @responses.activate
    @patch.dict(os.environ, {"TABICHAN_API_KEY": "env-test-key"})
    def test_start_chat_with_env_api_key(self):
        """Test start_chat method using API key from environment"""
        responses.add(
            responses.POST,
            "https://tourism-api.podtech-ai.com/v1/chat",
            json={"task_id": "test-task-id"},
            status=200,
        )

        api_key = os.getenv("TABICHAN_API_KEY")
        client = TabichanClient(api_key)
        task_id = client.start_chat("Test query", "user123")

        assert task_id == "test-task-id"
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["x-api-key"] == "env-test-key"

    @responses.activate
    @patch.dict(os.environ, {"TABICHAN_API_KEY": "env-poll-key"})
    def test_poll_chat_with_env_api_key(self):
        """Test poll_chat method using API key from environment"""
        responses.add(
            responses.GET,
            "https://tourism-api.podtech-ai.com/v1/chat/poll?task_id=test-task",
            json={"status": "completed", "result": {"answer": "Test response"}},
            status=200,
        )

        api_key = os.getenv("TABICHAN_API_KEY")
        client = TabichanClient(api_key)
        result = client.poll_chat("test-task")

        assert result["status"] == "completed"
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["x-api-key"] == "env-poll-key"

    @responses.activate
    @patch.dict(os.environ, {"TABICHAN_API_KEY": "env-image-key"})
    def test_get_image_with_env_api_key(self):
        """Test get_image method using API key from environment"""
        responses.add(
            responses.GET,
            "https://tourism-api.podtech-ai.com/v1/image?id=test-id&country=japan",
            json={"base64": "test-base64-data"},
            status=200,
        )

        api_key = os.getenv("TABICHAN_API_KEY")
        client = TabichanClient(api_key)
        image_data = client.get_image("test-id")

        assert image_data == "test-base64-data"
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["x-api-key"] == "env-image-key"

    @responses.activate
    @patch.dict(os.environ, {"TABICHAN_API_KEY": "env-wait-key"})
    def test_wait_for_chat_with_env_api_key(self):
        """Test wait_for_chat method using API key from environment"""
        responses.add(
            responses.GET,
            "https://tourism-api.podtech-ai.com/v1/chat/poll?task_id=test-wait-task",
            json={"status": "completed", "result": {"answer": "Wait test response"}},
            status=200,
        )

        api_key = os.getenv("TABICHAN_API_KEY")
        client = TabichanClient(api_key)
        result = client.wait_for_chat("test-wait-task")

        assert result["answer"] == "Wait test response"
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["x-api-key"] == "env-wait-key"

    @patch.dict(os.environ, {"TABICHAN_API_KEY": "env-key"})
    def test_different_countries_with_env_key(self):
        """Test methods with different country parameters using env API key"""
        api_key = os.getenv("TABICHAN_API_KEY")
        client = TabichanClient(api_key)

        with responses.RequestsMock() as rsps:
            # Test japan country (default)
            rsps.add(
                responses.POST,
                "https://tourism-api.podtech-ai.com/v1/chat",
                json={"task_id": "japan-task"},
                status=200,
            )
            task_id_japan = client.start_chat("Japan query", "user1", country="japan")
            assert task_id_japan == "japan-task"

            # Test france country
            rsps.add(
                responses.POST,
                "https://tourism-api.podtech-ai.com/v1/chat",
                json={"task_id": "france-task"},
                status=200,
            )
            task_id_france = client.start_chat(
                "France query", "user2", country="france"
            )
            assert task_id_france == "france-task"

            # Test get_image with france
            rsps.add(
                responses.GET,
                "https://tourism-api.podtech-ai.com/v1/image?id=fr-image&country=france",
                json={"base64": "france-image-data"},
                status=200,
            )
            france_image = client.get_image("fr-image", country="france")
            assert france_image == "france-image-data"

    @responses.activate
    @patch.dict(os.environ, {"TABICHAN_API_KEY": "env-key"})
    def test_wait_for_chat_failed_status(self):
        """Test wait_for_chat method with failed status"""
        responses.add(
            responses.GET,
            "https://tourism-api.podtech-ai.com/v1/chat/poll?task_id=failed-task",
            json={"status": "failed", "error": "Test error message"},
            status=200,
        )

        api_key = os.getenv("TABICHAN_API_KEY")
        client = TabichanClient(api_key)

        with pytest.raises(SystemExit):
            client.wait_for_chat("failed-task")

    @responses.activate
    @patch.dict(os.environ, {"TABICHAN_API_KEY": "env-key"})
    def test_wait_for_chat_failed_status_no_error(self):
        """Test wait_for_chat method with failed status but no error message"""
        responses.add(
            responses.GET,
            "https://tourism-api.podtech-ai.com/v1/chat/poll?task_id=failed-task-no-error",
            json={"status": "failed"},
            status=200,
        )

        api_key = os.getenv("TABICHAN_API_KEY")
        client = TabichanClient(api_key)

        with pytest.raises(SystemExit):
            client.wait_for_chat("failed-task-no-error")

    @responses.activate
    @patch.dict(os.environ, {"TABICHAN_API_KEY": "env-key"})
    def test_wait_for_chat_unexpected_status(self):
        """Test wait_for_chat method with unexpected status"""
        responses.add(
            responses.GET,
            "https://tourism-api.podtech-ai.com/v1/chat/poll?task_id=unexpected-task",
            json={"status": "unknown_status"},
            status=200,
        )

        api_key = os.getenv("TABICHAN_API_KEY")
        client = TabichanClient(api_key)

        with pytest.raises(SystemExit):
            client.wait_for_chat("unexpected-task")

    @responses.activate
    @patch.dict(os.environ, {"TABICHAN_API_KEY": "env-key"})
    def test_wait_for_chat_request_exception(self):
        """Test wait_for_chat method with request exception"""
        responses.add(
            responses.GET,
            "https://tourism-api.podtech-ai.com/v1/chat/poll?task_id=exception-task",
            body=requests.exceptions.ConnectionError("Connection failed"),
        )

        api_key = os.getenv("TABICHAN_API_KEY")
        client = TabichanClient(api_key)

        with pytest.raises(SystemExit):
            client.wait_for_chat("exception-task")

    @responses.activate
    @patch.dict(os.environ, {"TABICHAN_API_KEY": "env-key"})
    @patch("time.sleep")
    def test_wait_for_chat_timeout(self, mock_sleep):
        """Test wait_for_chat method timeout scenario"""
        responses.add(
            responses.GET,
            "https://tourism-api.podtech-ai.com/v1/chat/poll?task_id=timeout-task",
            json={"status": "running"},
            status=200,
        )

        api_key = os.getenv("TABICHAN_API_KEY")
        client = TabichanClient(api_key)

        with pytest.raises(SystemExit):
            client.wait_for_chat("timeout-task")

        # Should have made 30 attempts (max_attempts)
        assert len(responses.calls) == 30
        # Should have slept 29 times (attempts - 1)
        assert mock_sleep.call_count == 29

    @responses.activate
    @patch.dict(os.environ, {"TABICHAN_API_KEY": "env-key"})
    @patch("time.sleep")
    def test_wait_for_chat_running_then_completed(self, mock_sleep):
        """Test wait_for_chat method with running status then completed"""
        # First call returns running
        responses.add(
            responses.GET,
            "https://tourism-api.podtech-ai.com/v1/chat/poll?task_id=running-task",
            json={"status": "running"},
            status=200,
        )
        # Second call returns completed
        responses.add(
            responses.GET,
            "https://tourism-api.podtech-ai.com/v1/chat/poll?task_id=running-task",
            json={"status": "completed", "result": {"answer": "Final answer"}},
            status=200,
        )

        api_key = os.getenv("TABICHAN_API_KEY")
        client = TabichanClient(api_key)

        result = client.wait_for_chat("running-task")

        assert result["answer"] == "Final answer"
        assert len(responses.calls) == 2
        assert mock_sleep.call_count == 1

    @responses.activate
    @patch.dict(os.environ, {"TABICHAN_API_KEY": "env-key"})
    def test_wait_for_chat_verbose_mode(self):
        """Test wait_for_chat method with verbose output"""
        responses.add(
            responses.GET,
            "https://tourism-api.podtech-ai.com/v1/chat/poll?task_id=verbose-task",
            json={"status": "completed", "result": {"answer": "Verbose answer"}},
            status=200,
        )

        api_key = os.getenv("TABICHAN_API_KEY")
        client = TabichanClient(api_key)

        result = client.wait_for_chat("verbose-task", verbose=True)

        assert result["answer"] == "Verbose answer"
        assert len(responses.calls) == 1

    @responses.activate
    @patch.dict(os.environ, {"TABICHAN_API_KEY": "env-key"})
    @patch("time.sleep")
    def test_wait_for_chat_verbose_running(self, mock_sleep):
        """Test wait_for_chat method with verbose running status"""
        # First call returns running
        responses.add(
            responses.GET,
            "https://tourism-api.podtech-ai.com/v1/chat/poll?task_id=verbose-running-task",
            json={"status": "running"},
            status=200,
        )
        # Second call returns completed
        responses.add(
            responses.GET,
            "https://tourism-api.podtech-ai.com/v1/chat/poll?task_id=verbose-running-task",
            json={
                "status": "completed",
                "result": {"answer": "Verbose running answer"},
            },
            status=200,
        )

        api_key = os.getenv("TABICHAN_API_KEY")
        client = TabichanClient(api_key)

        result = client.wait_for_chat("verbose-running-task", verbose=True)

        assert result["answer"] == "Verbose running answer"
        assert len(responses.calls) == 2
        assert mock_sleep.call_count == 1
