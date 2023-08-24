include {ENRICH; ENRICH as ENRICH2} from "../subworkflows/enrich.nf"
include {MERGE_BEDS; } from "../modules/preprocessing.nf"

workflow RUN_ENRICHMENT_ANALYSIS{

    take: 
        samples
        selected_chunks

    main: 
        // 1. Map the individual track information on the test genes
        genes_and_samples_binary = selected_chunks.combine(samples).filter{ it[3] == "bed"}
        ENRICH( genes_and_samples_binary, "binary")


        // 2. Collapse all the tracks into a single file and perform the enrichment analysis
        grouped_samples = samples.filter{ it[2] == "bed"}
                                .map {it -> [it[0], it[1], it[2], it[3], it[6]]}
                                .groupTuple(by:[0,1,2,3])


        grouped_samples.view()
                                    
        collapsed_bed = MERGE_BEDS( grouped_samples ).map{it -> [it[0], it[1], it[2], it[3], "", "", it[4]]}

        gene_and_collapsed_track = selected_chunks.combine(collapsed_bed)
        ENRICH2( gene_and_collapsed_track, "binary")

    emit: 
        enrichments_biosamples = ENRICH.out.dressed_chunks
        enrichments_pooled = ENRICH2.out.dressed_chunks

}