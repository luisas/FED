

process DOWNLOAD_FROM_METADATA_SHEET{

    storeDir "${params.outdir}/downloads/${organism}/${assay}/${biosample}/"
    tag("${assay}-${organism}-${biosample}-${id}")

    input:
    tuple val(assay), val(organism), val(file_format), val(output_type), val(biosample), val(id), val(link)

    output:
    tuple val(assay), val(organism), val(file_format), val(output_type), val(biosample), val(id), file("${id}*")

    script:
    """
    if [[ ${link} =~ \.gz\$ ]]; then
        wget ${link} 
        gunzip *.gz
    else
        wget ${link}
    fi
    """

}


