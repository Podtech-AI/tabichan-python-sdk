# Tabichan Python SDK

[![Tests](https://github.com/Podtech-AI/tabichan-python-sdk/actions/workflows/test.yml/badge.svg)](https://github.com/Podtech-AI/tabichan-python-sdk/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/tabichan-python-sdk.svg)](https://badge.fury.io/py/tabichan-python-sdk)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

PodTech's Tabichan API SDK for Python - Your AI-powered tourism assistant.

## Features

- 🗾 Support for Japan and France tourism queries
- 🔄 Asynchronous chat processing with polling
- 🖼️ Image thumbnails for tourism content
- 🌍 Multi-language support
- 🔒 Secure API key authentication

## Installation

```bash
pip install tabichan-python-sdk
```

## Quick Start

### Environment Setup

Set your API key as an environment variable:

```bash
export TABICHAN_API_KEY="your-api-key-here"
```

### Basic Usage

```python
import os
from tabichan import TabichanClient

# Initialize client with API key from environment
api_key = os.getenv("TABICHAN_API_KEY")
client = TabichanClient(api_key)

# Start a chat about Japan tourism
task_id = client.start_chat(
    user_query="What are the best temples to visit in Kyoto?",
    user_id="user123",
    country="japan"
)

# Wait for the response
result = client.wait_for_chat(task_id, verbose=True)
print(result)
```

### Advanced Usage

```python
import os
from tabichan import TabichanClient

api_key = os.getenv("TABICHAN_API_KEY")
client = TabichanClient(api_key)

# Start a chat with history and additional inputs
task_id = client.start_chat(
    user_query="Tell me about romantic places in Paris",
    user_id="user456",
    country="france",
    history=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hello! How can I help you with your travel plans?"}
    ],
    additional_inputs={"budget": "mid-range", "duration": "3 days"}
)

# Poll for status manually
status_data = client.poll_chat(task_id)
print(f"Status: {status_data['status']}")

# Wait for completion
result = client.wait_for_chat(task_id)

# Get related image if available
image_id = result["itinerary"]["days"][0]["activities"][0]["activity"]["id"]
image_base64 = client.get_image(image_id, country="france")
print(f"Generated image: {len(image_base64)} characters")
```

## API Reference

### TabichanClient

#### `__init__(api_key: str)`

Initialize the client with your API key.

#### `start_chat(user_query: str, user_id: str, country: Literal["japan", "france"] = "japan", history: list[dict] = None, additional_inputs: dict = None) -> str`

Start a new chat session and return a task ID.

#### `poll_chat(task_id: str) -> dict`

Poll the status of a chat task.

#### `wait_for_chat(task_id: str, verbose: bool = False) -> dict`

Wait for a chat task to complete and return the result.

#### `get_image(id: str, country: Literal["japan", "france"] = "japan") -> str`

Get a base64-encoded image by ID.

## Development

### Setup

```bash
git clone https://github.com/Podtech-AI/tabichan-python-sdk.git
cd tabichan-python-sdk
uv sync --dev"
```

### Running Tests

```bash
uv run pytest
```

### Linting

```bash
uv run ruff format
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Run the test suite
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please contact us at [maxence@podtech.tech](mailto:maxence@podtech.tech) or open an issue on GitHub.

---

Made with ❤️ by [PodTech AI](https://podtech.tech)