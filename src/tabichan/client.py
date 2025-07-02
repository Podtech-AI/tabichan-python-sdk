import os
import sys
import time
from typing import Literal, Optional
import requests

from .__version__ import __version__


class TabichanClient:
    def __init__(self, api_key: Optional[str] = None):
        if api_key is None:
            api_key = os.getenv("TABICHAN_API_KEY")

        if api_key is None:
            raise ValueError(
                "API key is not set. Please set the TABICHAN_API_KEY environment variable or pass it as an argument to the TabichanClient constructor."
            )

        self.api_key = api_key
        self.base_url = "https://tourism-api.podtech-ai.com/v1"
        self.alternative_base_url = "https://tabichan.podtech-ai.com/v1"

        self.default_header = {
            "User-Agent": f"tabichan-python-sdk/{__version__}",
            "x-api-key": self.api_key,
        }

    def start_chat(
        self,
        user_query: str,
        user_id: str,
        country: Literal["japan", "france"] = "japan",
        history: list[dict] = None,
        additional_inputs: dict = None,
    ) -> str:
        body = {
            "user_query": user_query,
            "user_id": user_id,
            "country": country,
            "history": history or [],
            "additional_inputs": additional_inputs or {},
        }
        response_chat = requests.post(
            self.base_url + "/chat",
            headers=self.default_header,
            json=body,
            timeout=3,
        )
        response_chat.raise_for_status()
        return response_chat.json()["task_id"]

    def poll_chat(self, task_id: str) -> dict:
        response_poll = requests.get(
            self.base_url + f"/chat/poll?task_id={task_id}",
            headers=self.default_header,
            timeout=5,
        )
        response_poll.raise_for_status()
        return response_poll.json()

    def wait_for_chat(self, task_id: str, verbose: bool = False) -> dict:
        status = "running"
        max_attempts = 30  # Maximum 5 minutes (30 * 10 seconds)
        attempts = 0

        while status != "completed" and attempts < max_attempts:
            try:
                poll_data = self.poll_chat(task_id)
                status = poll_data["status"]

                if status == "completed":
                    if verbose:
                        print("✅ Generation complete!")

                    return poll_data["result"]

                elif status == "running":
                    if verbose:
                        print(
                            f"⏳ Generation still running... (attempt {attempts + 1}/{max_attempts})"
                        )

                elif status == "failed":
                    print(
                        f"❌ Generation failed: {poll_data.get('error', 'Unknown error')}"
                    )
                    sys.exit(1)
                else:
                    print(f"⚠️ Unexpected status: {status}")
                    sys.exit(1)

            except requests.exceptions.RequestException as e:
                print(f"❌ Failed to poll status: {e}")
                sys.exit(1)

            attempts += 1
            if attempts < max_attempts:
                time.sleep(10)

        if attempts >= max_attempts:
            print("❌ Timeout: Generation took too long")
            sys.exit(1)

    def get_image(self, id: str, country: Literal["japan", "france"] = "japan"):
        response_image = requests.get(
            self.base_url + f"/image?id={id}&country={country}",
            headers=self.default_header,
            timeout=30,
        )
        response_image.raise_for_status()
        return response_image.json()["base64"]
