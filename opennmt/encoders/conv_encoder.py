"""Define convolution-based encoders."""

import tensorflow as tf

from opennmt.encoders.encoder import Encoder
from opennmt.layers import common
from opennmt.layers import position


class ConvEncoder(Encoder):
  """An encoder that applies a convolution over the input sequence
  as described in https://arxiv.org/abs/1611.02344.
  """

  def __init__(self,
               num_layers,
               num_units,
               kernel_size=3,
               dropout=0.3,
               position_encoder_class=position.PositionEmbedder):
    """Initializes the parameters of the encoder.

    Args:
      num_layers: The number of convolutional layers.
      num_units: The number of output filters.
      kernel_size: The kernel size.
      dropout: The probability to drop units from the inputs.
      position_encoder: The :class:`opennmt.layers.position.PositionEncoder`
        class to use for position encoding (or a callable that returns such
        class).
    """
    super(ConvEncoder, self).__init__()
    self.dropout = dropout
    self.position_encoder = None
    if position_encoder_class is not None:
      self.position_encoder = position_encoder_class()
    self.cnn_a = [
        tf.keras.layers.Conv1D(num_units, kernel_size, padding="same")
        for _ in range(num_layers)]
    self.cnn_c = [
        tf.keras.layers.Conv1D(num_units, kernel_size, padding="same")
        for _ in range(num_layers)]

  def call(self, inputs, sequence_length=None, training=None):
    if self.position_encoder is not None:
      inputs = self.position_encoder(inputs)
    inputs = common.dropout(inputs, self.dropout, training=training)

    cnn_a = _cnn_stack(self.cnn_a, inputs)
    cnn_c = _cnn_stack(self.cnn_c, inputs)

    outputs = cnn_a
    state = tf.reduce_mean(cnn_c, axis=1)
    return (outputs, state, sequence_length)

def _cnn_stack(layers, inputs):
  next_input = inputs

  for l, layer in enumerate(layers):
    outputs = layer(next_input)
    # Add residual connections past the first layer.
    if l > 0:
      outputs += next_input
    next_input = tf.tanh(outputs)

  return next_input
