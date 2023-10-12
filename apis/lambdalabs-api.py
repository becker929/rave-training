import os
import requests
import subprocess
import sys
import time
from datetime import datetime
from subprocess import Popen, PIPE

HOME_DIR = os.environ.get("HOME_DIR")
if HOME_DIR == None:
    raise Exception("HOME_DIR environment variable not set")

# get API key from ./lambda-rave-api-key
with open(os.path.join(HOME_DIR, "lambda-rave-api-key.txt"), "r") as f:
    API_KEY = f.read().strip()

BASE_URL = "https://cloud.lambdalabs.com/api/v1/"
LIST_TYPES_URL = BASE_URL + "instance-types"
LAUNCH_URL = BASE_URL + "instance-operations/launch"
DETAILS_URL = BASE_URL + "instances/"
LIST_URL = BASE_URL + "instances"
TERMINATE_URL = BASE_URL + "instance-operations/terminate"
PEM_FILE = "/home/ec2-user/rave-key-1.pem"
GH_BASE_URL = "https://raw.githubusercontent.com/becker929/rave-training/main"
SETUP_SCRIPT = f"setup-lambda-worker.sh"
WORKER_BASE_DIR = "/home/ubuntu/rave-training"
S3_SCRIPT = f"setup-lambda-s3.sh"
DATA_SCRIPT = "download-data.py"
TRAINING_SCRIPT = f"rave-training.py"
PYTHON_APP = "/home/ubuntu/.pyenv/versions/3.10.11/bin/python3.10"
PREPROCESS = "/home/ubuntu/.pyenv/versions/3.10.11/bin/rave preprocess"
DATA_DIR = "/home/ubuntu/training-data"
OUTPUT_DIR = "/home/ubuntu/preprocessed"
NUM_TRAINING_STEPS = 1000


def list_instance_types():
    response = requests.get(LIST_TYPES_URL, auth=(API_KEY, ""))
    data = response.json().get("data")
    instance_types = []
    for instance_type_name, instance_type_data in data.items():
        price_cents_per_hour = instance_type_data["instance_type"][
            "price_cents_per_hour"
        ]
        # filter by availability
        if len(instance_type_data["regions_with_capacity_available"]) > 0:
            instance_types.append((instance_type_name, price_cents_per_hour))
    # sort by price, lowest first
    instance_types = sorted(instance_types, key=lambda x: x[1])
    return instance_types


def launch_instance(instance_type):
    body = {
        "region_name": "us-east-1",
        "instance_type_name": instance_type,
        "ssh_key_names": ["rave-key-1"],
        "file_system_names": [],
        "quantity": 1,
    }
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.post(LAUNCH_URL, json=body, headers=headers, auth=(API_KEY, ""))
    code = response.status_code
    return response.json(), code


def list_instance_ids():
    response = requests.get(LIST_URL, auth=(API_KEY, ""))
    data = response.json().get("data")
    instance_ids = []
    for instance_data in data:
        instance_ids.append(instance_data["id"])
    return instance_ids


def get_instance_details(instance_id):
    url = DETAILS_URL + instance_id
    response = requests.get(url, auth=(API_KEY, ""))
    code = response.status_code
    return response.json(), code


def wait_for_instance(instance_id):
    for i in range(100):
        data, status_code = get_instance_details(instance_id)
        status = data.get("data").get("status")
        print(f"Status: {status}")
        ip_address = data.get("data").get("ip")
        if status == "active":
            break
        time.sleep(5)
    return ip_address


def terminate_instance(instance_id):
    body = {
        "instance_ids": [instance_id],
    }
    headers = {
        "Content-Type": "application/json",
    }
    response = requests.post(
        TERMINATE_URL, json=body, headers=headers, auth=(API_KEY, "")
    )
    code = response.status_code
    return response.json(), code


def run_ssh_cmd(ip_address, cmd):
    user = "ubuntu"
    process = subprocess.run(
        f"ssh {user}@{ip_address} -i {PEM_FILE} {cmd}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process


def run_ssh_cmd2(ip_address, cmd):
    cmd = f"ssh ubuntu@{ip_address} -i {PEM_FILE} {cmd}"
    print("Running command:", cmd)
    with Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True) as p:
        while p.poll() is None:
            out = p.stdout.readline().decode("utf-8")
            print("o: ", out, flush=True)
            err = p.stderr.readline().decode("utf-8")
            print("e: ", err, flush=True)


