from setuptools import setup, find_packages

setup(name='spectrogram',
	  version='0.1',
	  description='Text embedding in short-time Fourier transformed audio signal',
	  url='http://gitlab.cs.fau.de/yr03yzut',
	  author='Benedikt Lorch',
	  author_email='benedikt.lorch@fau.de',
	  license='MIT',
	  packages=find_packages(),
	  package_data={'': ['*.ttf']},
	  install_requires=[
		  'scipy',
		  'numpy',
		  'matplotlib',
		  'Pillow',
		  'pydub',
		  'pytesseract',
		  'requests'
	  ],
	  zip_safe=False)
