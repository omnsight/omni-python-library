#!/bin/bash
set -e
echo "Cleaning up project..."

# Remove virtual environment
if [ -d ".venv" ]; then
  echo "Removing .venv..."
  rm -rf .venv
fi

# Remove pytest cache
if [ -d ".pytest_cache" ]; then
  echo "Removing .pytest_cache..."
  rm -rf .pytest_cache
fi

# Remove coverage file
if [ -f ".coverage" ]; then
  echo "Removing .coverage..."
  rm -f .coverage
fi

# Remove pycache directories
echo "Removing __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} +

# Remove mypy cache
if [ -d ".mypy_cache" ]; then
  echo "Removing .mypy_cache..."
  rm -rf .mypy_cache
fi

# Remove ruff cache
if [ -d ".ruff_cache" ]; then
  echo "Removing .ruff_cache..."
  rm -rf .ruff_cache
fi

# Remove build artifacts
if [ -d "build" ]; then
  echo "Removing build directory..."
  rm -rf build
fi

if [ -d "dist" ]; then
  echo "Removing dist directory..."
  rm -rf dist
fi

echo "Removing .egg-info directories..."
find . -type d -name "*.egg-info" -exec rm -rf {} +

# remove uv cache
if [ -d ".uv_cache" ]; then
    echo "Removing .uv_cache"
    rm -rf .uv_cache
fi

echo "Cleanup complete!"
