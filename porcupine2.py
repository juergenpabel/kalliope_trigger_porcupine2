#!/usr/bin/python3

import logging
import time
from threading import Thread
from kalliope import Utils
from pvporcupine import Porcupine


logging.basicConfig()
logger = logging.getLogger("kalliope")


class Porcupine2(Thread):
	def __init__(self, **kwargs):
		super(MQTT, self).__init__()
		logger.debug("[trigger:porcupine2] __init__()")
		self.input_device_index = kwargs.get('input_device_index', None)
		self.callback = kwargs.get('callback', None)
		if self.callback is None:
			raise MissingParameterException("Trigger callback method is missing (keyword argument 'callback')")

		self.config = dict()
		for key in ['access_key', 'library_path', 'model_path', 'keyword_paths', 'keywords', 'sensitivities']:
			self.config[key] = kwargs.get(key, "")
		if len(self.config['access_key']) == 0:
			raise MissingParameterException("mandatory 'access_key' is missing in configuration")

		self.config['keyword_paths'] = [keyword_path.trim()       for keyword_path in self.config['keyword_paths'].split(',')]
		self.config['keywords']      = [keyword.trim()            for keyword      in self.config['keywords'].split(',')]
		self.config['sensitivities'] = [float(sensitivity.trim()) for sensitivity  in self.config['sensitivities'].split(',')]
		self.config['keyword_paths'] = [Utils.get_real_file_path(keyword_path) for keyword_path in self.config['keyword_paths']]

		self.porcupine = Porcupine(self.config['access_key'], self.config['library_path'], self.config['model_path'],
		                           self.config['keyword_paths'], self.config['keywords'], self.config['sensitivities'])


	def run(self):
		logger.debug("[trigger:porcupine2] run()")
		self.pyaudio = pyaudio.PyAudio()
		self.audio_stream = self.pyaudio.open(rate=self.porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True,
		                                 frames_per_buffer=self.porcupine.frame_length, input_device_index=self.input_device_index)
		self.paused = False
		while True:
			if self.pause is False:
				pcm = self.audio_stream.read(self.porcupine.frame_length)
				pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
				keyword = self.porcupine.process()
				if keyword >= 0:
					logger.info("[trigger:porcupine2] keyword '{}' detected".format(in self.config['keywords'][keyword]))
					self.callback()
					self.paused = True
			else:
				time.sleep(0.1)

	def pause(self):
		logger.debug("[trigger:porcupine2] pause()")
		self.paused = True

	def unpause(self):
		logger.debug("[trigger:porcupine2] unpause()")
		self.paused = False

