from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import numpy as np
import os


def embed_text(mat, text, embedding_value, left_top=(50, 0), font_size=80):
	font_family = os.path.join(os.path.dirname(os.path.abspath(__file__)), "UbuntuMono-R.ttf")
	height, width = mat.shape
	image = Image.new("L", (width, height), 0)
	# image.show()
	draw = ImageDraw.Draw(image)
	font = ImageFont.truetype(font_family, font_size)

	# (left, top)
	draw.text(left_top, text, 1, font)
	arr = np.flipud(np.array(image))

	rasterized_text_mask = np.where(arr > 0)
	mat[rasterized_text_mask[0], rasterized_text_mask[1]] = embedding_value
	return mat


if __name__ == "__main__":
	mat = np.ones((100, 600))
	mat = embed_text(mat, "Hallo Welt", 10, font_size=20)
	plt.imshow(mat, interpolation='none', origin='lower', cmap=plt.cm.get_cmap('gray'))
	plt.tight_layout()
	plt.savefig("hallowelt.png")
	plt.show()
