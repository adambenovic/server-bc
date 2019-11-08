from Parser.PylintParser import PyreverseRun, ClassDiagram
from TCP.TCPHandler import TCPSender, TCPListener
import json

class DiagramHandler(object):

    def __init__(self):
        #build dict to handle goto definition etc
        return

    def onGoToInEditor(self):
        #qname as input
        return

    def onGoToInDiagram(self):
        #line no as input
        return

    def onGenClsDia(self, action, payload):
        paths = [payload["fsPath"], ]
        syspaths = [payload["rootPath"], ]
        print("paths:", paths, "syspaths:", syspaths)
        
        prr = PyreverseRun(paths, syspaths)
        diadefs = prr.Diadefs
        cd = ClassDiagram(diadefs[-1])
        respond = {
            "action":action,
            "payload": cd.Dictionary
        }

        TCPSender().send(json.dumps(respond) + "\n")
        return

    def onData(self, data):
        parsed = json.loads(data)
        action = parsed["action"]
        payload = parsed["payload"]

        if(action == "G_CLS_DIA"):
            self.onGenClsDia(action, payload)
        return

if __name__=="__main__":
    listener = TCPListener()
    handler = DiagramHandler()
    listener.run(handler.onData)