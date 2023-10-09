#!/usr/env nextflow

nextflow.enable.dsl=2

/*
*
*/

process evaluate_threshold_intersection{
  storeDir "${outputdir}/intersection_thresholds"
  tag "${id}"

  input:
  path script
  tuple val(id), path(batch)
  path suppl
  val outputdir

  output:
  path "${id}_thr_int_df.csv", emit: stats_out

  script:
  """
  python3 ${script} ${batch} ${suppl} "${id}_thr_int_df.csv"
  """

}


process mergeCSV {
  storeDir "${outputdir}/"

  input:
  path csv_file
  val outname
  val outputdir

  output:
  path "${outname}", emit: merged_csv

  script:
  """
  cat ${csv_file} > "${outname}"
  """
}


workflow stats {
  take:
  script
  batch
  suppl
  outname
  outputdir

  main:
	evaluate_threshold_intersection(script, batch, suppl, outputdir )
  mergeCSV(evaluate_threshold_intersection.out.stats_out.collect(), outname, outputdir)

  emit:
  tracks = mergeCSV.out.merged_csv
}
