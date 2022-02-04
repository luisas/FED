import gzip
from collections import Mapping
import importlib
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


datadir = "../../../../data/FED"
outputdir = os.path.join(datadir, "hd5")
fasta_file = os.path.join(datadir, "hg38.fa")
pyfaidx.Faidx(fasta_file)


# import utils.py as module
spec_utils = importlib.util.spec_from_file_location("enformer", os.path.join(os.getcwd() ,"utils.py"))
utils = importlib.util.module_from_spec(spec_utils)
spec_utils.loader.exec_module(utils)
from utils import *

# extract fasta file
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
human_dataset = get_dataset('human', 'valid', "gs://basenji_barnyard/data").batch(1).repeat()

print("human dataset loaded")
## Create new dataset
dataset_197k = []
notfound = []
NEW_SEQUENCE_LENGTH = 196608
max_steps = float('inf')


for i, batch in tqdm(enumerate(human_dataset)):
    batch_197k = {}
    print(i)
    # 1 from the sequence 131k get the sequence 197k
    interval_test = get_interval_from_sequence(batch["sequence"])
    if interval_test is None:
        notfound.append(batch)
        continue
    sequence_197k = one_hot_encode(fasta_extractor.extract(interval_test.resize(NEW_SEQUENCE_LENGTH)))
    batch_197k["sequence"] = tf.constant(sequence_197k[np.newaxis])

    # add same real targets
    batch_197k["target"] = batch["target"]
    dataset_197k.append(batch_197k)
    if max_steps is not None and i > max_steps:
        break

print(dataset_197k[0]["sequence"])
file = os.path.join(outputdir,'new_dataset_197k_valid.h5')
file_notfound = os.path.join(outputdir,'notfound.h5')

print("Done")


# Save
with open(file, 'wb') as config_dictionary_file:
    pickle.dump(dataset_197k, config_dictionary_file)

with open(file_notfound, 'wb') as config_dictionary_file:
    pickle.dump(notfound, config_dictionary_file)

print("Saved")
