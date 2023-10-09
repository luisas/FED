#!/usr/env nextflow

nextflow.enable.dsl=2

/*
*   Convert dataset with sequence length of 131k to 197k
*/

process split_list{
  storeDir "${outputdir}/tracks_chunks"

  input:
  path split_script
  path list
  val chunk_size
  val outputdir

  output:
  path "${baseName(list.toString())}_*", emit: chunks

  script:
  """
  python ${split_script} ${list} "${baseName(list.toString())}" ${chunk_size}
  """

}



process predict_eval{
   tag "${baseName(pickle_batch.toString())}"
   storeDir "${outputdir}/evaluation_files"

   input:
   path script
   path pickle_batch
   path model
   val outputdir
   path bin
   val head
   val eval_flag

   output:
   path "${baseName(pickle_batch.toString())}_pred.pkl", emit: preds

   script:
   """
   python ${script} ${pickle_batch} ${model} "${baseName(pickle_batch.toString())}_pred.pkl" ${head} ${eval_flag}
   """
}



process summary_df{
   tag "${baseName(pickle_batch.toString())}"
   storeDir "${outputdir}/evaluation_summary"

   input:
   path script
   path pickle_batch
   path targets
   val outputdir


   output:
   path "${baseName(pickle_batch.toString())}_eval_df.csv", emit: eval

   script:
   """
   python ${script} ${pickle_batch} ${targets} "${baseName(pickle_batch.toString())}_eval_df.csv"
   """
}


process summary_df_cross{
   tag "${baseName(pickle_batch.toString())}"
   storeDir "${outputdir}/dfs"

   input:
   path script
   path pickle_batch
   path tracks_train
   path tracks_pred
   val outputdir


   output:
   path "${baseName(pickle_batch.toString())}_df.csv", emit: eval

   script:
   """
   python3 ${script} ${pickle_batch} ${tracks_train} ${tracks_pred} "${baseName(pickle_batch.toString())}_df.csv"
   """
}


process mergeCSV {
  storeDir "${outputdir}/"

  input:
  path csv_file
  val outputdir

  output:
  path "correlation_evaluation.csv", emit: merged_csv

  script:
  """
  cat ${csv_file} > "correlation_evaluation.csv"
  """
}


workflow predict_eval_wf {
  take:
  script197
  scriptprep
  split_script
  input_pickle
  model
  outputdir
  bin
  targets
  head
  eval_flag
  chunk_size



  main:
  split_list(split_script, input_pickle, chunk_size, outputdir)
  split_list.out.chunks.flatten().set{ list_chunks }
	predict_eval(script197, list_chunks, model, outputdir, bin, head, eval_flag )
  summary_df(scriptprep, predict_eval.out.preds, targets, outputdir )
  mergeCSV(summary_df.out.eval.collect(), outputdir)

  emit:
  pred_eval_emit = predict_eval.out.preds
  summary_df_emit = summary_df.out.eval
}



workflow predict_wf {
  take:
  script197
  split_script
  script_eval_cross
  input_pickle
  model
  outputdir
  bin
  head
  eval_flag
  chunk_size
  tracks_train
  tracks_pred
  output_dir_eval

  main:
  split_list(split_script, input_pickle, chunk_size, outputdir)
  split_list.out.chunks.flatten().set{ list_chunks }
	predict_eval(script197, list_chunks, model, outputdir, bin, head, eval_flag )
  summary_df_cross(script_eval_cross, predict_eval.out.preds, tracks_train, tracks_pred, output_dir_eval)
  mergeCSV(summary_df_cross.out.eval.collect(), output_dir_eval)

  emit:
  pred_eval_emit = predict_eval.out.preds
}


def baseName(String string){
  if(string.contains("\\/")){
    return string.split("\\/")[-1].split("\\.").init().join('.')
  }else if(string.contains("\\.")){
    return string.split("\\.").init().join('.')
  }else{
    return string.split("\\/")[-1].split("\\.").init().join('.')
  }
}
