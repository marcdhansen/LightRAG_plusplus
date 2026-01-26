#!/bin/bash
uv run python -m pytest -m heavy --run-integration "$@"
