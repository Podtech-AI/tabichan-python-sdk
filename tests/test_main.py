"""Tests for the main module."""

from tabichan.main import main


def test_main(capsys):
    """Test the main function."""
    main()
    captured = capsys.readouterr()
    assert "Hello from tabichan-python-sdk!" in captured.out
