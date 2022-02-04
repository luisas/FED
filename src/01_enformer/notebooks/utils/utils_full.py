import gzip
from collections import Mapping
import importlib
import kipoiseq
from kipoiseq import Interval
import pyfaidx
import pandas as pd
import numpy as np
import os
from tqdm import tqdm
import pickle
import sys
import tensorflow as tf
import tensorflow_hub as hub
import json
import functools


def _reduced_shape(shape, axis):
  if axis is None:
    return tf.TensorShape([])
  return tf.TensorShape([d for i, d in enumerate(shape) if i not in axis])

def organism_path(organism, prefix):
    return os.path.join(prefix, organism)

#
def get_dataset(organism, subset, prefix, num_threads=8):

    metadata = get_metadata(organism, prefix)

    dataset = tf.data.TFRecordDataset(tfrecord_files(organism, subset, prefix = prefix),
                                        compression_type='ZLIB',
                                        num_parallel_reads=num_threads)
    dataset = dataset.map(functools.partial(deserialize, metadata=metadata),
                            num_parallel_calls=num_threads)
    return dataset


def get_metadata(organism, prefix):
  # Keys:
  # num_targets, train_seqs, valid_seqs, test_seqs, seq_length,
  # pool_width, crop_bp, target_length
    path = os.path.join(organism_path(organism, prefix), 'statistics.json')
    with tf.io.gfile.GFile(path, 'r') as f:
        return json.load(f)


def tfrecord_files(organism, subset, prefix):
  # Sort the values by int(*).
  return sorted(tf.io.gfile.glob(os.path.join(
      organism_path(organism, prefix), 'tfrecords', f'{subset}-*.tfr'
  )), key=lambda x: int(x.split('-')[-1].split('.')[0]))


def deserialize(serialized_example, metadata):
    """Deserialize bytes stored in TFRecordFile."""
    feature_map = {
          'sequence': tf.io.FixedLenFeature([], tf.string),
          'target': tf.io.FixedLenFeature([], tf.string),
    }
    example = tf.io.parse_example(serialized_example, feature_map)
    sequence = tf.io.decode_raw(example['sequence'], tf.bool)
    sequence = tf.reshape(sequence, (metadata['seq_length'], 4))
    sequence = tf.cast(sequence, tf.float32)

    target = tf.io.decode_raw(example['target'], tf.float16)
    target = tf.reshape(target,
                          (metadata['target_length'], metadata['num_targets']))
    target = tf.cast(target, tf.float32)

    return {'sequence': sequence,
              'target': target}



class Enformer:

    def __init__(self, tfhub_url):
        self._model = hub.load(tfhub_url).model

    def predict_on_batch(self, inputs):
        predictions = self._model.predict_on_batch(inputs)
        return {k: v.numpy() for k, v in predictions.items()}

    @tf.function
    def contribution_input_grad(self, input_sequence,
                                  target_mask, output_head='human'):
        input_sequence = input_sequence[tf.newaxis]

        target_mask_mass = tf.reduce_sum(target_mask)
        with tf.GradientTape() as tape:
            tape.watch(input_sequence)
            prediction = tf.reduce_sum(
              target_mask[tf.newaxis] *
              self._model.predict_on_batch(input_sequence)[output_head]) / target_mask_mass

        input_grad = tape.gradient(prediction, input_sequence) * input_sequence
        input_grad = tf.squeeze(input_grad, axis=0)
        return tf.reduce_sum(input_grad, axis=-1)





class EnformerScoreVariantsRaw:

      def __init__(self, tfhub_url, organism='human'):
        self._model = Enformer(tfhub_url)
        self._organism = organism

      def predict_on_batch(self, inputs):
        ref_prediction = self._model.predict_on_batch(inputs['ref'])[self._organism]
        alt_prediction = self._model.predict_on_batch(inputs['alt'])[self._organism]

        return alt_prediction.mean(axis=1) - ref_prediction.mean(axis=1)


class EnformerScoreVariantsNormalized:

    def __init__(self, tfhub_url, transform_pkl_path,
                   organism='human'):
        assert organism == 'human', 'Transforms only compatible with organism=human'
        self._model = EnformerScoreVariantsRaw(tfhub_url, organism)
        with tf.io.gfile.GFile(transform_pkl_path, 'rb') as f:
          transform_pipeline = joblib.load(f)
        self._transform = transform_pipeline.steps[0][1]  # StandardScaler.

    def predict_on_batch(self, inputs):
        scores = self._model.predict_on_batch(inputs)
        return self._transform.transform(scores)


class EnformerScoreVariantsPCANormalized:

    def __init__(self, tfhub_url, transform_pkl_path,
                   organism='human', num_top_features=500):
        self._model = EnformerScoreVariantsRaw(tfhub_url, organism)
        with tf.io.gfile.GFile(transform_pkl_path, 'rb') as f:
          self._transform = joblib.load(f)
        self._num_top_features = num_top_features

    def predict_on_batch(self, inputs):
        scores = self._model.predict_on_batch(inputs)
        return self._transform.transform(scores)[:, :self._num_top_features]

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






