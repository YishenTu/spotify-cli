#!/usr/bin/env python3
"""Entry point for `spotify serve` via launchd.

Designed to be invoked with the project's venv Python:
  .venv/bin/python serve.py --port 19743
"""
import os
import sys

# Ensure the project source is importable
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from spotify.server import run_server

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Spotify remote control server")
    p.add_argument("--port", type=int, default=19743)
    p.add_argument("--host", default="0.0.0.0")
    args = p.parse_args()
    run_server(host=args.host, port=args.port)
