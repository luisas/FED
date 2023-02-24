

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