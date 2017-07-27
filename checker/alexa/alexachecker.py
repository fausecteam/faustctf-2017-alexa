#!/usr/bin/python

import hashlib
import os
import random
import re
import uuid

import numpy as np
import requests
from spectrogram.stft import stft, istft
from spectrogram.watermarking import convert_wav_to_ogg, embed_text
from ctf_gameserver.checker import BaseChecker, OK, NOTFOUND, NOTWORKING, TIMEOUT
from lxml import html
from scipy.io import wavfile

AUDIO_SOURCE_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")
TMP_DIRECTORY = "/tmp"
TIMEOUT_SECONDS = 20


class AlexaChecker(BaseChecker):

	def __init__(self, tick, team, service, ip):
		BaseChecker.__init__(self, tick, team, service, ip)
		availableAudioFiles = [os.path.join(AUDIO_SOURCE_DIRECTORY, filename) for filename in os.listdir(AUDIO_SOURCE_DIRECTORY)]
		self._availableAudioFiles = list(filter(lambda f: f.endswith(".wav") or f.endswith(".flac"), availableAudioFiles))
		self._baseUrl = "http://{}:8000".format(ip)

	@staticmethod
	def _hideWatermark(infile, outfile, watermark):
		"""
		Hides a given watermark in the spectrogram of the given audio file
		:param infile: path to wav file
		:param outfile: path to wav file to be written
		:param watermark: text to embed
		:return:
		"""
		fs, data = wavfile.read(infile)
		# Extract first channel
		if len(data.shape) > 1:
			data = data[:, 0]

		# Normalize to amplitude [-1, 1]
		data = data.astype(np.float) / np.max(np.abs(data))
		windowLength = 1024
		nfft = windowLength
		h = windowLength // 4
		spectrogram, f, t = stft(data, windowLength, h, nfft, fs)

		# Embed text
		embedded = embed_text(spectrogram, watermark, embedding_value=5, left_top=(20, 20), font_size=80)
		# plotSpectrogram(embedded)

		# Reconstruct and save audio signal from modified spectrogram
		x, t = istft(embedded, windowLength, h, nfft, fs)
		wavfile.write(outfile, fs, x.T)

	@staticmethod
	def _md5hash(filename):
		hasher = hashlib.md5()
		with open(filename, "rb") as f:
			hasher.update(f.read())
		return hasher.hexdigest()

	@staticmethod
	def _shortenFlag(flag):
		"""
		Cut off leading FAUST_ prefix to shorten the flag string
		:param flag: flag as generated by the flag module
		:return: [flagFormatCharacters]{32}
		"""
		return re.sub("^FAUST_", "", flag)

	def check_flag(self, tick):
		yaml = self.retrieve_yaml(str(tick))
		if yaml is None:
			return NOTFOUND

		queryId = yaml["queryId"]
		uploadedFileMd5Hash = yaml["md5hash"]

		# Ask the server whether this query id still exists
		url = "{}/alexa/query/{}".format(self._baseUrl, queryId)
		try:
			response = requests.get(url, timeout=TIMEOUT_SECONDS)
		except requests.exceptions.Timeout:
			self.logger.info("Timeout while trying to retrieve audio file at {}".format(url))
			return TIMEOUT

		if 404 == response.status_code:
			self.logger.info("Could not find query at {}".format(url))
			return NOTFOUND
		elif 200 != response.status_code:
			self.logger.info("Unexpected status code {} at {}".format(response.status_code, url))
			return NOTWORKING

		# Find the audio source
		dom = html.fromstring(response.content)
		audioSourceElements = dom.xpath("//audio/source[@src]")
		if 0 == len(audioSourceElements):
			self.logger.info("Could not find audio source element with src attribute at {}".format(url))
			return NOTWORKING

		audioSourceUrl = audioSourceElements[0].attrib['src']
		audioUrlFilename = audioSourceUrl.rsplit('/', 1)[-1]

		# Access the audio source
		downloadedAudioFile = os.path.join(TMP_DIRECTORY, audioUrlFilename)
		audioUrl = self._baseUrl + audioSourceUrl
		try:
			response = requests.get(audioUrl, stream=True, timeout=TIMEOUT_SECONDS)
		except requests.exceptions.Timeout:
			self.logger.info("Timeout while trying to download audio file from {}".format(audioUrl))
			return TIMEOUT

		if not response.ok:
			self.logger.info("Could not download audio file from {}".format(audioUrl))
			return NOTWORKING

		# Download the audio source
		with open(downloadedAudioFile, "wb") as f:
			for block in response.iter_content(1024):
				f.write(block)

		# Compare hashes to check integrity
		downloadedFileMd5Hash = self._md5hash(downloadedAudioFile)
		if downloadedFileMd5Hash != uploadedFileMd5Hash:
			self.logger.info("Hash of downloaded audio file does not match hash of uploaded file")
			# Clean up
			os.remove(downloadedAudioFile)
			return NOTWORKING

		# Clean up
		os.remove(downloadedAudioFile)
		return OK

	def place_flag(self):
		# Shorten flag to make audio file smaller
		flag = AlexaChecker._shortenFlag(self.get_flag(str(self._tick)))
		audioFile = random.choice(self._availableAudioFiles)

		# Generate unique intermediate filename
		intermediatePrefix = str(uuid.uuid4()).replace("-", "")
		wavFile = os.path.join(TMP_DIRECTORY, "{}.wav".format(intermediatePrefix))
		oggFile = os.path.join(TMP_DIRECTORY, "{}.ogg".format(intermediatePrefix))

		# Embed flag in audio file
		AlexaChecker._hideWatermark(audioFile, wavFile, flag)
		# Convert to flac file
		convert_wav_to_ogg(wavFile, oggFile)
		# Delete intermediate wav file
		os.remove(wavFile)

		# Submit flac file to service
		url = "{}/alexa/query".format(self._baseUrl)
		with open(oggFile, 'rb') as f:
			files = {'audioFile': (oggFile, f, "audio/flac")}
			try:
				response = requests.post(url, files=files, timeout=TIMEOUT_SECONDS)
			except requests.exceptions.Timeout as e:
				# Timeout occurs if the speech recognition takes too long or the service does not respond
				if type(e) == requests.exceptions.ReadTimeout:
					self.logger.warn("Team {} might not have installed the hotfix".format(self._baseUrl))

				self.logger.info("Timeout while submitting audio file to {}".format(url))
				# Clean up
				os.remove(oggFile)
				return TIMEOUT
			except requests.exceptions.RequestException:
				self.logger.info("Request exception while submitting audio file to {}".format(url))
				# Clean up
				os.remove(oggFile)
				return NOTWORKING

		if response.status_code != 200:
			self.logger.info("Received status code {} after submitting audio file to {}".format(response.status_code, url))
			# Clean up
			os.remove(oggFile)
			return NOTWORKING

		# Verify response url
		if re.match("^{}/alexa/query/[a-z0-9]{{32}}$".format(self._baseUrl), response.url) is None:
			self.logger.info("Unexpected forwarding to {} after submitting audio file".format(response.url))
			# Clean up
			os.remove(oggFile)
			return NOTWORKING

		queryId = response.url.rsplit('/', 1)[-1]

		md5hash = AlexaChecker._md5hash(oggFile)
		self.store_yaml(str(self._tick), {"queryId": queryId, "md5hash": md5hash})

		# Clean up
		os.remove(oggFile)
		return OK


if __name__ == "__main__":
	tick = 1
	team = 1
	service = 1
	checker = AlexaChecker(tick, team, service, "10.66.1.2")
	placeResult = checker.place_flag()
	print("Place result: {}".format(placeResult))
	if OK == placeResult:
		checkResult = checker.check_flag(tick)
		print("Check result: {}".format(checkResult))