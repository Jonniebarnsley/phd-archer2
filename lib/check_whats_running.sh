#!/bin/bash/

# iterates over an ensemble and gives an update on the
# progress of each run. It will report on whether they are:
#   a) completed
#   b) still running and, if so, how many years they have done so far
#   c) not completed but are also not running (possibly crashed)

# inputs:
#   - ensemble_dir: path to ensemble home directory

usage() { echo "Usage: $0 <ensemble_dir>" 1>&2; exit 1; }

if [ "$#" -ne 1 ]; then
    usage
fi 

running_jobs=$(squeue --noheader --format=%j --me)

ENSEMBLE=$1
PYTHON_ENV=$WORK/env # python envrionment using venv
MAX_TIME=30 # time at which a job should be considered complete

# Determine if input is a single run or ensemble directory
if [[ $(basename "$ENSEMBLE") == run* && -d "$ENSEMBLE/plot" ]]; then
    # Single run directory
    run_dirs=("$ENSEMBLE")
else
    # Ensemble directory
    run_dirs=($ENSEMBLE/run*)
fi

# iterate over ensemble members
for run in "${run_dirs[@]}"; do

    # Check if plot directory exists
    if [[ ! -d "$run/plot" ]]; then
        echo "$run: no plot directory found"
        continue
    fi
    
    # Check if there are any plot files
    if [[ ! "$(ls -A "$run/plot" 2>/dev/null)" ]]; then
        echo "$run: plot directory is empty"
        continue
    fi
    
    last_plotfile=$(ls "$run/plot" | tail -n 1)
    years_complete=$(python $WORK/lib/get_time.py "$run/plot/$last_plotfile")

    if [ $years_complete -ge $MAX_TIME ]; then
        echo "$run complete!"

    # Extract run number for job queue lookup
    run_number=$(basename "$run")
    elif grep -q "lasagne_$run_number" <<< "$running_jobs"; then
        echo "$run_number running... $years_complete years done so far"

    else
        echo "$run has not completed but is also not running"
    fi
done
