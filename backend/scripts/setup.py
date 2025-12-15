#!/usr/bin/env python3
"""
Setup script for DealBro.

Performs initial setup:
- Creates `.env` from `.env.example` (if missing)
- Installs Python dependencies
- Verifies MongoDB connectivity
- Seeds default sources (and ensures indexes exist)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def print_section(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def check_python_version() -> bool:
    print_section("Checking Python Version")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")

    if version < (3, 11):
        print("Error: Python 3.11 or higher is required")
        return False

    print("OK: Python version supported")
    return True


def create_env_file() -> bool:
    print_section("Setting up Environment")

    backend_dir = Path(__file__).parent.parent
    env_file = backend_dir / ".env"
    env_example = backend_dir / ".env.example"

    if env_file.exists():
        print("OK: .env already exists")
        return True

    if not env_example.exists():
        print("Error: .env.example not found")
        return False

    env_file.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")
    print("OK: Created .env from .env.example")
    print("Next: edit .env with your MongoDB connection string (if needed)")
    return True


def install_dependencies() -> bool:
    print_section("Installing Dependencies")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
        )
        print("OK: Dependencies installed")
        return True
    except subprocess.CalledProcessError as exc:
        print(f"Error: Failed to install dependencies: {exc}")
        return False


def check_mongodb() -> bool:
    print_section("Checking MongoDB")

    try:
        from pymongo import MongoClient

        from app.core.config import settings
        from app.core.database import init_default_sources_sync

        client = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")

        # Ensure indexes exist and seed sources.
        init_default_sources_sync()

        print(f"OK: Connected to MongoDB database '{settings.database_name}'")
        return True
    except Exception as exc:
        print(f"Error: MongoDB connection failed: {exc}")
        print("Check MONGODB_URL and DATABASE_NAME in .env and ensure MongoDB is running.")
        return False


def main() -> int:
    print()
    print("DealBro Setup")

    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)

    steps = [
        ("Python Version", check_python_version),
        ("Environment File", create_env_file),
        ("Dependencies", install_dependencies),
        ("MongoDB", check_mongodb),
    ]

    results: list[tuple[str, bool]] = []
    for step_name, step_func in steps:
        try:
            ok = step_func()
        except Exception as exc:
            print(f"Error in {step_name}: {exc}")
            ok = False
        results.append((step_name, ok))

    print_section("Setup Summary")
    for step_name, ok in results:
        print(f"{'OK' if ok else 'FAIL'} {step_name}")

    if all(ok for _, ok in results):
        print()
        print("OK: Setup completed successfully!")
        print()
        print("Next steps:")
        print("  1. Start the API server:")
        print("     python -m uvicorn app.main:app --reload")
        print("  2. Start the ingestion scheduler:")
        print("     python -m app.ingestion.scheduler")
        return 0

    print()
    print("Setup completed with errors. Fix the issues above and run again.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