class CorrelationStats(tf.keras.metrics.Metric):
    """Contains shared code for PearsonR and R2."""

    def __init__(self, reduce_axis=None, name='pearsonr'):
        """Pearson correlation coefficient.

        Args:
          reduce_axis: Specifies over which axis to compute the correlation (say
            (0, 1). If not specified, it will compute the correlation across the
            whole tensor.
          name: Metric name.
        """
        super(CorrelationStats, self).__init__(name=name)
        self._reduce_axis = reduce_axis
        self._shape = None  # Specified in _initialize.

    def _initialize(self, input_shape):
        # Remaining dimensions after reducing over self._reduce_axis.
        self._shape = _reduced_shape(input_shape, self._reduce_axis)

        weight_kwargs = dict(shape=self._shape, initializer='zeros')
        self._count = self.add_weight(name='count', **weight_kwargs)
        self._product_sum = self.add_weight(name='product_sum', **weight_kwargs)
        self._true_sum = self.add_weight(name='true_sum', **weight_kwargs)
        self._true_squared_sum = self.add_weight(name='true_squared_sum',
                                                 **weight_kwargs)
        self._pred_sum = self.add_weight(name='pred_sum', **weight_kwargs)
        self._pred_squared_sum = self.add_weight(name='pred_squared_sum',
                                                 **weight_kwargs)

    def update_state(self, y_true, y_pred, sample_weight=None):
        """Update the metric state.

        Args:
          y_true: Multi-dimensional float tensor [batch, ...] containing the ground
            truth values.
          y_pred: float tensor with the same shape as y_true containing predicted
            values.
          sample_weight: 1D tensor aligned with y_true batch dimension specifying
            the weight of individual observations.
        """
        if self._shape is None:
          # Explicit initialization check.
          self._initialize(y_true.shape)
        y_true.shape.assert_is_compatible_with(y_pred.shape)
        y_true = tf.cast(y_true, 'float32')
        y_pred = tf.cast(y_pred, 'float32')

        self._product_sum.assign_add(
            tf.reduce_sum(y_true * y_pred, axis=self._reduce_axis))

        self._true_sum.assign_add(
            tf.reduce_sum(y_true, axis=self._reduce_axis))

        self._true_squared_sum.assign_add(
            tf.reduce_sum(tf.math.square(y_true), axis=self._reduce_axis))

        self._pred_sum.assign_add(
            tf.reduce_sum(y_pred, axis=self._reduce_axis))

        self._pred_squared_sum.assign_add(
            tf.reduce_sum(tf.math.square(y_pred), axis=self._reduce_axis))

        self._count.assign_add(
            tf.reduce_sum(tf.ones_like(y_true), axis=self._reduce_axis))

    def result(self):
        raise NotImplementedError('Must be implemented in subclasses.')

    def reset_states(self):
        if self._shape is not None:
            tf.keras.backend.batch_set_value([(v, np.zeros(self._shape))
                                        for v in self.variables])


class PearsonR(CorrelationStats):
    """Pearson correlation coefficient.

          Computed as:
      ((x - x_avg) * (y - y_avg) / sqrt(Var[x] * Var[y])
      """

    def __init__(self, reduce_axis=(0,), name='pearsonr'):
        """Pearson correlation coefficient.

        Args:
          reduce_axis: Specifies over which axis to compute the correlation.
          name: Metric name.
        """
        super(PearsonR, self).__init__(reduce_axis=reduce_axis,
                                       name=name)

    def result(self):
        true_mean = self._true_sum / self._count
        pred_mean = self._pred_sum / self._count

        covariance = (self._product_sum
                      - true_mean * self._pred_sum
                      - pred_mean * self._true_sum
                      + self._count * true_mean * pred_mean)

        true_var = self._true_squared_sum - self._count * tf.math.square(true_mean)
        pred_var = self._pred_squared_sum - self._count * tf.math.square(pred_mean)
        tp_var = tf.math.sqrt(true_var) * tf.math.sqrt(pred_var)
        correlation = covariance / tp_var

        return correlation


class R2(CorrelationStats):
    """R-squared  (fraction of explained variance)."""

    def __init__(self, reduce_axis=None, name='R2'):
        """R-squared metric.

        Args:
          reduce_axis: Specifies over which axis to compute the correlation.
          name: Metric name.
        """
        super(R2, self).__init__(reduce_axis=reduce_axis,
                                 name=name)

    def result(self):
        true_mean = self._true_sum / self._count
        total = self._true_squared_sum - self._count * tf.math.square(true_mean)
        residuals = (self._pred_squared_sum - 2 * self._product_sum
                     + self._true_squared_sum)

        return tf.ones_like(residuals) - residuals / total


class MetricDict:
    def __init__(self, metrics):
        self._metrics = metrics

    def update_state(self, y_true, y_pred):
        for k, metric in self._metrics.items():
            metric.update_state(y_true, y_pred)

    def result(self):
        return {k: metric.result() for k, metric in self._metrics.items()}






def one_hot_encode(sequence):
    return kipoiseq.transforms.functional.one_hot_dna(sequence).astype(np.float32)
