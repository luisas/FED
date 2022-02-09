#!/usr/bin/env nextflow

nextflow.enable.dsl=2

log.info """\
	Emformer via NF
	=====================================
	"""
	.stripIndent()


include { prep_head_tracks } from "${baseDir}/modules/03_createTracks.nf"


params.input_dir = "${baseDir}/../../../../data/FED"
params.scripts="${baseDir}/scripts"

// Script
Channel.fromPath("${params.scripts}/03_basenji_data.py").collect().set{basenji_data_script}

// Head params
params.head_train="bosTaurus"


// ---- Training --
// Assembly
Channel.fromPath("${params.input_dir}/assemblies/${params.head_train}/*.fa").collect().set{fasta}
Channel.fromPath("${params.input_dir}/assemblies/${params.head_train}/*.fa.fai").collect().set{fastaidx}



// --- Targets - bw
Channel.fromPath("${params.input_dir}/basenji/${params.head_train}/targets.csv").collect().set{targets_bw}


workflow {

		prep_head_tracks(basenji_data_script, fasta, fastaidx, targets_bw)

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
