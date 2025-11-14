#!/usr/bin/env python3
"""
Validate that the local Ollama instance is running and
can produce embeddings and chat completions.
"""

from __future__ import annotations

import argparse
import logging
import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ollama smoke test")
    parser.add_argument("--url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--chat-model", default="llama3.2:3b", help="Chat model to test")
    parser.add_argument("--embed-model", default="nomic-embed-text", help="Embedding model to test")
    parser.add_argument("--prompt", default="Hello from AI DevOps system!", help="Prompt for chat test")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_url = args.url.rstrip("/")

    logging.info("Testing embeddings API at %s", base_url)
    embed_resp = requests.post(
        f"{base_url}/api/embeddings",
        json={"model": args.embed_model, "prompt": "Test embedding"},
        timeout=60,
    )
    embed_resp.raise_for_status()
    logging.info("Embedding length: %s", len(embed_resp.json().get("embedding", [])))

    logging.info("Testing chat completion at %s", base_url)
    chat_resp = requests.post(
        f"{base_url}/api/generate",
        json={"model": args.chat_model, "prompt": args.prompt},
        timeout=60,
    )
    chat_resp.raise_for_status()
    output = chat_resp.json().get("response", "").strip()
    logging.info("Chat response: %s", output)


if __name__ == "__main__":
    main()
