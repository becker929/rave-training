curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install -i /opt/render/project/src/aws-cli -b /opt/render/project/src/bin
python3 -m pip install --upgrade pip
python3 -m pip install flask gunicorn requests rocketry stripe boto3 pydantic==1.10.10
