from flask import Flask
from flask_restful import Api, Resource, reqparse
from flask_executor import Executor

from Parser import PylintParser

app = Flask(__name__)
api = Api(app)
executor = Executor(app)

COUNTER = {
	'cd': 0
}

class Queue(Resource):
	def get(self, id):
		if executor.futures.done(id) == False:
			return {'status':'pending'}, 303
		elif executor.futures.done(id) == None:
			return "Task {0} not found".format(id), 404
		future = executor.futures.pop(id)
		return {'status': 'done', 'result': future.result()}, 200

class ClassDiagram(Resource):

	def __init__(self):
		super(ClassDiagram, self).__init__()
		return
	
	def parse(self, paths, syspaths):
		prr = PylintParser.PyreverseRun(paths, syspaths)
		diadefs = prr.Diadefs
		cd = PylintParser.ClassDiagram(diadefs[-1])
		return cd.Dictionary
	
	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument("fsPaths", required=True, action="append")
		parser.add_argument("rootPaths", required=True, action="append")
		args = parser.parse_args()
		COUNTER['cd'] += 1
		executor.submit_stored(COUNTER['cd'], self.parse, args["fsPaths"], args["rootPaths"])
		return {'status':'queued'}, 202, {'location': "/queue/{0}".format(COUNTER['cd'])}
	  
if __name__=="__main__":
	api.add_resource(Queue, "/queue/<int:id>")
	api.add_resource(ClassDiagram, "/diagram/class")

	app.run(debug=True)