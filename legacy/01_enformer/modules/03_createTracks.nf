#!/usr/env nextflow

nextflow.enable.dsl=2

/*
*   Convert dataset with sequence length of 131k to 197k
*/

process createTracks{
  storeDir "${outputdir}/chunks"

  input:
  path basenji_data_script
  path fasta
  path bw_txt

  output:
  path "*", emit: tracks

  script:
  """
  python ${basenji_data_script} ${fasta} ${bw_txt}
  """

}


workflow prep_head_tracks {
  take:
  basenji_data_script
  fasta
  bw_txt

  main:
	createTracks(basenji_data_script, fasta, bw_txt )

  emit:
  tracks = createTracks.out.tracks
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
