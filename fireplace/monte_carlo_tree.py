"""
A minimal implementation of Monte Carlo tree search (MCTS) in Python 3
Luke Harold Miles, July 2019, Public Domain Dedication
See also https://en.wikipedia.org/wiki/Monte_Carlo_tree_search
https://gist.github.com/qpwo/c538c6f73727e254fdc7fab81024f6e1
"""
import copy
from abc import ABC, abstractmethod
from collections import defaultdict
import math


class MCTS:
	"Monte Carlo tree searcher. First rollout the tree then choose a move."

	def __init__(self, exploration_weight):
		self.Q = defaultdict(int)  # total reward of each node
		self.N = defaultdict(int)  # total visit count for each node
		self.children = dict()  # children of each node
		self.exploration_weight = exploration_weight

	def reset(self):
		self.Q = defaultdict(int)
		self.N = defaultdict(int)
		self.children = dict()

	def choose(self, node): # works?
		"Choose the best successor of node. (Choose a move in the game)"
		if node.is_terminal():
			raise RuntimeError("choose called on terminal node {node}")

		if node not in self.children:
			return node.find_random_child()

		def score(n): # works?
			if self.N[n] < 5:
				return float("-inf")  # avoid moves with too small simulations
			return self.Q[n] / self.N[n]  # average reward

		result = max(self.children[node], key=score)
		return result

	def do_rollout(self, node): # has func calls that dont work
		"Make the tree one layer better. (Train for one iteration.)"
		#node_copy = copy.deepcopy(node) # remove this maybe, unnecessary
		path = self._select(node)
		leaf = path[-1]
		self._expand(leaf)
		reward = self._simulate(leaf)
		self._backpropagate(path, reward)

	def _select(self, node):
		"Find an unexplored descendent of `node`"
		path = []
		while True:
			path.append(node)
			if node not in self.children or not self.children[node]:
				# node is either unexplored or terminal
				return path
			unexplored = self.children[node] - self.children.keys()

			#unexplored = []
			#for child_of_game in self.children[node]:
			#	if(child_of_game not in self.children):
			#		unexplored.append(child_of_game)
			if unexplored:
				n = unexplored.pop()
				path.append(n)
				return path
			node = self._uct_select(node)  # descend a layer deeper

	def _expand(self, node):
		"Update the `children` dict with the children of `node`"
		if node in self.children: #mogoc je problem tu
			return  # already expanded
		self.children[node] = node.find_children()

	def _simulate(self, node):
		"Returns the reward for a random simulation (to completion) of `node`"
		node_copy = copy.deepcopy(node)
		node_copy.reset_identifier()
		if node_copy.current_player.name == "ENEMY": invert_reward = False
		if node_copy.current_player.name == "MCTS": invert_reward = True
		while True: # preglej ta simulate pa backpropagate da vidiš da rewardi pravilno delujejo, mogoč je to bug
			if node_copy.is_terminal():
				reward = node_copy.reward()
				return -1 * reward if invert_reward else reward
			node_copy = node_copy.play_set_turn()

	def _backpropagate(self, path, reward):
		"Send the reward back up to the ancestors of the leaf"
		#path = copy.deepcopy(path)
		for node in reversed(path):
			#if node.current_player.name == "ENEMY": reward = reward * -1
			#if node.current_player.name == "MCTS": reward = reward
			self.N[node] += 1
			self.Q[node] += reward
			reward = reward * -1 # 1 for me is 0 for my enemy, and vice versa

	def _uct_select(self, node):
		"Select a child of node, balancing exploration & exploitation"

		# All children of node should already be expanded:
		assert all(n in self.children for n in self.children[node])

		log_N_vertex = math.log(self.N[node])
		#print("log vertex: "+str(log_N_vertex))
		def uct(n):
			"Upper confidence bound for trees"
			return self.Q[n] / self.N[n] + self.exploration_weight * math.sqrt(
				log_N_vertex / self.N[n]
			)

		return max(self.children[node], key=uct)