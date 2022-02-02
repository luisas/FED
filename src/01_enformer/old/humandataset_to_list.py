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

human_dataset = get_dataset('human', 'valid', "gs://basenji_barnyard/data").batch(1).repeat()

human_dataset_list = []
for i, batch in tqdm(enumerate(human_dataset)):
    human_dataset_list.append(batch)

file = os.path.join(outputdir,'human_dataset.h5')

# Step 2
with open(file, 'wb') as config_dictionary_file:
    pickle.dump(human_dataset_list, config_dictionary_file)
