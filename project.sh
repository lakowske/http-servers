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

# Check if the virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Virtual environment is already activated."
fi

# Set the PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Set an alias for running the build script
alias now="python actions/build.py"

echo "Environment setup complete."