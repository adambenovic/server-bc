"""
Pylint parser
"""
from __future__ import print_function
from Layout import HCPolygons

import sys
import os

import ast

import json

from pylint.pyreverse.inspector import Linker, project_from_files
from pylint.pyreverse.diadefslib import DiadefsHandler
from pylint.pyreverse.main import Run
from pylint.pyreverse.utils import insert_default_options
from pylint.pyreverse import writer

from radon.raw import analyze
from radon.complexity import cc_visit_ast
from radon.metrics import h_visit_ast, mi_compute

from operator import itemgetter

class Diagram(object):
	"""Diagram wrapper base class"""

	def __init__(self, diadef):
		self._diadef = diadef
		self._glob = {}
		self._dict = self.buildDictionary(diadef)
		return
	
	@property
	def Dictionary(self):
		return self._dict
		
	def buildDictionary(self, diadef):
		raise NotImplementedError("Please Implement this method")
		
	def relationships(self, diadef):
		return [{
			"from": rel.from_object.node.qname(),
			"to": rel.to_object.node.qname(),
			"type": rel.type 
		} for typeRels in diadef.relationships.values() for rel in typeRels]

class PackageDiagram(Diagram):

	def __init__(self, diadef, classes=None):
		if classes is not None:
			diadef.objects.extend(classes)
			diadef.extract_relationships()
		for obj in diadef.modules():
			nsplit = obj.node.name.split(".")
			if len(nsplit) > 1:
				try:
					submodule = diadef.module(".".join(nsplit[:-1]))
				except KeyError:
					continue
				diadef.add_relationship(obj, submodule, 'contains')
		super(PackageDiagram, self).__init__(diadef)
		return

	def buildDictionary(self, diadef):
		return {
			"modules": self.modulesDictionary(diadef),
			"relationships": self.relationships(diadef), #ownership, depends
			"fileMap": self.fileMapping(diadef)
		}
		
	def modulesDictionary(self, diadef):
		modules = {module.node.qname(): {
			"name":module.node.name,
			"type": module.shape, #class, interface
			"classes": []
		} for module in diadef.modules()}
		if("ownership" in diadef.relationships):
			for rel in diadef.relationships["ownership"]:
				modules[rel.to_object.node.qname()]["classes"].append(rel.from_object.node.qname())
		return modules
	
	def fileMapping(self, diadef):
		mapping = {}
		for obj in diadef.modules():
			node = obj.node
			filePath = node.root().file.lower()
			if (filePath not in mapping):
				mapping[filePath] = []
			mapping[filePath].append({
				'qname': node.qname(),
				'fromLineNo': node.fromlineno,
				'toLineNo': node.tolineno
			})
			mapping[filePath].sort(key=lambda it: it['fromLineNo'])
		return mapping
	
class ClassDiagram(Diagram):
	"""Class diagram wrapper"""

	def buildDictionary(self, diadef):
		return {
			"classes": self.classesDictionary(diadef),
			"relationships": self.relationships(diadef), #specialization, implements, association
			"globals": self._glob,
			"fileMap": self.fileMapping(diadef)
		}
	
	def classesDictionary(self, diadef):
		return {clss.node.qname(): {
			"methods": self.methodsDictionary(clss),
			"attributes":self.attributesDictionary(clss),
			"name":clss.node.name,
			"type": clss.shape #class, interface
		} for clss in diadef.classes()}

	def methodsDictionary(self, clss):
		return {
			method.name: {
				"metrics": self.calculateMetrics(method),
				"argnames": method.argnames()
			} for method in clss.methods}

	def attributesDictionary(self, clss):
		return {attribute: {} for attribute in clss.attrs}

	def calculateMetrics(self, method):
		code = method.scope().as_string()
		parseCode = "from __future__ import print_function\n" + code if 'print_function' in method.root().future_imports else code
		tree = ast.parse(parseCode, method.root().file)
		rm = analyze(code)
		ccm = cc_visit_ast(tree)[0]
		hm = h_visit_ast(tree)
		mi = mi_compute(hm.volume, ccm.complexity, rm.sloc, rm.single_comments)
		metrics = {
			"lloc": rm.lloc,
			"sloc": rm.sloc,
			"loc": rm.loc,
			"comments": rm.comments,
			"multi": rm.multi,
			"blank": rm.blank,
			"cc": ccm.complexity,
			"mi": mi
		}
		#update globals
		gmetrics = self._glob.get("metrics")
		if (gmetrics is None):
			gmetrics = self._glob["metrics"] = {k: {"max": v, "min": v} for k, v in metrics.iteritems()}
		else:
			for key, value in metrics.iteritems():
				gmetrics[key]["max"] = max(gmetrics[key]["max"], value)
				gmetrics[key]["min"] = min(gmetrics[key]["min"], value)
		return metrics

	def fileMapping(self, diadef):
		mapping = {}
		for obj in diadef.classes():
			node = obj.node
			filePath = node.root().file.lower()
			if (filePath not in mapping):
				mapping[filePath] = []
			mapping[filePath].append({
				'qname': node.qname(),
				'fromLineNo': node.fromlineno,
				'toLineNo': node.tolineno,
				'methods': sorted([{
					'qname': m.qname(),
					'fromLineNo': m.fromlineno,
					'toLineNo': m.tolineno
				} for m in diadef.get_methods(node)], key=lambda it: it['fromLineNo'])
			})
			mapping[filePath].sort(key=lambda it: it['fromLineNo'])
		return mapping

