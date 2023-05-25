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
    - Refresh the page if `rave_env` is not in the list 
3. Set the MAX_STEPS & config to use
    - by default, will use `v2`, and run a short training run (1500 steps, ~5 minutes)
    - For a full training run, use `v2` and set MAX_STEPS to between 3_000_000 and 6_000_000
4. Run all cells & confirm that RAVE is training
    - If there is an error involving `NVML` then reboot the instance by running `sudo reboot` in terminal, wait a minute, then refresh the page and run again
6. In a terminal, run `tensorboard --logdir runs --port 6080`
7. In your local terminal, run ssh -i ~/path/to/lambda-key.pem -N -f -L localhost:16080:localhost:6080 ubuntu@<your.instance.ip>
8. Now, you should be able to view the progress of the training via tensorboard by visiting `localhost:16080` in your browser

Too complicated? Reach out to me and I may be able to help.

# RAVE changes in this repo
The `rave` subfolder contains a fork of `RAVE/rave`.

Local changes to `rave`:
- Apply Automatic Mixed Precision (amp) to forward pass

Todo:
- Test & Default to Wasserstein
- Compilation using torch.compile (in progress)
- Checking for simple best practices
- Experiment with Composer
- Experiment with increased batch size (24 vs 8)
- Experiment with reimplementation in JAX
