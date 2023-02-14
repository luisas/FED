#!/usr/bin/env python
# coding: utf-8
import gzip
import kipoiseq
from kipoiseq import Interval
import pyfaidx
import pandas as pd
import numpy as np
import os
from tqdm import tqdm
import pickle
import sys
import tensorflow as tf
import importlib
import copy

myDir = os.getcwd()
sys.path.append(myDir)

# ------------------------------------------------------
# -----------------      Load files      ------------
# ------------------------------------------------------

tfrecord = sys.argv[1]
metadata_path = sys.argv[2]
model_path = sys.argv[3]
outname = sys.argv[4]
head = sys.argv[5]
eval = sys.argv[6]


# Load model
from utils_full import *
model = Enformer(model_path)
print("1 -- Model loaded")

from enformer import *
print("2 -- Imports completed")


# Load the dataset
metadata = get_metadata_mod(metadata_path)
dataset = get_dataset_mod(tfrecord, metadata)

# Make predictions
prediction_obj = evaluate_model_all_sequences_mod(model,dataset=dataset,head=head, eval = "false")

# Save
with open(outname, 'wb') as file:
    pickle.dump(prediction_obj, file)
print("Saved")
