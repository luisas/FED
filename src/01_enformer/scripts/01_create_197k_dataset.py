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
import json
import functools
print("Imports done")

#   1 ------ IMPORTS ---------

tfrecord = sys.argv[1]
metadata = sys.argv[2]
fasta_file = sys.argv[3]
enformer_dict_file = sys.argv[4]
outname = sys.argv[5]
#spec_utils = importlib.util.spec_from_file_location("enformer", os.path.join(file_path ,"utils/utils.py"))
#utils = importlib.util.module_from_spec(spec_utils)
#spec_utils.loader.exec_module(utils)
#from utils.utils import *



with open(enformer_dict_file, 'rb') as config_dictionary_file:
    human_validation_dict = pickle.load(config_dictionary_file)

print("Number of sequences in dictionary")
print(len(human_validation_dict.keys()))


def one_hot_encode(sequence):
    return kipoiseq.transforms.functional.one_hot_dna(sequence).astype(np.float32)

def get_interval_from_sequence(sequence, human_validation_dict=human_validation_dict):
    for interval, ref_sequence in human_validation_dict.items():
        if np.allclose(sequence,ref_sequence):
            return(interval)

def deserialize(serialized_example, metadata):
    """Deserialize bytes stored in TFRecordFile."""
    feature_map = {
          'sequence': tf.io.FixedLenFeature([], tf.string),
          'target': tf.io.FixedLenFeature([], tf.string),
    }
    example = tf.io.parse_example(serialized_example, feature_map)
    sequence = tf.io.decode_raw(example['sequence'], tf.bool)
    sequence = tf.reshape(sequence, (metadata['seq_length'], 4))
    sequence = tf.cast(sequence, tf.float32)

    target = tf.io.decode_raw(example['target'], tf.float16)
    target = tf.reshape(target,
                          (metadata['target_length'], metadata['num_targets']))
    target = tf.cast(target, tf.float32)

    return {'sequence': sequence,
              'target': target}



class FastaStringExtractor:

    def __init__(self, fasta_file):
        self.fasta = pyfaidx.Fasta(fasta_file)
        self._chromosome_sizes = {k: len(v) for k, v in self.fasta.items()}

    def extract(self, interval: Interval, **kwargs) -> str:
        # Truncate interval if it extends beyond the chromosome lengths.
        chromosome_length = self._chromosome_sizes[interval.chrom]
        trimmed_interval = Interval(interval.chrom,
                                    max(interval.start, 0),
                                    min(interval.end, chromosome_length),
                                    )
        # pyfaidx wants a 1-based interval
        sequence = str(self.fasta.get_seq(trimmed_interval.chrom,
                                          trimmed_interval.start + 1,
                                          trimmed_interval.stop).seq).upper()
        # Fill truncated values with N's.
        pad_upstream = 'N' * max(-interval.start, 0)
        pad_downstream = 'N' * max(interval.end - chromosome_length, 0)
        return pad_upstream + sequence + pad_downstream

    def close(self):
        return self.fasta.close()


def get_metadata(metadata):
    with tf.io.gfile.GFile(metadata, 'r') as f:
        return json.load(f)

def get_dataset(tfr, metadata):

    metadata = get_metadata(metadata)

    dataset = tf.data.TFRecordDataset(tfrecord, compression_type='ZLIB')

    dataset = dataset.map(functools.partial(deserialize, metadata=metadata))

    return dataset



fasta_extractor = FastaStringExtractor(fasta_file)
# Create dataset with older sequences
human_dataset = get_dataset(tfrecord, metadata)
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

file = os.path.join(".",outname)
with open(file, 'wb') as config_dictionary_file:
    pickle.dump(dataset_197k, config_dictionary_file)
print("Saved")
