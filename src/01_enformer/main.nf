#!/usr/bin/env nextflow

nextflow.enable.dsl=2

log.info """\
	Emformer via NF
	=====================================
	"""
	.stripIndent()


include { enformer_human } from "${baseDir}/modules/01_enformer.nf"

params.head="human"
params.input_dir = "${baseDir}/../../../../data/FED"
params.output_dir="${params.input_dir}/basenji/${params.head}/tfrecords_197k"
params.scripts="${baseDir}/scripts"
params.tfrecords_131_path="${params.input_dir}/basenji/${params.head}/tfrecords"

Channel.fromPath("${params.scripts}/01_create_197k_dataset.py").collect().set{py_197k_script}
Channel.fromPath("${params.input_dir}/basenji/${params.head}/statistics.json").collect().set{metadata}
Channel.fromPath("${params.input_dir}/hg38.fa").collect().set{fasta}
Channel.fromPath("${params.input_dir}/hg38.fa.fai").collect().set{fastaidx}
Channel.fromPath("${params.input_dir}/basenji/${params.head}/00_enformer_dict_seqs_${params.head}.h5").collect().set{dict}
Channel.fromPath("${params.tfrecords_131_path}/*")
       .ifEmpty('tfrecords_131_path directory is empty')
       .map{ it -> [baseName(it.toString()),it]}
       .set{tfrecords_131}

tfrecords_131.view()

workflow {
	enformer_human(py_197k_script, tfrecords_131, metadata, fasta, fastaidx, dict, "${params.output_dir}")
  enformer_human.out.tfrecords_197_emit.view()
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
