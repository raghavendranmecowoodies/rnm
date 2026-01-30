#!/bin/bash
set -e

echo "=== Starting Build ==="

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing Playwright Chromium browser..."
python -m playwright install chromium

echo "=== Build Complete ==="