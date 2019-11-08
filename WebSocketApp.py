from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
from twisted.internet import threads
from Parser import PylintParser
from Tools import WordCloud
import json

from collections import defaultdict
from sets import Set

class Helpers(object):
	
	encoding = 'utf8'
	
	@staticmethod
	def jsonMessage(data):
		return Helpers.encode(json.dumps(data))
		
	@staticmethod
	def encode(data):
		return data.encode(Helpers.encoding)
		
	@staticmethod
	def decode(data):
		return data.decode(Helpers.encoding)
	
class DiagramTools(object):
	
	@staticmethod
	def createClassDiagram(paths, syspaths):
		prr = PylintParser.PyreverseRun(paths, syspaths)
		diadefs = prr.Diadefs
		cd = PylintParser.ClassDiagram(diadefs[-1])
		return cd.Dictionary
		
	@staticmethod
	def createPackageDiagram(paths, syspaths):
		prr = PylintParser.PyreverseRun(paths, syspaths)
		diadefs = prr.Diadefs
		pd = PylintParser.PackageDiagram(diadefs[0], diadefs[1].classes())
		return pd.Dictionary
		
class DiagramServerFactory(WebSocketServerFactory):

	def __init__(self, url):
		super(DiagramServerFactory, self).__init__(url)
		self.subscriptions = defaultdict(Set)
		return

	def subscribe(self, client, actions):
		for action in actions:
			self.subscriptions[action].add(client)
			print ("Subscribed", client.peer, "to", action)
		return

	def unsubscribe(self, client, actions=None):
		if actions is None:
			actions = self.subscriptions.keys()
		for action in actions:
			self.subscriptions[action].remove(client)
			print ("Unsubscribed", client.peer, "from", action)
		return

	def publish(self, action, msg):
		for client in self.subscriptions[action]:
			client.sendMessage(Helpers.encode(msg))
			# print ("Publishing - client:", client.peer, "action:", action)
		return

class DiagramServerProtocol(WebSocketServerProtocol):

	def onConnect(self, request):
		print("Client connecting: {0}".format(request.peer))

	def onOpen(self):
		print("WebSocket connection open.")

	def onMessage(self, payload, isBinary):
		if not isBinary:
			print(payload)
			data = json.loads(Helpers.decode(payload))
			action = data["action"]
			if(action == "generateDiagram"):
				d = threads.deferToThread(self.onGenerateDiagram, data)
				d.addCallback(self.publishResult)
			elif(action == "ideAction"):
				self.sendResponse(data)
				self.publishResult(data)
			elif(action == "xdeAction"):
				self.sendResponse(data)
				self.publishResult(data)
			elif(action == "subscribe"):
				self.onSubscribe(data)
			elif(action == "unsubscribe"):
				self.onUnsubscribe(data)
			elif(action == "echo"):
				self.sendMessage("echo")
			elif(action == "generateWordCloud"):
				d = threads.deferToThread(self.onGenerateWordCloud, data)
				d.addCallback(self.publishResult)
			elif(action == "generateCity"):
				d = threads.deferToThread(self.onGenerateCity, data)
				d.addCallback(self.publishResult)
		return
		
	def onSubscribe(self, data):
		events = data.get("args", {}).get("events")
		#TODO if None raise data error
		self.factory.subscribe(self, events)
		return
		
	def onUnsubscribe(self, data):
		events = data.get("args", {}).get("events")
		self.factory.unsubscribe(self, events)
		return
		
	def onGenerateDiagram(self, data):
		args = data.get("args", {})
		type = args.get("type")
		fsPaths = args.get("fsPaths")
		sysPaths = args.get("sysPaths")
		#TODO if None raise data error
		if(type == "class"):
			cd = DiagramTools.createClassDiagram(fsPaths, sysPaths)
			args["data"] = cd
		elif(type == "package"):
			pd = DiagramTools.createPackageDiagram(fsPaths, sysPaths)
			args["data"] = pd
		return data
		
	def onGenerateCity(self, data):
		args = data.get("args", {})
		fsPaths = args.get("fsPaths")
		sysPaths = args.get("sysPaths")
		prr = PylintParser.PyreverseRun(fsPaths, sysPaths)
		diadefs = prr.Diadefs
		ci = PylintParser.City(diadefs[-1])
		args["data"] = ci.Dictionary
		return data
		
	def onGenerateWordCloud(self, data):
		wc = WordCloud()
		args = data.get("args", {})
		fsPath = args.get("fsPath")
		lineFrom = args.get("fromLineNo")
		lineTo = args.get("toLineNo")
		with open(fsPath) as f:
			text = "".join(f.readlines()[slice(lineFrom, lineTo)])
			args["data"] = wc.base64Cloud(text)
		return data
		
	def sendResponse(self, data):
		response = {
			"action":data["action"],
			"args": {
				"status":"ok"
			}
		}
		self.sendMessage(Helpers.jsonMessage(response))
		return
		
	def publishResult(self, data):
		self.factory.publish(data["action"], Helpers.jsonMessage(data))
		return

	def onClose(self, wasClean, code, reason):
		self.factory.unsubscribe(self)
		print("WebSocket connection closed: {0}".format(reason))


if __name__ == '__main__':

	import sys

	from twisted.python import log
	from twisted.internet import reactor

	log.startLogging(sys.stdout)

	factory = DiagramServerFactory(u"ws://127.0.0.1:9000")
	factory.protocol = DiagramServerProtocol
	# factory.setProtocolOptions(maxConnections=2)
	reactor.listenTCP(9000, factory)
	reactor.run()
