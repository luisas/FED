

include {FASTA_FROM_BED} from "../modules/preprocessing.nf"
include {SIMILARITY} from "../modules/alignment_utils.nf"

workflow SEQ_SIMILARITY{
    take: 
        chunks_and_assembly

    main: 
        // 1. Extract FA sequences
        FASTA_FROM_BED( chunks_and_assembly )
        // 2. Pairwise alignment 
        SIMILARITY( FASTA_FROM_BED.out.fasta )
}