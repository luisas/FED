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

dataset_197k_file = sys.argv[1]
model_path = sys.argv[2]
outname = sys.argv[3]
head = sys.argv[4]
eval = sys.argv[5]


from utils_full import *
# Get pre-trained model
model = Enformer(model_path)
print("1 -- Model loaded")

from enformer import *


with open(dataset_197k_file, 'rb') as file:
    dataset_197k = pickle.load(file)




SEQUENCE_LENGHT = 393_216
## pad the sequence with Ns (anyways ignored by the model)
def pad_one_hot(sequence_one_hot, NEW_SIZE):
    ADD_ENDS = int((NEW_SIZE - sequence_one_hot.shape[0])/2)
    pad_zero = np.tile(np.array([0., 0., 0., 0.]), (ADD_ENDS, 1))
    padded_left = np.append(pad_zero,sequence_one_hot, axis=0)
    pad_sequence = np.append(padded_left,pad_zero, axis=0)
    return(pad_sequence)


def evaluate_model_all_sequences_mod(model, dataset, head, dataset_197k_evaluation, max_steps=None):

    # Given a tensor with a one-encoded sequence, predicts head tracks
    def predict(x):
        padded_sequence = pad_one_hot(np.squeeze(x.numpy(), axis=0), SEQUENCE_LENGHT)[np.newaxis]
        predictions = model.predict_on_batch(padded_sequence)[head]
        return tf.convert_to_tensor(predictions, dtype=tf.float32)

    for i in range(len(dataset)):
        if max_steps is not None and i > max_steps:
            break

        batch = dataset[i]
        prediction = predict(batch['sequence'])
        with open('log.txt', 'a') as f:
            f.write(str(i))

        if(eval == "eval"):
            metric_seq = MetricDict({'PearsonR': PearsonR(reduce_axis=(0,1))})
            metric_seq.update_state(batch['target'][np.newaxis], prediction)
            pearson_seq = metric_seq.result()["PearsonR"].numpy()
            batch_validation = {"sequence": batch["sequence"],
                                        "target": batch["target"],
                                        "interval": batch["interval"],
                                        "prediction": prediction,
                                        "PearsonR": pearson_seq}
        else:
            batch_validation = {"sequence": batch["sequence"],
                                                "target": batch["target"],
                                                "prediction": prediction,
                                                "interval": batch["interval"]
                                                }



        dataset_197k_evaluation.append(batch_validation)

    return dataset_197k_evaluation

dataset_197k_evaluation = []
metrics_human = evaluate_model_all_sequences_mod(model,
                               dataset=dataset_197k,
                               head=head,
                               dataset_197k_evaluation = dataset_197k_evaluation)



dataset_197k_evaluation = metrics_human

print("Pred and evaluation done")
print(outname)
# Save
with open(outname, 'wb') as file:
    pickle.dump(dataset_197k_evaluation, file)
print("Saved")
