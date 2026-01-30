#!/bin/bash
set -e

echo "=== Starting Build ==="

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "=== Build Complete (No browser installation needed - using BrowserBase) ==="