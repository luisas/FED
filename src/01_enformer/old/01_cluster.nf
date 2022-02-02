log.info "=============================================="
log.info "           Emformer test on cluster           "
log.info "=============================================="


// Input directory
params.input_dir = "/users/cn/lsantus/data/FED"
//input_dir = Channel.fromPath("${params.input_dir}/*").collect()

// Output directory
output_dir="${params.input_dir}/hd5"

params.scripts="${baseDir}/scripts"

py_197k_script = Channel
                    .fromPath("${params.scripts}/01_create_197k_validationset.py")



process create_197K_dataset{
   storeDir "${output_dir}"

   input:
   file tfr 
   file script from py_197k_script

   output:


   script:
   """
   python ${script} ${x}
   """
}
