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
//Channel.fromPath("${params.scripts}/03_basenji_data.py").collect().set{basenji_data_script}
Channel.fromPath("${params.scripts}/02_pred_eval_fromtfr.py").collect().set{py_pred_script}
Channel.fromPath("${params.scripts}/01b_split_list.py").collect().set{split_script}
Channel.fromPath("${params.scripts}/02c_prep_df_cross.py").collect().set{cross_script}

// Head params
params.head_train = "human"
params.head_pred = "bosTaurus"


// ---- Training --
// Assembly
Channel.fromPath("${params.input_dir}/assemblies/${params.head_train}/*.fa").collect().set{fasta}
Channel.fromPath("${params.input_dir}/assemblies/${params.head_train}/*.fa.fai").collect().set{fastaidx}



// --- Targets - bw
Channel.fromPath("${params.input_dir}/basenji/${params.head_train}/targets.csv").collect().set{targets_bw}



params.input_dir = "${baseDir}/../../../../data/FED"
params.scripts="${baseDir}/scripts"





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


// -- Evalutation
params.evaluation_tracks = "cerebellum"
Channel.fromPath("${params.output_dir}/${params.evaluation_tracks}/train_tracks.csv").collect().set{tracks_train}
Channel.fromPath("${params.output_dir}/${params.evaluation_tracks}/pred_tracks.csv").collect().set{tracks_pred}
params.output_dir_eval = "${params.output_dir}/${params.evaluation_tracks}"




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
