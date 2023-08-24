

process SIMILARITY{
    container 'luisas/foldseek_tcoffee:2'
    storeDir "${params.outdir}/stats/sim/"
    label "small"
    
    input:
    path(fasta)
    
    output:
    path("${fasta.baseName}.sim"), emit: sim
    
    script:
    """
    t_coffee -other_pg seq_reformat -in ${fasta} -output sim_idscore -type=dna > ${fasta.baseName}.sim
    """
}