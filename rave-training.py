import hashlib
import os
import sys

import gin
import pytorch_lightning as pl
import torch
from torch.utils.data import DataLoader

import rave
import rave.core
import rave.dataset

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--name', help='Name of the training run.', required=True)

args = parser.parse_args()

NAME = args.name
CONFIG = ["v2", "wasserstein"]
DB_PATH = "/home/ubuntu/preprocessed/"
MAX_STEPS = 3_000_000
VAL_EVERY = 10_000
N_SIGNAL = 131072
BATCH = 8
ckpt = None
OVERRIDE = []
WORKERS = 8
GPU = None
DERIVATIVE = False
NORMALIZE = False
PROGRESS = True

def add_gin_extension(config_name: str) -> str:
    if config_name[-4:] != '.gin':
        config_name += '.gin'
    return config_name

def setup():
    torch.backends.cudnn.benchmark = True
    gin.parse_config_files_and_bindings(
        map(add_gin_extension, CONFIG),
        OVERRIDE,
    )
    model = rave.RAVE()
    if DERIVATIVE:
        model.integrator = rave.dataset.get_derivator_integrator(model.sr)[1]

    dataset = rave.dataset.get_dataset(
        DB_PATH, model.sr, N_SIGNAL, derivative=DERIVATIVE, normalize=NORMALIZE
    )
    train, val = rave.dataset.split_dataset(dataset, 98)
    num_workers = WORKERS

    train = DataLoader(
        train, BATCH, True, drop_last=True, num_workers=num_workers
    )
    val = DataLoader(val, BATCH, False, num_workers=num_workers)

    # CHECKPOINT CALLBACKS
    validation_checkpoint = pl.callbacks.ModelCheckpoint(
        monitor="validation", filename="best")
    last_checkpoint = pl.callbacks.ModelCheckpoint(filename="last")
    val_check = {}
    if len(train) >= VAL_EVERY:
        val_check["val_check_interval"] = VAL_EVERY
    else:
        nepoch = VAL_EVERY // len(train)
        val_check["check_val_every_n_epoch"] = nepoch
    gin_hash = hashlib.md5(
        gin.operative_config_str().encode()).hexdigest()[:10]
    RUN_NAME = f'{NAME}_{gin_hash}'
    os.makedirs(os.path.join("runs", RUN_NAME), exist_ok=True)

    GPU = [0]

    accelerator = None
    devices = None
    if GPU == [-1]:
        pass
    elif torch.cuda.is_available():
        accelerator = "cuda"
        devices = GPU or rave.core.setup_gpu()
    
    trainer = pl.Trainer(
        logger=pl.loggers.TensorBoardLogger(
            "runs",
            name=RUN_NAME,
        ),
        accelerator=accelerator,
        devices=devices,
        callbacks=[
            validation_checkpoint,
            last_checkpoint,
            rave.model.WarmupCallback(),
            rave.model.QuantizeCallback(),
            rave.core.LoggerCallback(rave.core.ProgressLogger(RUN_NAME)),
        ],
        max_epochs=100000,
        max_steps=MAX_STEPS,
        profiler="simple",
        enable_progress_bar=PROGRESS,
        **val_check,
    )
    run = rave.core.search_for_run(ckpt)
    if run is not None:
        step = torch.load(run, map_location='cpu')["global_step"]
        trainer.fit_loop.epoch_loop._batches_that_stepped = step

    with open(os.path.join("runs", RUN_NAME, "config.gin"), "w") as config_out:
        config_out.write(gin.operative_config_str())

    return trainer, model, train, val, run

trainer, model, train, val, run = setup()
trainer.fit(model, train, val, ckpt_path=run)