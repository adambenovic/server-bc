from scurve.hilbert import Hilbert
import numpy as np
from sets import Set
import math

class HCPolygons(object):

	def __init__(self, total):
		dimension = 2
		order = int(math.ceil(math.log(total, 2) / dimension))
		self.hilbert = Hilbert(dimension, order)
		self.placed = 0
		return
		
	def buildPolygon(self, size, start=None):
		mapSet = Set()
		if start is not None:
			self.placed = start
		for i in xrange(size):
			x,y = self.hilbert.point(self.placed + i)
			x = x * 5 + 1
			y = y * 5 + 1
			mapSet |= Helpers.wrap(x, y, 2)
		mapSet = Helpers.erode(mapSet)
		filtered = Set()
		for x,y in mapSet:
			if not Helpers.neighCheck(x,y,mapSet):
				continue
			filtered.add((x,y))
		#sort floor coords to form path and simplify
		blocks = [(x,y) for x,y in Helpers.orderBlocks(filtered.copy()) if not Helpers.lineCheck(x,y,filtered)]
		self.placed += size
		return blocks

class Helpers(object):

	@classmethod
	def orderBlocks(cls, blocks):
		first = current = blocks.pop()
		ordered = [first]
		prev = None
		while(blocks):
			test = ((0,1), (1,0), (0,-1), (-1,0))
			for ax, ay in test:
				toCheck = (current[0]+ax, current[1]+ay)
				if( toCheck != prev and toCheck in blocks):
					ordered.append(toCheck)
					blocks.remove(toCheck)
					prev = current
					current = toCheck
					break
		return ordered
		
	@classmethod
	def wrap(cls, x, y, level):
		wrapped = Set()
		toAdd = range(-level, level+1)
		for a1 in toAdd:
			for a2 in toAdd:
				wrapped.add((x+a1, y+a2))
		return wrapped
		
	@classmethod
	def lineCheck(cls, x, y, map):
		toCheck = (
			(x-1,y) in map and (x+1,y) in map,
			(x,y-1) in map and (x,y+1) in map
		)
		return any(toCheck)
		
	@classmethod
	def neighCheck(cls, x, y, map):
		toCheck = (
			(x-1,y+1 ) not in map,
			(x,y+1 ) not in map,
			(x+1,y+1 ) not in map,
			(x+1,y ) not in map,
			(x+1,y-1 ) not in map,
			(x,y-1 ) not in map,
			(x-1,y-1 ) not in map,
			(x-1,y ) not in map
		)
		return any(toCheck)
	
	@classmethod
	def erode(cls, map):
		eroded = map.copy()
		for x, y in map:
			if cls.neighCheck(x,y, map):
				eroded.remove((x,y))
		return eroded

def showTestPoints(points):
	hcp = HCPolygons(len(points))
	d = hcp.hilbert.dimensions()
	d = hcp.hilbert.dimensions()
	a = np.zeros(np.array(d) * 5 - 2)
	for p in points:
		a[p] = 1
	plt.imshow(a)
	plt.show()
	return

if __name__=="__main__":
	hcp = HCPolygons(64)
	
	d = hcp.hilbert.dimensions()
	a = np.zeros(np.array(d) * 5 - 2)
	
	points = hcp.buildPolygon(32)
	for p in points:
		a[p] = 1
	
	points = hcp.buildPolygon(9, 43)
	for p in points:
		a[p] = 3
		
	points = hcp.buildPolygon(12)
	for p in points:
		a[p] = 4
	
	import matplotlib.pyplot as plt
	plt.imshow(a)
	plt.show()
