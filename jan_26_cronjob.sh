#!/bin/bash
# jan_26_cronjob.sh

# Exit immediately if a command exits with a non-zero status
set -e

# Change to the directory containing the Pipfile (optional, but good practice)
cd "$(dirname "$0")"

echo "Starting script within the pipenv environment..."

# Run the python script using pipenv run
pipenv run python3 girlpoc_jan_26.py "$@"

echo "Script finished."
