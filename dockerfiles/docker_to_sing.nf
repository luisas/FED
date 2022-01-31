

params.dockerfile = "$HOME/sample.fa"

sequences = file(params.in)
SPLIT = (System.properties['os.name'] == 'Mac OS X' ? 'gcsplit' : 'csplit')

process splitSequences {

    input:
    file 'input.fa' from sequences

    output:
    file 'seq_*' into records

    """
    $SPLIT input.fa '%^>%' '/^>/' '{*}' -f seq_
    """

}


result.subscribe { println it }
