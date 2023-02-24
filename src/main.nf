/*
 * enables modules
 */
nextflow.enable.dsl = 2


include { CREATE_TEST; } from './workflows/test.nf'


workflow {
    CREATE_TEST()
}

/*
 * completion handler
 */
 workflow.onComplete {

     def msg = """\
         Pipeline execution summary
         ---------------------------
         Completed at: ${workflow.complete}
         Duration    : ${workflow.duration}
         Success     : ${workflow.success}
         workDir     : ${workflow.workDir}
         exit status : ${workflow.exitStatus}
         """
         .stripIndent()

}
