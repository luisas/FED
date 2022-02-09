#!/usr/env nextflow

nextflow.enable.dsl=2

/*
*   Convert dataset with sequence length of 131k to 197k
*/

process create_197K_dataset{
   tag "${baseName(id)}"
   storeDir "${outputdir}"


   input:
   path script
   tuple val(id), path(tfr_batch)
   path metadata
   path fasta
   path fastaidx
   path dict_sequences_131k
   val outputdir

   output:
   path "${baseName(id)}_197k.pkl", emit: tfrecords_197

   script:
   """
   echo ${tfr_batch}
   echo ${baseName(id)}

   python ${script} ${tfr_batch} ${metadata} ${fasta} ${dict_sequences_131k} "${baseName(id)}_197k.pkl"
   """
}



workflow enformer_prep197 {
  take:
  script197
  input_tfr
  metadata
  fasta
  fastaidx
  dict_sequences_131k
  outputdir


  main:
	create_197K_dataset(script197,input_tfr, metadata, fasta, fastaidx, dict_sequences_131k,outputdir )

  emit:
  tfrecords_197_emit = create_197K_dataset.out.tfrecords_197
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
