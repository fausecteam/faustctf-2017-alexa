import os
import random
import string

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.io import wavfile
from scipy.ndimage.morphology import grey_closing, grey_erosion

from ..stft import stft, istft, plot_spectrogram
from .audioutils import convert_to_wav
from .embedding import embed_text
from .ocr import ocr_space


def hide_watermark(infile, outfile, watermark):
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
	window_length = 1024
	nfft = window_length
	h = window_length // 4
	spectrogram, f, t = stft(data, window_length, h, nfft, fs)

	# Embed text
	embedded = embed_text(spectrogram, watermark, embedding_value=5, left_top=(20, 20), font_size=80)
	# plotSpectrogram(embedded)

	# Reconstruct and save audio signal from modified spectrogram
	x, t = istft(embedded, window_length, h, nfft, fs)
	wavfile.write(outfile, fs, x.T)


def extract_watermark(audio_file, interactive=False):
	"""
	Extracts the watermark from the spectrogram of the given audio file
	:param audio_file: path to wav file
	:param interactive: activates plotting 
	:return: watermark as text, or None if the watermark could not be extracted
	"""

	# Convert audio file to wav if necessary
	wavFile = convert_to_wav(audio_file)

	fs, data = wavfile.read(wavFile)
	data = data.astype(np.float) / np.max(np.abs(data))
	window_length = 1024
	nfft = window_length
	h = window_length // 4
	spectrogram, f, t = stft(data, window_length, h, nfft, fs)
	if interactive:
		plot_spectrogram(spectrogram)

	# Convert to PIL image in order to use optical character recognition
	# Flip upside down due to the usual way in which we view a spectrogram
	ocr_image = np.flipud(np.abs(spectrogram))

	# Do some image enhancement
	ocr_image[ocr_image < 0.2] = 0
	ocr_image = grey_closing(ocr_image, (5, 2))
	ocr_image = grey_erosion(ocr_image, (3, 5))

	# Convert to 8 bit image
	ocr_image = np.uint8(ocr_image / np.max(ocr_image) * 255 * 10)[20:120, :]
	ocr_image[ocr_image > 5] = 255

	# Enlarge image by interpolation
	# ocr_image = imresize(ocr_image, (ocr_image.shape[0] * 8, ocr_image.shape[1] * 8), interp="bilinear")

	if interactive:
		# Show for debugging purposes
		plt.imshow(ocr_image)
		plt.show()

	ocr_image = Image.fromarray(ocr_image)
	ocr_image_filename = "test.png"
	ocr_image.save(ocr_image_filename, format="png")

	# watermark = ocr.tesseract(ocr_image)
	watermark = ocr_space(ocr_image_filename)
	# ocr_image.save("test.png", format="png")
	return watermark


def _generate_flag(seed=45684651):
	random.seed(seed)
	#return 'FAUST_' + ''.join([random.choice(string.ascii_letters + string.digits + "\\" + "+") for _ in range(32)])
	return ''.join([random.choice(string.ascii_letters + string.digits + "\\" + "+") for _ in range(32)])


if __name__ == "__main__":
	from pydub import AudioSegment
	flag = _generate_flag()

	hide_watermark("audio/smoke_weed_everyday_song.wav", "flag.wav", flag)
	wav = AudioSegment.from_wav("flag.wav")
	wav.export("flag.flac", format="flac")
	wav.export("flag.ogg", format="ogg", codec="libvorbis", bitrate="140k")
	os.remove("flag.wav")

	ogg = AudioSegment.from_ogg("flag.ogg")
	ogg.export("flag.wav", format="wav")
	watermark = extract_watermark("flag.wav", interactive=True)

	print("Generated\t{}".format(flag))
	print("Extracted\t{}".format(watermark))