class City(ClassDiagram):

	def __init__(self, diadef):
		self.attrClsSize = 1
		self.metricId = "lloc"
		super(City, self).__init__(diadef)
		return	

	def classesDictionary(self, clss):
		classes = super(City, self).classesDictionary(clss)
		hcp = HCPolygons(self._hilbertSize(classes))
		offset = 0
		for cVal in classes.values():			
			polygons = []
			methods = cVal["methods"]
			if len(methods) == 0 and self.attrClsSize > 0:
				polygons.append(("NO-METHOD", hcp.buildPolygon(self.attrClsSize, offset)))
				offset += self.attrClsSize
			else:
				sortedMethods = sorted(((mKey, mVal["metrics"][self.metricId]) for mKey, mVal in methods.iteritems()), key=itemgetter(1), reverse=True)
				for mKey, metric in sortedMethods:
					polygons.append((mKey, hcp.buildPolygon(metric, offset)))
				offset += sortedMethods[0][1]
			cVal["polygons"] = polygons
		return classes
		
	def _hilbertSize(self, classes):
		total = 0
		for cKey, cVal in classes.iteritems():
			methods = cVal["methods"]
			total += max(mVal["metrics"][self.metricId] for mKey, mVal in methods.iteritems()) if len(methods) > 0 else self.attrClsSize
		return total

class PyreverseRun(Run):
	"""Overrided class for pyReverse Run"""

	def __init__(self, paths, syspaths):
		#pyreverse heavily depends on sys argv and in init they call sys.exit... so wow... never see such shitty code
		args = ['-o', 'png']
		sys.argv = sys.argv[:1]
		sys.argv.extend(args)
		sys.argv.extend(paths)
		super(Run, self).__init__(usage=__doc__)
		self.load_command_line_configuration()
		self._args = paths
		self._project, self._linker, self._handler, self._diadefs = self.run(syspaths)
		return

	@property
	def Diadefs(self):
		return self._diadefs

	def run(self, syspaths):
		"""checking arguments and run project"""
		sys.path = syspaths + sys.path
		try:
			project = project_from_files(self._args, project_name=self.config.project,
											black_list=self.config.black_list)
			linker = Linker(project, tag=True)
			handler = DiadefsHandler(self.config)
			diadefs = handler.get_diadefs(project, linker)
		finally:
			sys.path = sys.path[len(syspaths):]
		return project, linker, handler, diadefs

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('--sys-paths', nargs='+', help="syspaths to use")
	parser.add_argument('--paths', nargs='+', help="paths to analyze")
	parser.add_argument('-o', help="save json to file")
	parser.add_argument('-l', action='store_true', help="log json to stdout")
	args = parser.parse_args()
	
	paths = args.paths or []
	syspaths = args.sys_paths or []
	
	prr = PyreverseRun(paths, syspaths)
	diadefs = prr.Diadefs
	writer.DotWriter(prr.config).write(diadefs)

	pdd, cdd = diadefs
	cd = ClassDiagram(cdd)
	pd = PackageDiagram(pdd, cdd.classes())
	
	if args.l:
		print(json.dumps(cd.Dictionary, indent=4))

	if args.o:
		with open(args.o, "w") as out:
			json.dump(cd.Dictionary, out, indent=4)

