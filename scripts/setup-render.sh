python3 -m pip install --upgrade pip
python3 -m pip install flask gunicorn requests rocketry pydantic==1.10.10

# echo "SETTING UP SSH"
# # todo: upload pem file somehow
# # or create ssh key pair in code?
# chmod 600 ./rave-key-1.pem
# echo "StrictHostKeyChecking=accept-new" >> ~/.ssh/config
# echo "" >> ~/.ssh/config
# chmod 700 ~/.ssh && chmod 600 ~/.ssh/*
