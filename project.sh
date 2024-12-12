#!/bin/bash

# This script is used to setup and run the project. You can source this script 
# to setup the bash environment for the project.

# Function to create a virtual environment
create_venv() {
    python3 -m venv .venv
}

# Check if .venv directory exists
if [ -d ".venv" ]; then
    echo "Activating existing virtual environment..."
else
    echo ".venv directory does not exist. Creating virtual environment..."
    create_venv
fi

# Source the activate script
source .venv/bin/activate

# Set the PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "Environment setup complete."