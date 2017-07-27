# Copyright (c) 2017, Hristo Zhivomirov
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:

# * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in
# the documentation and/or other materials provided with the distribution

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Implementation based on https://uk.mathworks.com/matlabcentral/fileexchange/45197-short-time-fourier-transformation--stft--with-matlab-implementation

import math

import numpy as np
from scipy.signal import hamming


def stft(x, window_length, h, nfft, fs):
	"""
	Computes the short time fourier transform of a given signal
	:param x: signal in time domain
	:param window_length: length of the hamming window
	:param h: hop size
	:param nfft: number of FFT points
	:param fs: sampling frequency in Hz
	:return: (stft, f, t) where
		STFT matrix, time across columns, frequency coefficients across rows
		f frequency vector in Hz
		t time vector in seconds
	"""

	signal_length = len(x)

	# Create a periodic hamming window
	window = hamming(window_length, sym=False)

	# Form the STFT matrix
	num_rows = math.ceil((1.0 + nfft) / 2.0)
	num_cols = 1 + int((signal_length - window_length) / float(h))
	stft = np.zeros((num_rows, num_cols), dtype=np.complex)

	idx = 0
	col = 0

	while idx + window_length < signal_length:
		# Windowing
		signal_window = x[idx:idx + window_length] * window

		# FFT
		signal_window_ft = np.fft.fft(signal_window, nfft)

		# Update STFT matrix
		stft[:, col] = signal_window_ft[0:num_rows]

		# Update indices
		idx = idx + h
		col += 1

	# Calculate time and frequency vectors
	t = np.arange(window_length / 2, window_length / 2 + num_cols * h, step=h) / fs
	f = np.arange(num_rows) * fs / nfft
	return stft, f, t


def istft(stft, window_length, h, nfft, fs):
	"""
	Computes the inverse short term Fourier transform of the given signal
	:param stft: STFT matrix
	:param window_length: length of the hamming window
	:param h: hop size
	:param nfft: number of FFT points
	:param fs: sampling frequency in Hz
	:return: (x, t) where x is the signal in time domain and t the time vector in seconds
	"""

	# Estimate the length of the signal
	num_cols = stft.shape[1]
	signal_length = nfft + (num_cols - 1) * h
	x = np.zeros((1, signal_length))

	# Form a periodic hamming window
	window = hamming(window_length, sym=False)

	# Perform IFFT and weighted OLA
	if nfft % 2 == 1:
		# Odd nfft excludes Nyquist point
		for b in np.arange(0, h * num_cols, step=h):
			# Extract FFT points
			X = stft[:, b//h]
			X = np.hstack((X, np.conj(X[1::-1])))

			# IFFT
			xprim = np.real(np.fft.ifft(X))

			# Weighted OLA
			x[b:b+nfft] += xprim * window
	else:
		# Even nfft includes Nyquist point
		for b in np.arange(0, h * num_cols, step=h):
			# Extract FFT points
			X = stft[:, b//h]
			X = np.hstack((X, np.conj(X[::-1][1:-1])))

			# IFFT
			xprim = np.real(np.fft.ifft(X))

			# Weighted OLA
			x[:, b:b+nfft] += xprim * window

	# Find W0
	W0 = np.sum(np.square(window))
	# Scale the weighted OLA
	x *= h / W0

	# Calculate the time vector
	# Find actual length of the signal
	actual_signal_length = x.shape[1]
	# Generate time vector
	t = np.array(range(actual_signal_length)) / fs
	return x, t


def plot_spectrogram(stft):
	"""
	Displays the spectrogram from the given stft matrix
	:param stft: matrix with columns across time steps and rows across frequencies
	:return: None
	"""
	import matplotlib.pyplot as plt
	from matplotlib.colors import LogNorm

	fig = plt.figure()
	ax = plt.gca()
	im = ax.matshow(np.abs(stft), cmap=plt.get_cmap('plasma'), norm=LogNorm(vmin=0.01, vmax=1), origin='lower')
	fig.colorbar(im)
	#plt.imshow(np.log(np.abs(stft) + 1), origin='lower')
	plt.title("Spectrogram")
	plt.show()
