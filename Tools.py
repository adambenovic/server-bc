import numpy as np
import wordcloud
import os
import base64
import cStringIO
import keyword

from os import path
from PIL import Image

class WordCloud(object):
	
	def __init__(self):
		#TODO args
		dir = path.dirname(__file__)
		mode = 'RGBA'		
		background_color = None
		max_words = 20
		min_font_size = 64
		self.mask = Image.open(path.join(dir, "Masks", "cloud.png"))
		np_mask = np.array(self.mask)
		stopwords = set(wordcloud.STOPWORDS).union(set(keyword.kwlist)).union(set(["self", "None", "True", "False"]))
		self.wc = wordcloud.WordCloud(background_color=background_color, max_words=max_words, mask=np_mask, stopwords=stopwords, mode=mode, min_font_size=min_font_size)
		return
		
	def base64Cloud(self, text):
		self.wc.generate(text)
		image = Image.alpha_composite(self.mask, self.wc.to_image())
		buffer = cStringIO.StringIO()
		image.save(buffer, format="png")
		return base64.b64encode(buffer.getvalue())
