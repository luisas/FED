include {ENRICH_BINARY; ENRICH_CONTINUOUS; } from "../modules/dress_up.nf"

workflow ENRICH{

    take: 
        genes_and_track
        mode
    
    main: 
        if(mode == "binary"){
            ENRICH_BINARY(genes_and_track, "${params.binary_intersection_min}")
            dressed_chunks = ENRICH_BINARY.out.bed
        }
        else{
            ENRICH_CONTINUOUS(genes_and_track)
            dressed_chunks = ENRICH_CONTINUOUS.out.bed
        }
           

    emit: 
        dressed_chunks
}
