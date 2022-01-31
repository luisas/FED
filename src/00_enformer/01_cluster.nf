log.info "=============================================="
log.info "           Emformer test on cluster           "
log.info "=============================================="



// CONFIG FILE: ../configs/nextflow.annotation.config

// Input directory
params.input_dir = "/gpfs/projects/bsc83/Data/Ebola/01_bulk_RNA-Seq_lncRNAs_annotation/"

// Output directory
output_dir="${params.input_dir}/03_novel_lncRNAs_list/99_benchmark_annotation/"

// Reference genome ( Macaca Mulatta rheMac10 )
reference_assembly = Channel.fromPath("/gpfs/projects/bsc83/Data/assemblies/ensembl/release-100/rheMac10/Macaca_mulatta.Mmul_10.dna.toplevel.fa").collect()

// Reference annotation ( Macaca Mulatta rheMac10)
gtf = Channel.fromPath("/gpfs/projects/bsc83/Data/gene_annotation/ensembl_release100/rheMac10/Macaca_mulatta.Mmul_10.100.gtf")



process create_197K_dataset{
   storeDir "${output_dir_sub}/00_preliminaryfiles/"

   input:
   file gtf2bed
   file candidates from gtf

   output:
   file("${candidates.baseName}.bed12") into candidatesbed

   script:
   """
   Rscript ${gtf2bed} ${candidates} ${candidates.baseName}.bed12
   """
}
