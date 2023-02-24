FROM ubuntu:16.04

RUN apt-get update && apt-get install -y zlib1g-dev build-essential wget

RUN apt-get update && apt-get -y upgrade

RUN apt-get install -y python3-pip

RUN pip3 install --upgrade "pip < 21.0"

RUN pip3 install pandas biopython

RUN apt-get install -y bedtools