

include {FASTA_FROM_BED} from "../modules/preprocessing.nf"


workflow SEQ_SIMILARITY{
    take: 
        selected_chunks
        assembly

    main: 
        // 1. Extract FA sequences 
        FASTA_FROM_BED( selected_chunks, assembly)
        // 2. pairwise alignment 
        // get all pairs 
        // compute the pairwise alignment
        // chec
}