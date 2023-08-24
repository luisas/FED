

process ENRICH_BINARY{
    
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



process ENRICH_CONTINUOUS{

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
    """
}