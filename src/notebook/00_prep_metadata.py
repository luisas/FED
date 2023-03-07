#!/usr/bin/env python
# coding: utf-8

# # Parse json 

# In[1]:


import requests, json
import pandas as pd
from pandas import json_normalize
from functools import reduce


# In[2]:


# https://www.encodeproject.org/matrix/?type=Experiment
metadata_file = "/home/luisasantus/Desktop/crg_cluster/data/FED/metadata/experiment_report_2023_3_3_15h_56m.tsv"
outfile = "/home/luisasantus/Desktop/crg_cluster/data/FED/metadata/atac_metadata.tsv"


# In[3]:


# Load Metadata 
metadata = pd.read_csv(metadata_file, sep = "\t", skiprows=1)
# Filter values
assay_title = "ATAC-seq"
organism = "Homo sapiens"
biosample_classification = "tissue"
perturbation = False

file_formats = ["bed", "bigWig", "bigBed"]
output_types = ["fold change over control", "IDR thresholded peaks"]

# Extract columns of interest 
prefix_link = "https://www.encodeproject.org"
file_columns = ["accession", "file_format","file_type","file_format_type","output_type", "assay_title","assembly", "href" ]
experiment_columns = ["Accession", "Biosample term name", "Biosample accession", "Organism", "Biosample ontology", "Perturbed", "Biological replicate", "Technical replicate"]


# Filter metadata
metadata_filtered = metadata[metadata['Assay title'] == assay_title]
metadata_filtered = metadata_filtered[metadata_filtered['Organism'] == organism]
metadata_filtered = metadata_filtered[metadata_filtered["Biosample ontology"].str.contains(biosample_classification)]
metadata_filtered = metadata_filtered[metadata_filtered["Perturbed"] == perturbation]
metadata_filtered = metadata_filtered.reset_index().drop("index", axis = 1)


# In[4]:


# Extract file ids for each experiment 
def get_file_ids(row): 
    def get_file_name(name):
        return name.split("/")[2]

    # For each line 
    files = list(row["Files"].split(","))
    file_ids = list(map(get_file_name, files))
    return(file_ids)

def get_biosample(biosample_id):
    # Force return from the server in JSON format
    headers = {'accept': 'application/json'}
    # This URL locates the ENCODE biosample with accession number ENCBS000AAA
    url = 'https://www.encodeproject.org/biosample/'+biosample_id+'/?frame=object'
    # GET the object
    response = requests.get(url, headers=headers)
    # Extract the JSON response as a Python dictionary
    biosample = response.json()
    # Print the Python object
    biosample = json_normalize(json.loads(json.dumps(biosample)))
    return(biosample)

def get_files_df(row):
    # Get files 
    file_ids = get_file_ids(row)
    biosamples = pd.DataFrame()
    for bio_id in file_ids: 
        biosamples = pd.concat([biosamples,get_biosample(bio_id)]) 
    filtered_files = biosamples[biosamples.file_format.isin(file_formats)]
    return(filtered_files)

def filter_files(row, prefix_link, file_columns):
    # Filter files 
    files = get_files_df(row)
    files_filtered = files[file_columns]
    files_filtered["link"] = prefix_link+files_filtered.href
    files_filtered = files_filtered.drop("href", axis = 1)
    files_filtered = files_filtered.rename(columns = {"accession": "File accession"})
    return(files_filtered)

def extract_summary(row): 
    files = filter_files(row, prefix_link, file_columns)
    experiment = pd.DataFrame(row[experiment_columns]).T
    files['tmp'] = 1
    experiment['tmp'] = 1
    summary = pd.merge(files, experiment, on=['tmp'])
    summary = summary.drop('tmp', axis=1)
    return(summary)


# In[5]:


summary = pd.concat(list(metadata_filtered.apply(lambda row : extract_summary(row), axis = 1)))


# In[6]:


# finish prepping experiment 
summary["Biosample type"] = summary["Biosample ontology"].str.split("/", expand = True)[2].str.split("_", expand = True)[0]
summary = summary.rename(columns = {"Accession": "Experiment accession"})

# Filter output types 
summary_filtered = summary[summary.output_type.isin(output_types)]


# # SAVE

# In[7]:


# Save
summary_filtered.to_csv(outfile, index=False)  

