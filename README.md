# rave-training
Utilities and experiments for training RAVE. 

Currently, A10 instances on Lambda Cloud (cloud.lambdalabs.com) are the target deployment environment.

# Setup

1. Start your A10 instance on Lambda Cloud, creating and downloading a PEM file key if you haven't already
1. Once running, launch the instance's Cloud IDE (JupyterLab)
1. Upload your audio data to `/home/ubuntu/training-data` (or set up your S3 bucket and access keys)
1. Create a new terminal in JupyterLab
1. Clone this repository: `git clone https://github.com/becker929/rave-training.git && cd rave-training`
1. Make script executable: `chmod +x ./setup-rave-lambdalabs.sh`
1. Run script `./setup-rave-lambdalabs.sh` (use your access keys and bucket name as parameters if using S3)
1. Open `rave-timing.ipynb`, choosing `rave_env` as the kernel
1. Set the MAX_STEPS & config to use
    - by default, will use `test`, and run a short training run (1500 steps, ~5 minutes)
    - For a full training run, use `v2` and set MAX_STEPS to between 3_000_000 and 6_000_000
1. Run all cells & confirm that RAVE is training
1. In a terminal, run `tensorboard --logdir runs --port 6080`
1. In your local terminal, run ssh -i ~/path/to/lambda-key.pem -N -f -L localhost:16080:localhost:6080 ubuntu@<your.instance.ip>
1. Now, you should be able to view the progress of the training via tensorboard by visiting `localhost:16080` in your browser



# RAVE changes in this repo
The `rave` subfolder contains a fork of `RAVE/rave`.

Local changes to `rave`:
- Apply Automatic Mixed Precision (amp) to forward pass
