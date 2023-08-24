
// Given a list of IDs and the reference bed file, extract the corresponding regions and save in BED file
process EXTRACT_FROM_BED {

    container "luisas/bedtools"
    storeDir "${params.gene_lists}"
    label "small"

    input:
    file test_genes
    file annotation_bed

    output:
    path("*.bed"), emit: bed

    script:
    """
    extract_ids_from_bed.py ${test_genes} ${annotation_bed} ${test_genes.baseName}.bed
    """
}

process MERGE_BEDS{

    container "luisas/bedtools:2"
    storeDir "${params.outdir}/downloads/${organism}/${assay}/collapsed/"
    label "small"

    input:
    tuple val(assay), val(organism), val(file_format), val(output_type), file(samples)

    output:
    tuple val(assay), val(organism), val(file_format), val(output_type), file("${assay}.bed"), emit: bed

    script:
    """
    for i in "*.bed"; do
        sort -i \$i > \$i.sorted
    done
    bedops -m *.sorted > ${assay}.bed
    """    
}


process FASTA_FROM_BED{
    
    container "luisas/bedtools"
    storeDir "${params.outdir}/downloads/${organism}/${assay}/collapsed/"
    
    input:
    tuple val(bed), val(assembly)
    
    output:
    path("${bed.baseName}.fa"), emit: fasta
    
    script:
    """
    bedtools getfasta -fi ${assembly} -bed ${bed} -fo ${bed.baseName}.fa
    """
}



