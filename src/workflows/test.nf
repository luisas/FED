
include {DOWNLOAD_FROM_METADATA_SHEET;} from "../modules/downloads.nf"
include {EXTRACT_FROM_BED; MERGE_BEDS; } from "../modules/preprocessing.nf"
include {RUN_ENRICHMENT_ANALYSIS; } from "../subworkflows/enrichment_analysis.nf"
include {SEQ_SIMILARITY; } from "../subworkflows/sequence_similarity.nf"


metadata_download = Channel.fromPath( params.metadata_sheet, checkIfExists: true )
assembly = Channel.fromPath( params.assembly, checkIfExists: true ).map{it -> [it.parent.name, it]} 
test_genes = Channel.fromPath( params.test_genes, checkIfExists: true )
annotation_bed = Channel.fromPath( params.annotation_bed, checkIfExists: true )



metadata = Channel.fromPath(params.metadata_sheet).splitCsv(header : true)
                     .map { row -> ["${row["assay_title"]}",
                                     "${row["Organism"]}",
                                     "${row["file_format"]}", 
                                     "${row["output_type"]}", 
                                     "${row["Biosample term name"]}",
                                     "${row["File accession"]}",
                                     "${row["link"]}"] }


//metadata = metadata.filter{ it[2] == "bed"}

// Do I w want to first call the peaks or first subselect the genes? 
workflow CREATE_TEST{
    
      // Prepare the bed file with the test genes
      selected_chunks = EXTRACT_FROM_BED( test_genes, annotation_bed)

      // Downloand tracks
      samples = DOWNLOAD_FROM_METADATA_SHEET( metadata )
      
      // Run the enrichment analysis
      RUN_ENRICHMENT_ANALYSIS(samples, selected_chunks)

}