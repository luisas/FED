

process EXTRACT_BED{
    
    container "luisas/bedtools"
    storeDir "${params.enrichment}/"

    input:
    tuple file(chunks), val(assay), val(organism), val(file_format), val(output_type), val(biosample), val(id), file(track)
    val min_overlap

    output:
    path("${chunks.baseName}_${track.baseName}_${min_overlap}_overlap_binary.txt"), emit: bed

    script:
    """
    bedtools intersect -a ${chunks} -b ${track} -f ${params.binary_intersection_min} -c  > ${chunks.baseName}_overlap.txt
    # Extract the ID of the chunk if overlaps or not 
    awk '{if(\$NF>0) print \$5"\t1"; else print \$5"\t0"}' ${chunks.baseName}_overlap.txt > ${chunks.baseName}_${track.baseName}_${min_overlap}_overlap_binary.txt
    """
}

// Given a list of IDs and the reference bed file, extract the corresponding regions and save in BED file
process EXTRACT_ID_FROM_BED {

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

process EXTRACT_BIGWIG{

    container "luisas/bedtools"
    storeDir "${params.enrichment}"

    input:
    tuple file(chunks), val(assay), val(organism), val(file_format), val(output_type), val(biosample), val(id), file(track)

    output:
    path("*.bed"), emit: bed

    script:
    """
    # extract the whole bigWig from the bed file 
    echo "Not implemented yet"
	 # use https://github.com/CRG-Barcelona/bwtool/wiki/extract ?
    """
}
