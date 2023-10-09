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

dataset_file = sys.argv[1]
suppl_df_path = sys.argv[2]
outname = sys.argv[3]


with open(suppl_df_path, 'rb') as file:
    suppl_df = pickle.load(file)

def sub_labels(item):
    if(item == "DNase"):
        item = item.replace("DNase","DNase/ATAC")
    elif(item == "ATAC"):
        item = item.replace("ATAC","DNase/ATAC")
    return(item)

suppl_df["short_assay"] = list(map(sub_labels,suppl_df.assay_subtype ))



with open(dataset_file, 'rb') as file:
    dataset = pickle.load(file)


# Convert tracks to binary track (yes or no)
def to_binary_track(track_values, c):
    return(np.where(track_values > c,0, None))

def get_assay_only(values, assay, suppl_df):
    indeces = suppl_df[suppl_df.short_assay == assay].index
    return(values[:,list(indeces)])

def keep_position(row, threshold_intersection):
    prop_not_null = (row.tolist().count(0)/row.shape[0])*100
    if prop_not_null >= threshold_intersection:
        return True
    else:
        return False

# For one sequence
def get_intersection(batch, sequence, assays, threshold_peak, threshold_intersection, subset = "target"):
    columns = list(["sequence", "assay", "threshold_peak", "threshold_int", "value", "chr", "start", "end"])
    assays_intersections = pd.DataFrame(columns=columns)
    for assay in assays:
        targets = get_assay_only(batch[subset].numpy(), assay, suppl_df)
        targets_binary = to_binary_track(targets, threshold_peak)
        intersection_position = np.apply_along_axis(keep_position, 1, targets_binary, threshold_intersection)
        intersection_perc = (list(intersection_position).count(True)/len(intersection_position))*100
        # Extract interval info
        interval = batch["interval"]
        # Create dataset entry
        entry = pd.DataFrame(list([sequence, assay, threshold_peak, threshold_intersection, intersection_perc, interval.chrom, interval.start, interval.end])).T
        entry.columns = columns
        assays_intersections = assays_intersections.append(entry)
    return(assays_intersections)

threshold_peak = 0
assays = list(set(suppl_df.short_assay))
intersection_thresholds = range(0,101,5)

# For each sequence in the dataset
df_thresholds_benchmark = pd.DataFrame()
for i, batch in enumerate(dataset):
    sequence_id = dataset_file +"_"+ str(i)
    for threshold_intersection in intersection_thresholds:
        inte = get_intersection(batch, sequence_id, assays, threshold_peak, threshold_intersection)
        df_thresholds_benchmark  = df_thresholds_benchmark.append(inte)


df_thresholds_benchmark.to_csv(outname, sep = "\t", index=False)
print("Saved")
