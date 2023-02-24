include {ENRICH_BINARY; ENRICH_CONTINUOUS; } from "../modules/dress_up.nf"

workflow ENRICH{

    take: 
        bed
        track_bed
        mode
    
    main: 
        if(mode == "binary"){
            ENRICH_BINARY(bed, track_bed, "${params.binary_intersection_min}")
            dressed_chunks = ENRICH_BINARY.out.bed
        }
        else{
            ENRICH_CONTINUOUS(bed, track_bed)
            dressed_chunks = ENRICH_CONTINUOUS.out.bed
        }
           

    emit: 
        dressed_chunks
}