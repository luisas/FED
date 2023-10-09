#!/usr/bin/env python
# coding: utf-8
print("Starting!")
import os
import pickle
import sys
print("Imported the modules")


# ------------------------------------------------------
# -----------------      Load files      ------------
# ------------------------------------------------------

split_list_file = sys.argv[1]
prefix = sys.argv[2]
chunk_size = sys.argv[3]


print("Start loading")
with open(split_list_file, 'rb') as file:
    split_list = pickle.load(file)
print("Loaded")


with open('log.txt', 'a') as f:
    f.write("loaded")

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]



chunks = list(chunks(split_list,int(chunk_size)))
print("chunked")
with open('log.txt', 'a') as f:
    f.write("chunked")

for chunk in range(0,len(chunks)):
    outname = prefix+"_"+str(chunk)+".pkl"
    print(chunk)
    with open('log.txt', 'a') as f:
        f.write(str(chunk))
    with open(outname, 'wb') as file:
        pickle.dump(chunks[chunk], file)
