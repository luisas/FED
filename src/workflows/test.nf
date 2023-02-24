
include {DOWNLOAD_FROM_METADATA_SHEET;} from "../modules/downloads.nf"
include {EXTRACT_FROM_BED;} from "../modules/preprocessing.nf"
include {ENRICH; } from "../subworkflows/enrich.nf"

metadata_download = Channel.fromPath( params.metadata_sheet, checkIfExists: true )
//assembly = Channel.fromPath( params.assembly, checkIfExists: true ) 
test_genes = Channel.fromPath( params.test_genes, checkIfExists: true )
//annotation_gtf = Channel.fromPath( params.annotation_gtf, checkIfExists: true )
annotation_bed = Channel.fromPath( params.annotation_bed, checkIfExists: true )


track_bed = Channel.fromPath( params.track_bed, checkIfExists: true )

// Do I w want to first call the peaks or first subselect the genes? 
workflow CREATE_TEST{
    
      // Prepare data
      //DOWNLOAD_FROM_METADATA_SHEET( metadata_download )
      // GTF_TO_BED( annotation_gtf ) todo     

      EXTRACT_FROM_BED( test_genes, annotation_bed)
      selected_chunks = EXTRACT_FROM_BED.out.bed      

      // map the track information on the test genes
      ENRICH( selected_chunks, track_bed, params.enrich_mode)
      // ID, YES/NO


      // Then after here you need to analyze 
      // Q1: for all the gene groups, check the concordance of the enrichment results 

}