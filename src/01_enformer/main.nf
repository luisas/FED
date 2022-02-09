#!/usr/bin/env nextflow

nextflow.enable.dsl=2

log.info """\
	Emformer via NF
	=====================================
	"""
	.stripIndent()


include { enformer_prep197 } from "${baseDir}/modules/01_enformer_prep.nf"
include { predict_eval_wf;  predict_wf } from "${baseDir}/modules/02_enformer_pred.nf"


params.input_dir = "${baseDir}/../../../../data/FED"
params.scripts="${baseDir}/scripts"


// Script
Channel.fromPath("${params.scripts}/01_create_197k_dataset.py").collect().set{py_197k_script}
Channel.fromPath("${params.scripts}/02_pred_eval.py").collect().set{py_pred_script}
Channel.fromPath("${params.scripts}/02b_prep_df.py").collect().set{prep_df_script}
Channel.fromPath("${params.scripts}/01b_split_list.py").collect().set{split_script}
// Model
Channel.fromPath("${params.input_dir}/enformer/1").collect().set{model}
params.bin="${baseDir}/bin"
Channel.fromPath("${params.bin}/*.py").collect().set{bin}

// Head params
params.head_train="human"
params.head_pred="human"
params.eval = "eval"

// ---- Training --
// Assembly
Channel.fromPath("${params.input_dir}/assemblies/${params.head_train}/*.fa").collect().set{fasta}
Channel.fromPath("${params.input_dir}/assemblies/${params.head_train}/*.fa.fai").collect().set{fastaidx}
params.tfrecords_131_path="${params.input_dir}/basenji/${params.head_train}/tfrecords"
params.output_dir_197="${params.input_dir}/basenji/${params.head_train}/tfrecords_197k"
Channel.fromPath("${params.input_dir}/basenji/${params.head_train}/statistics.json").collect().set{metadata}
Channel.fromPath("${params.input_dir}/basenji/${params.head_train}/00_enformer_dict_seqs_${params.head_train}.h5").collect().set{dict}
// Head channels
Channel.fromPath("${params.tfrecords_131_path}/*")
       .ifEmpty('tfrecords_131_path directory is empty')
       .map{ it -> [baseName(it.toString()),it]}
       .set{tfrecords_131}


// --- Prediction
params.output_dir="${params.input_dir}/enformer/${params.head_train}/${params.head_pred}/pred_standard"
Channel.fromPath("${params.input_dir}/basenji/${params.head_pred}/targets.csv").collect().set{targets}


workflow {


	// Prepare dataset 197K
	enformer_prep197(py_197k_script, tfrecords_131, metadata, fasta, fastaidx, dict, "${params.output_dir_197}")

	// Evaluate
	if("${params.eval}" == "eval")

		predict_eval_wf(py_pred_script,
										prep_df_script,
										split_script,
			 							enformer_prep197.out.tfrecords_197_emit , model,
										"${params.output_dir}", bin, targets,
										"${params.head_pred}",
										"eval",
										25)

	else
		predict_wf(py_pred_script, split_script, enformer_prep197.out.tfrecords_197_emit , model, "${params.output_dir}", bin, "${params.head_pred}", "false", 25)



	// Predict and evaluate
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
