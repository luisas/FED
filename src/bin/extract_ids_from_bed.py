#!/usr/bin/env python3

import pandas as pd
import sys

list_ids = sys.argv[1]
bed_annot = sys.argv[2]
out_file = sys.argv[3]


id_df = pd.read_csv(list_ids, sep = "\t", header = None)
ids = list(id_df[0])

annot = pd.read_csv(bed_annot, sep = "\t", header = None)
annot = annot[annot[7] == "gene" ]

annot[4] = annot[9].str.split(";", expand = True)[0].str.split("\s", expand = True)[1].str.replace("\"", "").str.split(".", expand= True)[0]
filtered_annot = annot[annot[4].isin(ids)]
filtered_annot.to_csv(out_file, sep = "\t", header = False, index = False)   