def download_resources(ip_address):
    cmds = [
        f"mkdir {WORKER_BASE_DIR}",
        f"wget {GH_BASE_URL}/scripts/{SETUP_SCRIPT} -O {WORKER_BASE_DIR}/{SETUP_SCRIPT}",
        f"wget {GH_BASE_URL}/scripts/{S3_SCRIPT} -O {WORKER_BASE_DIR}/{S3_SCRIPT}",
        f"wget {GH_BASE_URL}/{DATA_SCRIPT} -O {WORKER_BASE_DIR}/{DATA_SCRIPT}",
        f"wget {GH_BASE_URL}/{TRAINING_SCRIPT} -O {WORKER_BASE_DIR}/{TRAINING_SCRIPT}",
        f"git clone https://github.com/acids-ircam/RAVE.git {WORKER_BASE_DIR}/RAVE",
    ]
    for cmd in cmds:
        result = run_ssh_cmd(ip_address, cmd)
        print("result: ", result)


def run_setup_script(ip_address):
    result = run_ssh_cmd(ip_address, f"chmod +x {WORKER_BASE_DIR}/{SETUP_SCRIPT}")
    print("result: ", result)
    run_ssh_cmd2(ip_address, f"{WORKER_BASE_DIR}/{SETUP_SCRIPT}")


def setup_s3(ip_address, access_key, secret_key):
    result = run_ssh_cmd(ip_address, f"chmod +x {WORKER_BASE_DIR}/{S3_SCRIPT}")
    print("result: ", result)
    result = run_ssh_cmd(
        ip_address, f"{WORKER_BASE_DIR}/{S3_SCRIPT} {access_key} {secret_key}"
    )
    print("result: ", result)


def download_data(ip_address, bucket_name, object_name):
    download_cmd = (
        f'{PYTHON_APP} {WORKER_BASE_DIR}/{DATA_SCRIPT} {bucket_name} "{object_name}"'
    )
    run_ssh_cmd2(ip_address, download_cmd)


def preprocess_data(ip_address):
    cmd = f"{PREPROCESS} --input_path {DATA_DIR} --output_path {OUTPUT_DIR}"
    run_ssh_cmd(ip_address, cmd)


def train_rave(ip_address):
    name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    cmd = f"{PYTHON_APP} {WORKER_BASE_DIR}/{TRAINING_SCRIPT} -s {NUM_TRAINING_STEPS} -n {name}"
    run_ssh_cmd2(ip_address, cmd)


if __name__ == "__main__":
    access_key = sys.argv[1]
    secret_key = sys.argv[2]
    bucket_name = sys.argv[3]
    object_name = sys.argv[4]

    # create an instance, get its ID, get its id address,
    # run some commands, and terminate it
    instance_types = list_instance_types()
    instance_type = instance_types[0][0]
    print(f"Launching instance of type {instance_type}")
    data, status_code = launch_instance(instance_type)
    if status_code != 200:
        print("Error launching instance")
        exit(1)
    instance_id = data.get("data").get("instance_ids")[0]
    print(f"Instance ID: {instance_id}")

    # wait for instance to be ready
    # when ready, data.get("data").get("status") == "active"
    ip_address = wait_for_instance(instance_id)
    print(f"IP Address: {ip_address}")
    if ip_address is None:
        print("Error getting IP Address")
        exit(1)

    # setup worker
    print("Downloading resources")
    download_resources(ip_address)
    print("Running setup script")
    run_setup_script(ip_address)
    print("Setting up S3")
    setup_s3(ip_address, access_key, secret_key)
    print("Downloading data")
    download_data(ip_address, bucket_name, object_name)
    print("Preprocessing data")
    preprocess_data(ip_address)
    print("Training RAVE")
    train_rave(ip_address)

    # # terminate all instances
    # instance_ids = list_instance_ids()
    # print(f"Terminating instances {instance_ids}")
    # for instance_id in instance_ids:
    #     data, status_code = terminate_instance(instance_id)
    #     print(data)
    #     if status_code != 200:
    #         print("Error terminating instance")
    #         exit(1)
