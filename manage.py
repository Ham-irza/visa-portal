#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Load environment variables from .env file
from pathlib import Path
from dotenv import load_dotenv

# Find the .env file in the backend directory
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "activated in your virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
