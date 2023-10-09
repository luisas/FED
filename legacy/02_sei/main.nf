#!/bin/bash nextflow

fasta = "${params.datasetdir}/test_dataset/sco_genes.fa"
fasta_ch = Channel.fromPath("${params.fasta}").map{ it -> it[it.baseName,it]}

fasta_ch.view()