# #!/bin/bash
# set -e

# echo "CLEANING UP"
# rm -rf /home/ec2-user/.pyenv
# cd /home/ec2-user

# echo "UPDATING"
# sudo yum upgrade -y
# sudo yum update -y

# echo "INSTALLING GIT & PYENV"
# sudo yum install git
# curl https://pyenv.run | bash

# echo "WRITING BASHRC"
# lines_to_add=(
# 'export PATH="$HOME/.pyenv/bin:$PATH"'
# 'eval "$(pyenv init -)"'
# )

# for line in "${lines_to_add[@]}"; do
#     grep -Fxq "$line" ~/.bashrc || echo "$line" >> ~/.bashrc
# done

# echo "INSTALLING PYTHON 3.10.11"
# sudo yum groupinstall "Development Tools" -y
# sudo yum install libffi-devel bzip2-devel wget -y
# sudo yum install ncurses-devel readline-devel sqlite-devel -y
# /home/ec2-user/.pyenv/bin/pyenv install 3.10.11

# echo "INSTALLING PIP PACKAGES"
# /home/ec2-user/.pyenv/versions/3.10.11/bin/python3.10 -m pip install --upgrade pip
# /home/ec2-user/.pyenv/versions/3.10.11/bin/python3.10 -m pip install black requests rocketry flask gunicorn
# /home/ec2-user/.pyenv/versions/3.10.11/bin/python3.10 -m pip uninstall pydantic
# /home/ec2-user/.pyenv/versions/3.10.11/bin/python3.10 -m pip install pydantic==1.10.10

# echo "SETTING UP SSH"
# # todo: upload pem file somehow
# # or create ssh key pair in code?
# chmod 600 ./rave-key-1.pem
# echo "StrictHostKeyChecking=accept-new" >> ~/.ssh/config
# echo "" >> ~/.ssh/config
# chmod 700 ~/.ssh && chmod 600 ~/.ssh/*
