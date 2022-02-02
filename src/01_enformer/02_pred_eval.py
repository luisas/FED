#!/usr/bin/env python
# coding: utf-8

print("Hello, I am starting!")
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


# ------------------------------------------------------
# -----------------      Load files      ------------
# ------------------------------------------------------
# import utils.py as module
file_path = os.path.dirname(os.path.realpath(__file__))
spec_utils = importlib.util.spec_from_file_location("utils", os.path.join(file_path ,"utils/utils_full.py"))
utils = importlib.util.module_from_spec(spec_utils)
spec_utils.loader.exec_module(utils)
from utils import *
from utils.utils import *

# Load files
model_path = 'https://tfhub.dev/deepmind/enformer/1'
datadir = "../../../../data/FED"
outputdir = os.path.join(datadir, "hd5")
fasta_file = os.path.join(datadir, "hg38.fa")
human_sequences = os.path.join(datadir, "data_human_sequences.bed")
pyfaidx.Faidx(fasta_file)

# Get pre-trained model
model = utils.Enformer(model_path)


spec_utils = importlib.util.spec_from_file_location("attention_module", os.path.join(file_path ,"utils/attention_module.py"))
attention_module = importlib.util.module_from_spec(spec_utils)
spec_utils.loader.exec_module(attention_module)
from attention_module import *
from utils.attention_module import *



spec_utils = importlib.util.spec_from_file_location("enformer", os.path.join(file_path ,"utils/enformer.py"))
enformer = importlib.util.module_from_spec(spec_utils)
spec_utils.loader.exec_module(enformer)
from enformer import *
from utils.enformer import *


# ------------------------------------------------------
# -----------------      Extract fasta      ------------
# ------------------------------------------------------
fasta_extractor = utils.FastaStringExtractor(fasta_file)


# Load previous validation dictionary
dataset_197k_file = os.path.join(outputdir,'test_197k_valid.h5')
with open(dataset_197k_file, 'rb') as config_dictionary_file:
    dataset_197k = pickle.load(config_dictionary_file)
dataset_197k_evaluation = copy.deepcopy(dataset_197k)


SEQUENCE_LENGHT = 393_216
## pad the sequence with Ns (anyways ignored by the model)
def pad_one_hot(sequence_one_hot, NEW_SIZE):
    ADD_ENDS = int((NEW_SIZE - sequence_one_hot.shape[0])/2)
    pad_zero = np.tile(np.array([0., 0., 0., 0.]), (ADD_ENDS, 1))
    padded_left = np.append(pad_zero,sequence_one_hot, axis=0)
    pad_sequence = np.append(padded_left,pad_zero, axis=0)
    return(pad_sequence)


max_steps = float("inf")

def evaluate_model_all_sequences_mod(model, dataset, head, dataset_197k_evaluation, max_steps=None):

    metric = MetricDict({'PearsonR': PearsonR(reduce_axis=(0,1))})

    # Given a tensor with a one-encoded sequence, predicts head tracks
    def predict(x):
        padded_sequence = pad_one_hot(np.squeeze(x.numpy(), axis=0), SEQUENCE_LENGHT)[np.newaxis]
        predictions = model.predict_on_batch(padded_sequence)[head]
        return tf.convert_to_tensor(predictions, dtype=tf.float32)

    for i in range(len(dataset_197k)):
        if max_steps is not None and i > max_steps:
            break

        batch = dataset_197k[i]
        prediction = predict(batch['sequence'])
        metric.update_state(batch['target'], prediction)
        # Compute it on a sequence basis
        metric_seq = MetricDict({'PearsonR': PearsonR(reduce_axis=(0,1))})
        metric_seq.update_state(batch['target'], prediction)
        dataset_197k_evaluation[i]["PearsonR"] = metric.result()["PearsonR"].numpy()
    return list([metric.result(), dataset_197k_evaluation])


metrics_human = evaluate_model_all_sequences_mod(model,
                               dataset=dataset_197k,
                               head='human',
                               dataset_197k_evaluation = dataset_197k_evaluation,
                               max_steps=float("inf"))

summarized_metrics = metrics_human[0]
dataset_197k_evaluation = metrics_human[1]

# ------------------------------------------------------
# -----------------     Save                ------------
# ------------------------------------------------------

file_summarized_metrics = os.path.join(outputdir,'summarized_metrics.h5')
with open(file_summarized_metrics, 'wb') as config_dictionary_file:
    pickle.dump(summarized_metrics, config_dictionary_file)

file_dataset_197k_evaluation = os.path.join(outputdir,'dataset_197k_evaluation.h5')
with open(file_dataset_197k_evaluation, 'wb') as config_dictionary_file:
    pickle.dump(dataset_197k_evaluation, config_dictionary_file)




# ------------------------------------------------------
# -------------     Prep evaluation df      ------------
# ------------------------------------------------------
file = os.path.join(outputdir,'suppl_df.h5')
with open(file, 'rb') as config_dictionary_file:
    suppl_df = pickle.load(config_dictionary_file)

ordered_assays = suppl_df[suppl_df["organism"] == "human"]["assay_type"]

def get_sequence_evaluation_df(i,dataset_197k_evaluation, ordered_assays ):
    # Create dataframe for plotting
    df = pd.DataFrame()
    # Add sequence
    df["sequence"] = np.repeat(1,len(ordered_assays))
    # Add assay
    df["assay"] = ordered_assays
    # Add pearson values
    df["pearson"] = (dataset_197k_evaluation[i]["PearsonR"])
    return(df)


final_df = pd.DataFrame()
for i in range(len(dataset_197k_evaluation)):
    df = get_sequence_evaluation_df(i,dataset_197k_evaluation, ordered_assays)
    print(i)
    final_df = pd.concat([final_df, df])


file_df = os.path.join(outputdir,'evaluation_df.h5')
with open(file_df, 'wb') as config_dictionary_file:
    pickle.dump(final_df, config_dictionary_file)
