# rave-training
Utilities and experiments for training RAVE. 

Currently, A10 instances on Lambda Cloud (cloud.lambdalabs.com) are the target deployment environment.

# Setup

1. Start your A10 instance on Lambda Cloud, creating and downloading a PEM file key if you haven't already
1. Once running, launch the instance's Cloud IDE (JupyterLab)
1. Make sure your audio data is in a directory called `/home/ubuntu/training-data`. You can do this e.g. by using the JupyterLab upload feature.
1. Create a new terminal in JupyterLab
1. Clone this repository: `git clone https://github.com/becker929/rave-training.git && cd rave-training`
1. Make script executable: `chmod +x ./setup-rave-lambdalabs.sh`
1. Run script `./setup-rave-lambdalabs.sh`
1. To begin training, replace `<training-run-name>` and run the command: `nohup /home/ubuntu/.pyenv/versions/3.10.11/python3.10 ./rave-training.py --name="<training-run-name>" &`
2. Confirm that RAVE is training
3. In a terminal, run `tensorboard --logdir runs --port 6080`
4. In your local terminal, run ssh -i ~/path/to/lambda-key.pem -N -f -L localhost:16080:localhost:6080 ubuntu@<your.instance.ip>
5. Now, you should be able to view the progress of the training via tensorboard by visiting `localhost:16080` in your browser

Too complicated? Reach out to me and I may be able to help.

# RAVE changes in this repo
The `rave` subfolder contains a fork of `RAVE/rave`.

Local changes to `rave`:
- Apply Automatic Mixed Precision (amp) to forward pass
- Default V2 + Wasserstein config

Todo:
- Experiment with increased batch size (24 vs 8)
- Compilation using torch.compile (in progress)
- Checking for simple best practices
- Experiment with Composer
- Experiment with reimplementation in JAX / Haiku
