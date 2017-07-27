from pydub import AudioSegment
import os


def convert_to_wav(audio_file):
	"""
	Converts the given audio file to a wav file stored in /tmp
	:param audio_file: wav or flac audio file
	:return: path to wav file in /tmp directory
	"""
	basename, ext = os.path.splitext(os.path.basename(audio_file))
	temp_file = "/tmp/{}.wav".format(basename)
	if ext == ".wav":
		return audio_file
	elif ext == ".flac":
		audio_segment = AudioSegment.from_file(audio_file, "flac")
		audio_segment.export(temp_file, "wav")
		return temp_file
	elif ext == ".ogg":
		audio_segment = AudioSegment.from_ogg(audio_file)
		audio_segment.export(temp_file, "wav")
		return temp_file
	else:
		raise ValueError("Unknown file format")


def convert_wav_to_flac(wav_file, flac_file):
	wav = AudioSegment.from_wav(wav_file)
	wav.export(flac_file, format="flac")


def convert_wav_to_ogg(wav_file, ogg_file):
	wav = AudioSegment.from_wav(wav_file)
	wav.export(ogg_file, format="ogg", codec="libvorbis", bitrate="140k")
