#!/usr/bin/python3

import logging
import time
from os.path import basename, expanduser
from threading import Thread
from kalliope import Utils
from kalliope.core.NeuronModule import MissingParameterException
from pvporcupine import Porcupine, create as new_Porcupine
import pyaudio
import struct


logging.basicConfig()
logger = logging.getLogger("kalliope")


class Porcupine2(Thread):
	def __init__(self, **kwargs):
		super(Porcupine2, self).__init__()
		logger.debug("[trigger:porcupine2] __init__()")
		self.input_device_index = kwargs.get('input_device_index', None)
		self.callback = kwargs.get('callback', None)
		if self.callback is None:
			raise MissingParameterException("Trigger callback method is missing (keyword argument 'callback')")

		self.config = dict()
		for key in ['access_key_file', 'access_key', 'library_path', 'model_path', 'keyword_paths', 'sensitivities']:
			self.config[key] = kwargs.get(key, None)
		if self.config['access_key_file'] is None and self.config['access_key'] is None:
			raise MissingParameterException("mandatory 'access_key' (or 'access_key_file') is missing in configuration")

		if self.config['access_key_file'] is not None:
			with open(expanduser(self.config['access_key_file']), 'r') as file:
				self.config['access_key'] = file.readline().strip()
			del self.config['access_key_file']

		if self.config['keyword_paths'] is not None:
			self.config['keyword_paths'] = [keyword_path.strip() for keyword_path in self.config['keyword_paths'].split(',')]
			self.config['keyword_paths'] = [Utils.get_real_file_path(keyword_path) for keyword_path in self.config['keyword_paths']]
		if type(self.config['sensitivities']) is float:
			self.config['sensitivities'] = [self.config['sensitivities']]
		self.porcupine = None
		self.pyaudio = None
		self.audio_stream = None


	def run(self):
		logger.debug("[trigger:porcupine2] run()")
		self.porcupine = new_Porcupine(access_key=self.config['access_key'], library_path=self.config['library_path'],
		                           model_path=self.config['model_path'], keyword_paths=self.config['keyword_paths'],
		                           sensitivities=self.config['sensitivities'])
		self.pyaudio = pyaudio.PyAudio()
		self.audio_stream = self.pyaudio.open(rate=self.porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True,
		                                      frames_per_buffer=self.porcupine.frame_length, input_device_index=self.input_device_index)
		self.audio_stream_open = None
		while True:
			if self.audio_stream is not None:
				pcm = self.audio_stream.read(self.porcupine.frame_length)
				pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
				keyword = self.porcupine.process(pcm)
				if keyword >= 0:
					logger.info("[trigger:porcupine2] keyword from '{}' detected".format(basename(self.config['keyword_paths'][keyword])))
					self.pause()
					self.callback()
			else:
				if self.audio_stream_open is not None:
					self.audio_stream_open.close()
					self.audio_stream_open = None
				time.sleep(0.1)


	def pause(self):
		if self.audio_stream is not None:
			logger.debug("[trigger:porcupine2] pause()")
			if self.pyaudio is not None:
				self.audio_stream_open = self.audio_stream
				self.audio_stream = None


	def unpause(self):
		if self.audio_stream is None:
			logger.debug("[trigger:porcupine2] unpause()")
			if self.pyaudio is not None:
				self.audio_stream = self.pyaudio.open(rate=self.porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True,
				                                      frames_per_buffer=self.porcupine.frame_length, input_device_index=self.input_device_index)

