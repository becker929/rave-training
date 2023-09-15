#!/bin/bash

# RUN THIS BEFORE THE FIRST TIME YOU USE THE RAVE TRAINING NOTEBOOK
# This script is for setting up a Lambda Labs machine for RAVE training.

set -e

if ! nvidia-smi ; then
    echo "nvidias-smi failed, please reboot"
    exit 1
fi
# if nvidia-smi doesn't work, then run the following:
# sudo reboot

echo "CLEANING UP"
rm -rf /home/ubuntu/.pyenv
rm -rf /home/ubuntu/training-data
rm -rf /home/ubuntu/preprocessed
cd /home/ubuntu

echo "UPDATING"
sudo apt-get update && \
sudo apt-get upgrade -y

echo "INSTALLING PYENV"
curl https://pyenv.run | bash

echo "WRITING FILES"
lines_to_add=(
'export PATH="$HOME/.pyenv/bin:$PATH"'
'eval "$(pyenv init -)"'
)

for line in "${lines_to_add[@]}"; do
    grep -Fxq "$line" ~/.bashrc || echo "$line" >> ~/.bashrc
done

echo "INSTALLING PYTHON 3.10.11"
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils \
tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev && \
/home/ubuntu/.pyenv/bin/pyenv install 3.10.11

echo "INSTALLING PYTHON PACKAGES"
/home/ubuntu/.pyenv/versions/3.10.11/bin/python3.10 -m pip install --upgrade pip && \
/home/ubuntu/.pyenv/versions/3.10.11/bin/python3.10 -m pip install "einops>=0.5.0" \
    "gin-config" "GPUtil>=1.4.0" "librosa>=0.9.2" "numpy>=1.23.3" \
    "pytorch_lightning==1.9.0" "PyYAML>=6.0" "scikit_learn>=1.1.2" \
    "scipy==1.10.0" "tqdm>=4.64.1" "udls>=1.0.1" "cached-conv>=2.4.1" \
    "nn-tilde>=1.3.4" "tensorboard" "pytest>=7.2.2" && \
/home/ubuntu/.pyenv/versions/3.10.11/bin/python3.10 -m pip install acids-rave && \
/home/ubuntu/.pyenv/versions/3.10.11/bin/python3.10 -m pip install lit && \
/home/ubuntu/.pyenv/versions/3.10.11/bin/python3.10 -m pip install triton==2.0.0 && \
/home/ubuntu/.pyenv/versions/3.10.11/bin/python3.10 -m pip uninstall -y torch torchvision torchaudio && \
/home/ubuntu/.pyenv/versions/3.10.11/bin/python3.10 -m pip install torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu118 && \
/home/ubuntu/.pyenv/versions/3.10.11/bin/python3.10 -m pip install boto3

echo "CHECKING TORCH + TORCHVISION VERSION"
.pyenv/versions/3.10.11/bin/python3.10 -c "import torchvision;"
