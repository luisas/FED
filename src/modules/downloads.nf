

process DOWNLOAD_FROM_METADATA_SHEET{

    storeDir "${params.outdir}/downloads"

    input:
    file metadata_sheet

    output:
    path("*"), emit: downloads

    script:
    """
    cut -f 1,48 ${metadata_sheet} | tail -n +2 | while read id track; do
        echo \$id
        echo \$track
        wget -O \$track
    done
    """
}


