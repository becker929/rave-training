#!/bin/bash

# This script will start an instance on lambdalabs.com,
# then list the instances, then stop the instance.

# List the available instance types
# URL="https://cloud.lambdalabs.com/api/v1/instance-types"
# curl -X GET $URL -H "Authorization: Bearer $API_KEY"

# Start an instance
URL="https://cloud.lambdalabs.com/api/v1/instance-operations/launch"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
response=$(curl -X POST $URL \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
            "region_name": "us-west-1",
            "instance_type_name": "gpu_1x_a10",
            "ssh_key_names": ["rave-key-1"],
            "name": "auto-node-'$TIMESTAMP'"
        }')
echo "Response: $response"
instance_id=$(echo $response | jq -r '.data.instance_ids[0]')
echo "Instance ID: $instance_id"

# Terminate the instance
URL="https://cloud.lambdalabs.com/api/v1/instance-operations/terminate"
curl -X POST $URL \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
            "instance_ids": [
                "'$instance_id'"
            ]
        }'
