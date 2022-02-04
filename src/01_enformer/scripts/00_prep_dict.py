import pandas as pd
import kipoiseq
from kipoiseq import Interval
import pyfaidx
import numpy as np

mouse_sequences = "/home/luisasantus/Desktop/crg_cluster/data/FED/basenji/mouse/mouse_sequences.bed"
fasta_file = "/home/luisasantus/Desktop/crg_cluster/data/FED/hg38.fa"



mouse_sequences = "/users/cn/lsantus/data/FED/basenji/mouse/mouse_sequences.bed"
fasta_file = "/users/cn/lsantus/data/FED/hg38.fa"
logfile = "/users/cn/lsantus/data/FED/basenji/mouse/log.txt"

df = pd.read_csv(mouse_sequences, memory_map=True, header=None, index_col=False, delimiter="\t")
# keep only validation intervals
validation_intervals= df[df[3]=="valid"]
#validation_intervals = validation_intervals.head()
# create list with interval
interval_list = list()
validation_intervals.apply(lambda row : interval_list.append(kipoiseq.Interval(row[0],row[1], row[2])), axis = 1)

def one_hot_encode(sequence):
    return kipoiseq.transforms.functional.one_hot_dna(sequence).astype(np.float32)

class FastaStringExtractor:

    def __init__(self, fasta_file):
        self.fasta = pyfaidx.Fasta(fasta_file)
        self._chromosome_sizes = {k: len(v) for k, v in self.fasta.items()}

    def extract(self, interval: Interval, **kwargs) -> str:
        # Truncate interval if it extends beyond the chromosome lengths.
        chromosome_length = self._chromosome_sizes[interval.chrom]
        trimmed_interval = Interval(interval.chrom,
                                    max(interval.start, 0),
                                    min(interval.end, chromosome_length),
                                    )
        # pyfaidx wants a 1-based interval
        sequence = str(self.fasta.get_seq(trimmed_interval.chrom,
                                          trimmed_interval.start + 1,
                                          trimmed_interval.stop).seq).upper()
        # Fill truncated values with N's.
        pad_upstream = 'N' * max(-interval.start, 0)
        pad_downstream = 'N' * max(interval.end - chromosome_length, 0)
        return pad_upstream + sequence + pad_downstream

    def close(self):
        return self.fasta.close()


def get_metadata(metadata):
    with tf.io.gfile.GFile(metadata, 'r') as f:
        return json.load(f)

def get_dataset(tfr, metadata):

    metadata = get_metadata(metadata)

    dataset = tf.data.TFRecordDataset(tfrecord, compression_type='ZLIB')

    dataset = dataset.map(functools.partial(deserialize, metadata=metadata))

    return dataset



fasta_extractor = FastaStringExtractor(fasta_file)
print("Fasta extracted")
# Create dictionary for search (can be improved! quite slow)
mouse_validation_dict = {}
i = 0
for interval in interval_list:
    print(i)
    i = i+1

    with open(logfile, "a") as file_object:
        file_object.write(str(i))
        file_object.write("\n")
        file_object.write("-------------")
        file_object.write("\n")
    sequence = one_hot_encode(fasta_extractor.extract(interval))
    mouse_validation_dict[interval] = sequence

print("Intervaldir done")
outputdir = "/home/luisasantus/Desktop/crg_cluster/data/FED/basenji/mouse"

enformer_dict_file = os.path.join(outputdir,'00_enformer_dict_seqs_mouse.h5')
# Step 2
with open(enformer_dict_file, 'wb') as config_dictionary_file:
    pickle.dump(mouse_validation_dict, config_dictionary_file)
