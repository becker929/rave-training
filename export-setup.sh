#!/bin/bash

# Check if the variable is provided
if [ -z "$1" ]; then
    echo "Provide the name of the run. This should be a directory within /home/ubuntu/runs/."
    exit 1
fi

run="$1"

sudo touch /etc/cron.hourly/export-rave && \
sudo chmod +x /etc/cron.hourly/export-rave && \
echo '/home/ubuntu/.pyenv/versions/3.10.11/bin/rave export \
--run=/home/ubuntu/runs/'"$run"'/ --streaming && \

timestamp=$(date +"%Y%m%d%H%M%S")
new_directory="/home/ubuntu/exports/${timestamp}"

if [ ! -d "${new_directory}" ]; then
    mkdir "${new_directory}"
fi

mv /home/ubuntu/runs/'"$run"'/*.ts "${new_directory}"' | sudo tee /etc/cron.hourly/export-rave

echo '------------------------------'
echo 'CREATED EXPORT JOB at /etc/cron.hourly/export-rave'
echo 'REMEMBER TO RUN THIS SETUP SCRIPT AGAIN IF CREATING A NEW RUN'
