#!/bin/bash
# Script to build and publish InfraGPT to PyPI

# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Build distribution packages
echo "Building distribution packages..."
python -m pip install --upgrade build
python -m build

# Check the distribution packages
echo "Checking distribution packages..."
python -m pip install --upgrade twine
python -m twine check dist/*

# Upload to PyPI
echo "Uploading to PyPI..."
echo "Please make sure you have configured .pypirc or have your credentials ready."
echo "Do you want to upload to PyPI? (y/n)"
read upload_choice

if [ "$upload_choice" = "y" ]; then
    python -m twine upload dist/*
    echo "Package published to PyPI!"
else
    echo "Upload cancelled."
fi