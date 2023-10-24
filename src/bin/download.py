#!/usr/bin/env python3

import requests
import json
import sys
from multiprocessing import Pool
from functools import partial
from typing import List

ENCODE_URL = "https://www.encodeproject.org/"
PREFERRED_FORMATS = set({"bigwig", "bed"})

def get_encode_json(enc_id: str) -> dict:
    """Downloads the JSON object containing the metadata for this encode accession.
    """
    try:
        enc_meta = requests.get(f"{ENCODE_URL}/files/{enc_id}?format=json", headers={"accept": "application/json"}, allow_redirects=True).json()
    except OSError as e:
        print("ERROR in downloading accession metadata from ENCODE. Check your network connection!")
        raise e

    if not 'accession' in enc_meta or enc_meta['accession'] != enc_id:
        # there must have been an error downloading from ENCODE
        raise ValueError(f"ERROR: Found invalid metadata! Check the sample ID: {enc_id}")
    return enc_meta


def get_file_id(exp_meta: dict) -> str:
    """Takes metadata from an ENCODE experiment and searches for an ENCODE data file ID to download.
    This method searches among the files listed in an experiment JSON for a file with the appropriate format among the files listed as preferred default.
    """
    #exp_meta = get_encode_json(enc_id) # get experiment metadata
    ret = ''
    for file in exp_meta["files"]:
        if not bool(file["no_file_available"]) and\
                file["file_format"].lower() in PREFERRED_FORMATS:
                #bool(file["preferred_default"]) and\
                # apparently this field is not returned when queried through requests, it is returned when queried via curl however

            if int(file["file_size"]) < 10_000_000_000: # avoid accidentally downloading huge files
                ret = file["accession"]
                break # take the first file
    return ret


def download(enc_meta: dict, work_dir: str ='.') -> str:
    """Downloads a data file from ENCODE.
    Takes a metadata dict.
    Returns a path to the downloaded file.
    Throws an error if given a non-file ENCODE ID.
    """
    #enc_meta = get_encode_json(enc_id)
    # download 
    path = f"{work_dir}/{enc_meta['accession']}.{enc_meta['file_format']}"
    with open(path, 'wb') as f:
        size = int(enc_meta["file_size"])
        chunksize = min(10_000_000, size//10)
        progress = 0
        for chunk in requests.get(f"{ENCODE_URL}{enc_meta['href']}", allow_redirects=True).iter_content(chunk_size=chunksize):
            f.write(chunk)
            print(int(progress), "% done", end="\033[0K\r", sep='')
            # stolen from https://www.baeldung.com/linux/echo-printf-overwrite-terminal-line
            progress += chunksize*100 / size

    return path

def download_from_dataset(enc_id: str, work_dir: str ='.') -> tuple[str, dict]:
    """Takes an ENCODE experiment ID, extracts metadata and downloads the experiment file we are interested in (hopefully).
    """
    exp_meta = get_encode_json(enc_id)
    ## extract useful metadata from encode JSON, to later import into nextflow meta map
    meta = dict()
    meta["datatype"] = exp_meta["assay_term_name"]
    meta["ID"] = enc_id
    meta["organism"] = exp_meta["replicates"][0]["library"]["biosample"]["organism"]["scientific_name"] # hope this works everytime, coding seems to vary a bit?

    file_id = get_file_id(exp_meta)
    file_meta = get_encode_json(file_id)
    meta["FileID"] = file_id
    meta["format"] = file_meta["file_format"]

    return download(file_meta), meta

def p_download_from_dataset(ids: List[str], work_dir: str ='.', max_workers: int =4) -> List[tuple[str, dict] ]:
    with Pool(processes=max_workers) as p:
        return p.map(partial(download_from_dataset, work_dir=work_dir), ids)


if __name__ == "__main__":
    ids = sys.argv[1:]
    print(p_download_from_dataset(ids))
