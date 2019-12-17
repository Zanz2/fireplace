import os.path
import random
import time
from bisect import bisect
from importlib import import_module
from pkgutil import iter_modules
from typing import List
from xml.etree import ElementTree
from fireplace.monte_carlo_tree import *
from fireplace.exceptions import GameOver

from hearthstone.enums import CardClass, CardType


# Autogenerate the list of cardset modules
_cards_module = os.path.join(os.path.dirname(__file__), "cards")
CARD_SETS = [cs for _, cs, ispkg in iter_modules([_cards_module]) if ispkg]


class CardList(list):
	def __contains__(self, x):
		for item in self:
			if x is item:
				return True
		return False

	def __getitem__(self, key):
		ret = super().__getitem__(key)
		if isinstance(key, slice):
			return self.__class__(ret)
		return ret

	def __int__(self):
		# Used in Kettle to easily serialize CardList to json
		return len(self)

	def contains(self, x):
		"""
		True if list contains any instance of x
		"""
		for item in self:
			if x == item:
				return True
		return False

	def index(self, x):
		for i, item in enumerate(self):
			if x is item:
				return i
		raise ValueError

	def remove(self, x):
		for i, item in enumerate(self):
			if x is item:
				del self[i]
				return
		raise ValueError

	def exclude(self, *args, **kwargs):
		if args:
			return self.__class__(e for e in self for arg in args if e is not arg)
		else:
			return self.__class__(e for k, v in kwargs.items() for e in self if getattr(e, k) != v)

	def filter(self, **kwargs):
		return self.__class__(e for k, v in kwargs.items() for e in self if getattr(e, k, 0) == v)


def random_draft(card_class: CardClass, exclude=[]):
	"""
	Return a deck of 30 random cards for the \a card_class
	"""
	from . import cards
	from .deck import Deck

	deck = []
	collection = []
	# hero = card_class.default_hero

	for card in cards.db.keys():
		if card in exclude:
			continue
		cls = cards.db[card]
		if not cls.collectible:
			continue
		if cls.type == CardType.HERO:
			# Heroes are collectible...
			continue
		if cls.card_class and cls.card_class not in [card_class, CardClass.NEUTRAL]:
			# Play with more possibilities
			continue
		collection.append(cls)

	while len(deck) < Deck.MAX_CARDS:
		card = random.choice(collection)
		if deck.count(card.id) < card.max_count_in_deck:
			deck.append(card.id)

	return deck

def mcts_draft(card_class: CardClass, exclude=[]):
	"""
	Return a midrange deck for mage
	"""
	from . import cards
	from .deck import Deck

	deck = []
	collection = []
	# hero = card_class.default_hero
	include = ["Arcane Missiles","Frostbolt","Arcane Intellect","Fireball","Polymorph","Water Elemental","Flamestrike","Acidic Swamp Ooze","Bloodfen Raptor","Razorfen Hunter","Shattered Sun Cleric","Chillwind Yeti","Gnomish Inventor","Gurubashi Berserker","Boulderfist Ogre"]
	for card in cards.db.keys():
		if card in exclude:
			continue
		cls = cards.db[card]
		if not cls.collectible:
			continue
		if cls.type == CardType.HERO:
			# Heroes are collectible...
			continue
		if cls.card_class and cls.card_class not in [card_class, CardClass.NEUTRAL]:
			# Play with more possibilities
			continue
		if cls.name in include:
			if collection.count(cls) < cls.max_count_in_deck:
				collection.append(cls)
				collection.append(cls)
		continue

	if len(collection) < Deck.MAX_CARDS:
		raise Exception('Deck wasnt completely filled. Deck count was: {}'.format(Deck.MAX_CARDS))
	else:
		while len(deck) < Deck.MAX_CARDS:
			card = random.choice(collection)
			if deck.count(card.id) < card.max_count_in_deck:
				deck.append(card.id)
	#card = random.choice(collection)
	#if deck.count(card.id) < card.max_count_in_deck:
	#deck.append(card.id)

	return deck

def random_class():
	return CardClass(random.randint(3, 10))


def get_script_definition(id):
	"""
	Find and return the script definition for card \a id
	"""
	for cardset in CARD_SETS:
		module = import_module("fireplace.cards.%s" % (cardset))
		if hasattr(module, id):
			return getattr(module, id)


def entity_to_xml(entity):
	e = ElementTree.Element("Entity")
	for tag, value in entity.tags.items():
		if value and not isinstance(value, str):
			te = ElementTree.Element("Tag")
			te.attrib["enumID"] = str(int(tag))
			te.attrib["value"] = str(int(value))
			e.append(te)
	return e


