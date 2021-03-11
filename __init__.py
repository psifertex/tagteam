#!/usr/bin/env python
# -*- coding: utf-8 -*
from binaryninja import PluginCommand, Settings, interaction, log_info, HighLevelILOperation

Settings().register_group("tagteam", "Tag Team Plugin")
Settings().register_setting("tagteam.largeFunc", """
	{
		"title" : "Number of basic blocks",
		"type" : "number",
		"default" : 40,
		"description" : "Functions with more than this number of basic blocks will be considered large"
	}
	""")

Settings().register_setting("tagteam.largeSwitch", """
	{
		"title" : "Large Switch Statement",
		"type" : "number",
		"default" : 10,
		"description" : "Functions with switch statements with more than this many cases are considered switchy"
	}
	""")

Settings().register_setting("tagteam.complexFunc", """
	{
		"title" : "Complex Function",
		"type" : "number",
		"default" : 40,
		"description" : "Functions with cyclomatic complexity scores above this will be considered complex"
	}
	""")

def init_tags(bv):
	for tagType in tags:
		if tagType['name'] not in bv.tag_types.keys():
			bv.create_tag_type(tagType['name'], tagType['emoji'])

def cc(fn):
	nodes = len(fn.basic_blocks)
	edges = sum(len(x.outgoing_edges) for x in fn.basic_blocks)
	connected = 1 #always 1 for binary control flow graphs, kinda the whole point
	return edges - nodes + 2 * connected

def isswitchy(fn):
	for h in fn.hlil.instructions:
		if h.operation == HighLevelILOperation.HLIL_SWITCH:
			if len(h.cases) > Settings().get_integer("tagteam.largeSwitch"):
				return True
	return False

def iscomplex(fn):
	return cc(fn) > Settings().get_integer("tagteam.complexFunc")

def isleaf(fn):
	return len(fn.callees) == 0

def islarge(fn):
	return len(fn.basic_blocks) >= Settings().get_integer("tagteam.largeFunc")

def isstub(fn):
	"""Returns true if a function is likely only a stub"""
	if len(fn.basic_blocks) > 1 or len(fn.llil.basic_blocks) > 1:
		return False
	if fn.llil.basic_blocks[0].has_undetermined_outgoing_edges or len(fn.callees) == 1:
		return True
	return False

def hasloop(fn):
	"""Returns true if a function has a 'strange loop' (ignore this, inside joke)"""
	for bb in fn.basic_blocks:
		if bb in bb.dominance_frontier:
			return True
	return False

tags = [ \
{'emoji': '🍃', 'name': 'Leaf Function', 'description': 'Leaf function (does not call anything else)', 'fn': isleaf},
{'emoji': '🔄', 'name': 'Loop Function', 'description': 'Function contains a loop', 'fn': hasloop},
{'emoji': '🥾', 'name': 'Stub Function', 'description': 'Function is likely a stub (only contains one basic block and one call or indirect jump)', 'fn': isstub},
{'emoji': '🐘', 'name': 'Large Function', 'description': 'Function is "large" (IE, it has more than the blocks defined above)', 'fn': islarge},
{'emoji': '🤯', 'name': 'Complex Function', 'description': 'Function is "complex" (IE, it has a cyclomatic complexity greater than a defined constant)', 'fn': iscomplex},
{'emoji': '🌴', 'name': 'Switchy Function', 'description': 'Function contains a large switch statemen', 'fn': isswitchy},
]

def start(bv):
	init_tags(bv)
	for fn in bv.functions:
		for tagType in tags:
			if tagType['fn'](fn):
				fn.create_user_function_tag(bv.tag_types[tagType['name']], '', unique=True)
				#fn.name = fn.name + tagType['emoji']

PluginCommand.register("TagTeam", "Tag Functions with Emoji for Various Properties", start)
