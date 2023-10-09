#!/usr/bin/env nextflow

nextflow.enable.dsl=2

log.info """\
	Emformer via NF
	=====================================
	"""
	.stripIndent()


include { stats } from "${baseDir}/modules/04_stats.nf"

params.input_dir = "${baseDir}/../../../../data/FED"
params.scripts="${baseDir}/scripts"

// Script
Channel.fromPath("${params.scripts}/04_stats_intersection.py").collect().set{script_stats}


// ---- Training --
// Assembly

params.head = "human"
params.dataset_path="${params.input_dir}/basenji/${params.head}/tfrecords_197k"
params.suppl_df="${params.input_dir}/suppl_${params.head}.pkl"

Channel.fromPath("${params.suppl_df}").collect().set{suppl}

Channel.fromPath("${params.dataset_path}/*")
       .ifEmpty('path directory is empty')
       .map{ it -> [baseName(it.name),it]}
       .set{dataset}

dataset.view()

// --- STATS
params.output_dir="${params.input_dir}/basenji/${params.head}/stats"


workflow {

	stats(script_stats, dataset, suppl, "thresholds_intersection.csv", "${params.output_dir}")


}


workflow.onComplete {
    println "Pipeline completed at: $workflow.complete"
    println "Execution status: ${ workflow.success ? 'OK' : 'failed' }"
}


def baseName(String string){
  if(string.contains("\\/")){
    return string.split("\\/")[-1].split("\\.").init().join('.')
  }else if(string.contains("\\.")){
    return string.split("\\.").init().join('.')
  }else{
    return string
  }
}
