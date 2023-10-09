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

evaluation_dataset_file = sys.argv[1]
targets_csv = sys.argv[2]
outname = sys.argv[3]

prefix = os.path.basename(evaluation_dataset_file)

with open(evaluation_dataset_file, 'rb') as file:
    evaluation_dataset = pickle.load(file)

targets = pd.read_csv(targets_csv, sep='\t')

ordered_assays = targets["target"]

def get_sequence_evaluation_df(i,evaluation_dataset, ordered_assays ):
    # Create dataframe for plotting
    df = pd.DataFrame()
    # Add sequence
    seq = prefix + "_" + str(i)
    df["sequence"] = np.repeat(seq,len(ordered_assays))
    # Add assay
    df["assay"] = ordered_assays
    # Add pearson values
    df["pearson"] = (evaluation_dataset[i]["PearsonR"])
    return(df)


# Compute dataset
final_df = pd.DataFrame()
for i in range(len(evaluation_dataset)):
    df = get_sequence_evaluation_df(i,evaluation_dataset, ordered_assays)
    final_df = pd.concat([final_df, df])

print(final_df)
# Save
final_df.to_csv(outname, sep = "\t", index=False)
print("Saved")
