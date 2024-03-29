###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Crossbar.io Technologies GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

from autobahn.twisted.websocket import WebSocketClientProtocol, \
	WebSocketClientFactory
import time
import json

class MyClientProtocol(WebSocketClientProtocol):

	def test(self):
		data = {
			"action": "subscribe",
			"args": {
				"events": ["generateDiagram"]
			}
		}
		self.sendMessage(json.dumps(data).encode('utf8'))
		data = {
			"action": "generateDiagram",
			"args": {
				"type": "package",
				"fsPaths": [r"C:\Python27\Lib\site-packages\django\contrib\gis\gdal"],
				"sysPaths": [r"C:\Python27\Lib\site-packages"]
			}
		}
		self.sendMessage(json.dumps(data).encode('utf8'))
		self.sendMessage(json.dumps({"action":"echo"}).encode('utf8'))
		return

	def onConnect(self, response):
		print("Server connected: {0}".format(response.peer))

	def onOpen(self):
		print("WebSocket connection open.")
		self.test()

	def onMessage(self, payload, isBinary):
		if isBinary:
			print("Binary message received: {0} bytes".format(len(payload)))
		else:
			print("Text message received: {0}".format(payload.decode('utf8')))

	def onClose(self, wasClean, code, reason):
		print("WebSocket connection closed: {0}".format(reason))


if __name__ == '__main__':

	import sys

	from twisted.python import log
	from twisted.internet import reactor

	log.startLogging(sys.stdout)

	factory = WebSocketClientFactory(u"ws://127.0.0.1:9000")
	factory.protocol = MyClientProtocol

	reactor.connectTCP("127.0.0.1", 9000, factory)
	reactor.run()
