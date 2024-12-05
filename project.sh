#!/bin/bash

# This script is used to setup a project after cloning it from git.
# It's similar to npm install, npm run, etc.

# Set some environment variables if they are not set
export VENV="${VENV:-.venv}"
export PYTHONPATH="${PYTHONPATH:-.}"

# Function to print environment variables if --verbose flag is set
print_env_vars() {
    if [ "$VERBOSE" = true ]; then
        echo "VENV=$VENV"
        echo "PYTHONPATH=$PYTHONPATH"
    fi
}

# Install dependencies function
# project.sh install - creates a virtual environment and installs dependencies
install() {
    # Create a virtual environment
    python3 -m venv $VENV

    # Activate the virtual environment
    source $VENV/bin/activate

    # Install dependencies
    pip install -r requirements.txt
}

# Test the project function
# project.sh test - runs the tests
test() {
    # Activate the virtual environment
    source $VENV/bin/activate

    # Run the tests
    pytest --disable-warnings tests/
}

# Run the project function
# project.sh run - runs the project
run() {
    # Activate the virtual environment
    source $VENV/bin/activate

    # Run the project
    uvicorn app.main:app --reload
}

## Help displays the help message
help() {
    echo "Usage: project.sh [install|test|run|help]"
    echo "install - creates a virtual environment and installs dependencies"
    echo "test - runs the tests"
    echo "run - runs the project"
}

# Check if the --verbose flag is set
VERBOSE=false
for arg in "$@"; do
    if [ "$arg" == "--verbose" ]; then
        VERBOSE=true
        print_env_vars
        # Remove --verbose from arguments
        set -- "${@/--verbose/}"
        shift
    fi
done

# Check if the user has provided an argument
if [ -z "$1" ]; then
    echo "Please provide an argument"
    exit 1
fi

# Check the argument provided by the user
if [ "$1" == "install" ]; then
    install
elif [ "$1" == "test" ]; then
    test
elif [ "$1" == "run" ]; then
    run
elif [ "$1" == "help" ]; then
    help
else
    echo "Invalid argument"
    exit 1
fi
