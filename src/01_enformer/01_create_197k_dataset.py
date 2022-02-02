import tensorflow as tf
import gzip
import importlib
import kipoiseq
from kipoiseq import Interval
from kipoiseq import transforms
import pyfaidx
import os
import pandas as pd
import numpy as np
from tqdm import tqdm
import pickle
import sys
print("Imports done")

#   1 ------ IMPORTS ---------
file_path = os.path.dirname(os.path.realpath(__file__))
datadir = os.path.join(file_path,"../../../../data/FED")
outputdir = os.path.join(datadir, "hd5")
fasta_file = os.path.join(datadir, "hg38.fa")
pyfaidx.Faidx(fasta_file)

# import utils.py as module
spec_utils = importlib.util.spec_from_file_location("enformer", os.path.join(file_path ,"utils/utils.py"))
utils = importlib.util.module_from_spec(spec_utils)
spec_utils.loader.exec_module(utils)
from utils import *
from utils.utils import *


#   2 ------ PREPARE FILES ---------
#   extract fasta files
fasta_extractor = FastaStringExtractor(fasta_file)

# Load previous validation dictionary
enformer_dict_file = os.path.join(outputdir,'00_enformer_dict_seqs.h5')

with open(enformer_dict_file, 'rb') as config_dictionary_file:
    human_validation_dict = pickle.load(config_dictionary_file)

print("Number of sequences in dictionary")
print(len(human_validation_dict.keys()))


def get_interval_from_sequence(sequence, human_validation_dict=human_validation_dict):
    for interval, ref_sequence in human_validation_dict.items():
        if np.allclose(sequence,ref_sequence):
            return(interval)

# Create dataset with older sequences
human_dataset = get_dataset('human', 'valid', "/users/cn/lsantus/data/FED/basenji")
print("human dataset loaded")


## Create new dataset
dataset_197k = []
NEW_SEQUENCE_LENGTH = 196608
max_steps = float('inf')

print("iteration running")
print(max_steps)
# 1 from the sequence 131k get the sequence 197k
for i, batch in tqdm(enumerate(human_dataset)):

    print(i)

    # Find out which sequence it is
    interval_test = get_interval_from_sequence(batch["sequence"])
    if(interval_test is None):
        print("Skipping entry : ")
        print(i)
        continue

    # Create new sequence with interval lengh
    sequence_197k = one_hot_encode(fasta_extractor.extract(interval_test.resize(NEW_SEQUENCE_LENGTH)))

    # Recreate list of dictionaries
    # Dictionary keys: "sequence", "target", "interval"
    batch_197k = {}
    batch_197k["sequence"] = tf.constant(sequence_197k[np.newaxis])
    batch_197k["target"] = batch["target"]
    batch_197k["interval"] = interval_test

    # Add to list
    dataset_197k.append(batch_197k)
    if max_steps is not None and i > max_steps:
        break



# ------------------------------------------------------
# -----------------      Save     ----------------------
# ------------------------------------------------------

file = os.path.join(outputdir,'test_197k_valid.h5')
with open(file, 'wb') as config_dictionary_file:
    pickle.dump(dataset_197k, config_dictionary_file)
print("Saved")
