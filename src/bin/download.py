#!/bin/python3

import requests
import json
import sys

ENCODE_URL="https://www.encodeproject.org/"

def get_encode_json(enc_id: str) -> dict:
    """Downloads the JSON object containing the metadata for this encode accession.
    """
    try:
        enc_meta = requests.get(f"{ENCODE_URL}/files/{enc_id}?format=json", headers={"accept": "application/json"}, allow_redirects=True).json()
    except OSError as e:
        print("ERROR in downloading accession metadata from ENCODE. Check your network connection!")
        raise e

    if not 'accession' in enc_meta:
        # there must have been an error downloading from ENCODE
        raise ValueError(f"ERROR: Found invalid metadata! Check the sample ID: {enc_id}")
    return enc_meta


def download_from_encode(enc_id: str, work_dir: str='./') -> [str, dict]:
    """Downloads a data file from ENCODE. Returns a path to the downloaded file and a dictionary containing some metainformation.
    """
    enc_meta = get_encode_json(enc_id)

    ## extract useful metadata from encode JSON, to later import into nextflow meta map
    meta = dict()
    meta["datatype"] = enc_meta["assay_term_name"] #TODO maybe switch/double check with pipelines[0] or azure?
    meta["ID"] = enc_id
    meta["format"] = enc_meta["file_format"]

    # download 
    path = f"{work_dir}/{enc_id}.{meta['format']}"
    with open(path, 'wb') as f:
        size = int(enc_meta["file_size"])
        chunksize = min(10_000_000, size//10)
        progress = 0
        for chunk in requests.get(f"{ENCODE_URL}{enc_meta['href']}", allow_redirects=True).iter_content(chunk_size=chunksize):
            f.write(chunk)
            progress += chunksize*100 // size
            print(progress, "% done", "\033[0K\r", sep='')
            # stolen from https://www.baeldung.com/linux/echo-printf-overwrite-terminal-line

    return path, meta

if __name__ == "__main__":
    ids = sys.argv[1:]
    print(ids)
    for i in ids:
        print(download_from_encode(i))
