#!/bin/bash
set -e

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Installing Playwright browsers..."
playwright install chromium

echo "Installing system dependencies for Chromium..."
playwright install-deps chromium

echo "Build complete!"