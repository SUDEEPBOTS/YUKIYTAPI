#!/bin/bash
echo "=========================================="
echo "    YUKIYTAPI Secure Installer (C-Core)   "
echo "=========================================="
echo "Installing required system packages (gcc, python3-dev)..."
sudo apt-get update
sudo apt-get install -y gcc python3-dev python3-setuptools python3-pip

echo "Setting up Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "Installing Python Dependencies..."
pip install setuptools
pip install -r requirements.txt

echo "Compiling C Source Code into Native Binaries (.so)..."
python3 setup.py build_ext --inplace

echo "Cleaning up C Source Files for Security..."
rm -f YUKIYTAPI/main.c
rm -f YUKIYTAPI/database/stats.c
rm -rf build/

echo "=========================================="
echo "Installation Complete! The API is securely compiled."
echo "You can now run the API using: bash start"
echo "=========================================="
