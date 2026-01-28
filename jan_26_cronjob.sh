#!/bin/bash
# jan_26_cronjob.sh

# Exit immediately if a command exits with a non-zero status
set -e

# Change to the directory containing the Pipfile (optional, but good practice)
cd "$(dirname "$0")"

start_time_epoch=$(date +%s)
start_time_print=$(date -d @$start_time_epoch)
start_time_filepath=$(date -d @$start_time_epoch +"%Y-%m-%d_%H-%M-%S")
log_filepath=./logs/$start_time_filepath.log

echo "Starting script at $start_time_print" |& tee $log_filepath

# Run the python script using pipenv run
pipenv run python3 -u girlpoc_jan_26.py |& tee -a $log_filepath

end_time_epoch=$(date +%s)
end_time_print=$(date -d @$end_time_epoch)
echo "Script finished at $end_time_print after $(( $end_time_epoch - $start_time_epoch )) seconds" |& tee -a $log_filepath