def game_state_to_xml(game):
	tree = ElementTree.Element("HSGameState")
	tree.append(entity_to_xml(game))
	for player in game.players:
		tree.append(entity_to_xml(player))
	for entity in game:
		if entity.type in (CardType.GAME, CardType.PLAYER):
			# Serialized those above
			continue
		e = entity_to_xml(entity)
		e.attrib["CardID"] = entity.id
		tree.append(e)

	#for player in game.players:
	#	for hand in player.hand:
	#		hand = entity_to_xml(hand)
	#		tree.append(hand)

	#for element in game.board:
	#	tree.append(entity_to_xml(element))
	#tree.append(entity_to_xml(game.current_player))
	return ElementTree.tostring(tree)


def weighted_card_choice(source, weights: List[int], card_sets: List[str], count: int):
	"""
	Take a list of weights and a list of card pools and produce
	a random weighted sample without replacement.
	len(weights) == len(card_sets) (one weight per card set)
	"""

	chosen_cards = []

	# sum all the weights
	cum_weights = []
	totalweight = 0
	for i, w in enumerate(weights):
		totalweight += w * len(card_sets[i])
		cum_weights.append(totalweight)

	# for each card
	for i in range(count):
		# choose a set according to weighting
		chosen_set = bisect(cum_weights, random.random() * totalweight)

		# choose a random card from that set
		chosen_card_index = random.randint(0, len(card_sets[chosen_set]) - 1)

		chosen_cards.append(card_sets[chosen_set].pop(chosen_card_index))
		totalweight -= weights[chosen_set]
		cum_weights[chosen_set:] = [x - weights[chosen_set] for x in cum_weights[chosen_set:]]

	return [source.controller.card(card, source=source) for card in chosen_cards]


def setup_game( mcts=False) -> ".game.Game":
	from .game import Game
	from .player import Player

	#class1 = random_class()
	#class2 = random_class()
	class1 = CardClass.MAGE
	class2 = CardClass.MAGE
	if mcts:
		deck1 = mcts_draft(class1)
		deck2 = mcts_draft(class2)
	else:
		deck1 = random_draft(class1)
		deck2 = random_draft(class2)
	player1 = Player("Player1", deck1, class1.default_hero)
	player2 = Player("Player2", deck2, class2.default_hero)

	game = Game(players=(player1, player2))
	game.start()

	return game


def play_turn(game: ".game.Game") -> ".game.Game":
	player = game.current_player

	while True:

		# iterate over our hand and play whatever is playable
		shuffled_hand = player.hand
		random.shuffle(shuffled_hand)
		for card in shuffled_hand:
			if card.is_playable():
				target = None
				if card.must_choose_one and card.choose_cards is not None:
					card = random.choice(card.choose_cards)
				if card.requires_target() and card.targets is not None:
					target = random.choice(card.targets)
				# print("Playing %r on %r" % (card, target))
				if (card.is_playable() and not card.requires_target()) or (
					card.is_playable() and card.requires_target() and target is not None): card.play(target=target)

				if player.choice:
					choice = random.choice(player.choice.cards)
					# print("Choosing card %r" % (choice))
					player.choice.choose(choice)

				continue

		# Randomly attack with whatever can attack
		shuffled_characters = player.characters
		random.shuffle(shuffled_characters)
		for character in shuffled_characters:
			if character.can_attack():
				character.attack(random.choice(character.targets))

		break

		heropower = player.hero.power
		if heropower.is_usable():
			if heropower.requires_target():
				heropower.use(target=random.choice(heropower.targets))
			else:
				heropower.use()
			continue
	game.end_turn()
	return game


def play_full_game() -> ".game.Game":
	game = setup_game()

	for player in game.players:
		print("Can mulligan %r" % (player.choice.cards))
		mull_count = random.randint(0, len(player.choice.cards))
		cards_to_mulligan = random.sample(player.choice.cards, mull_count)
		player.choice.choose(*cards_to_mulligan)

	while True:
		play_turn(game)

	return game

def play_full_mcts_game(expl_weight) -> ".game.Game":
	game = setup_game(mcts=True)

	tree = MCTS(exploration_weight=expl_weight)
	for player in game.players:
		cards_to_mulligan = []
		for card in player.choice.cards:
			if card.cost > 3:
				cards_to_mulligan.append(card)
		player.choice.choose(*cards_to_mulligan)


	while True:
		#print(game.current_player)
		#game2 = copy.deepcopy(game)
		t_end = time.time() + 74
		rollout_num = 0
		while time.time() < t_end:
			try:
				tree.do_rollout(game)
				rollout_num += 1
			except GameOver:
				pass
		try:
			game = tree.choose(game)
		except RuntimeError:
			return game
		#if game2.__hash__() == game.__hash__() : print("enaka")
		#print(game.current_player)
		game.end_turn()
		#print(game.current_player)
		print("# expanded nodes on tree: " + str(len(tree.children)) + " # rollouts: "+str(rollout_num))
		play_turn(game)


	return game
