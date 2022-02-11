#!/usr/bin/env python
# coding: utf-8
import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import itertools
import scipy.stats
import pickle
import sys

myDir = os.getcwd()
sys.path.append(myDir)

# ------------------------------------------------------
# -----------------      Load files      ------------
# ------------------------------------------------------

evaluation_dataset_file = sys.argv[1]
train_targets = sys.argv[2]
pred_targets = sys.argv[3]
outname = sys.argv[4]

prefix = os.path.basename(evaluation_dataset_file)

# Load file
with open(evaluation_dataset_file, 'rb') as file:
    pred = pickle.load(file)

train_tracks_ind = pd.read_csv(train_targets)
train_tracks_ind = list(train_tracks_ind["0"])
pred_tracks_ind = pd.read_csv(pred_targets)
pred_tracks_ind = list(pred_tracks_ind["0"])



# Swap axes so i can access to each track
def swap_dim(example):
    example_tmp= (example.numpy().squeeze())
    example_swapped = np.swapaxes(example_tmp, 0,1)
    return(example_swapped)

def get_tracks(example_section, track_ids):
    example_swapped = swap_dim(example_section)
    tracks = []
    for track in track_ids:
        tracks.append(list([track,example_swapped[track]]))
    return(tracks)

def eval_sequence(example):
    # Extract ground truth for each of the training tracks
    train_targets = get_tracks(example["target"], train_tracks_ind)
    prediction_values = get_tracks(example["prediction"], pred_tracks_ind)

    # Compare them
    targets = [];  preds = []; pearson = []
    for target in train_targets:
        for prediction in prediction_values:
            targets.append(target[0])
            preds.append(prediction[0])
            pearson.append(scipy.stats.pearsonr(target[1], prediction[1])[0])

    df = pd.DataFrame(list(zip(targets, preds, pearson)), columns = ["targets", "preds", "pearson"])
    return(df)


# Compute dataset
evaluation_df = pd.DataFrame()
for sequence, example in enumerate(pred):
    df = eval_sequence(example)
    df["sequence"] = prefix+"_"+str(sequence)
    evaluation_df = pd.concat([evaluation_df, df], ignore_index = True, axis = 0)

# Save
evaluation_df.to_csv(outname, index=False)
print("Saved")
