#!/bin/bash
# Reads from .env and sets all keys as Fly.io secrets.

set -e

if [ ! -f .env ]; then
  echo "Error: .env file not found"
  exit 1
fi

flyctl secrets set $(grep -v '^#' .env | grep -v '^$' | xargs)
