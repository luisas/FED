
#OLDFILE="/home/luisasantus/Desktop/crg_cluster/data/FED/basenji/human/data_human_sequences_noSubsetInfo.bed"
#CHAIN="/home/luisasantus/Desktop/crg_cluster/data/FED/ucsc/chains/hg38ToMm10.over.chain"
#NEWFILE="/home/luisasantus/Desktop/crg_cluster/data/FED/basenji/human/liftover/data_human_sequences_lifted.bed"
#UNMAPPED="/home/luisasantus/Desktop/crg_cluster/data/FED/basenji/human/liftover/data_human_sequences_unmapped.bed"
#liftover -bedPlus=3 -tab ${OLDFILE} ${CHAIN} ${NEWFILE} ${UNMAPPED}
