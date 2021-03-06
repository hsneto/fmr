import cv2
import json
import numpy as np
from collections import namedtuple
from is_wire.core import Channel
from is_msgs.image_pb2 import Image
from is_wire.core.wire.conversion import WireV1

def read_options(file, verbose=False):
  """
  Read json file and return data as namedtuple

  Args:
    \-> file - json file
  """

  with open(file) as f:
    data = json.load(f)
  op = namedtuple("options", data.keys())(*data.values())

  if verbose:
    print(op)

  return op


def get_labels(expressions, commands, default):
  """
  Get all available labels and return those which were selected as a command

  Args:
    \-> list with all available labels
    \-> list with the chosen labels
    \-> default expressionto replace non-used labels

  Output:
    \-> new list of labels
  """

  command_labels = list(commands.values())

  # turn not used labels into default expression
  for i in range(len(expressions)):
    if expressions[i] not in command_labels:
      expressions[i] = default

  return expressions


def get_pb_image(input_image, encode_format='.jpeg', compression_level=0.8):
    if isinstance(input_image, np.ndarray):
        if encode_format == '.jpeg':
            params = [cv2.IMWRITE_JPEG_QUALITY, int(compression_level * (100 - 0) + 0)]
        elif encode_format == '.png':
            params = [cv2.IMWRITE_PNG_COMPRESSION, int(compression_level * (9 - 0) + 0)]
        else:
            return Image()        
        cimage = cv2.imencode(ext=encode_format, img=input_image, params=params)
        return Image(data=cimage[1].tobytes())
    elif isinstance(input_image, Image):
        return input_image
    else:
        return Image()


class StreamChannel(Channel):
  def consume(self, return_dropped=False):
    
    def clean_and_consume(timeout=None):
      self.amqp_message = None
      while self.amqp_message is None:
        self.connection.drain_events(timeout=timeout)
      return self.amqp_message
    
    _amqp_message = clean_and_consume()
    dropped = 0
    while True:
      try:
        # will raise an exceptin when no message remained
        _amqp_message = clean_and_consume(timeout=0.0)
        dropped += 1
      except:
        # returns last message
        msg = WireV1.from_amqp_message(_amqp_message)
        return (msg, dropped) if return_dropped else msg