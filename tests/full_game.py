#!/usr/bin/env python
import json
import sys

from hearthstone.enums import PlayState

from fireplace import cards
from fireplace.exceptions import GameOver
from fireplace.utils import play_full_game, play_full_mcts_game


sys.path.append("..")


def test_full_game():
	do_mcts = True
	starting_expl_weight = -2
	log_dict = {}
	if not do_mcts:
		try:
			play_full_game()
		except GameOver:
			print("Game completed normally.")
	else:
		won = 0
		lost = 0
		tied = 0
		i = 0
		while(True):
			if( False and i%20 == 0 and i!= 0): # 20 games at a given expl weight
				log_dict[starting_expl_weight] = [won, lost, tied]
				starting_expl_weight += 1
				print("expl_weight: " + str(starting_expl_weight) + "-------------------------")
				won = 0
				lost = 0
				i = 0
				tied = 0
				output = json.dumps(log_dict)
				with open('result_auto_logged.txt', 'w') as outfile:
					json.dump(output, outfile)
			game = play_full_mcts_game(expl_weight=starting_expl_weight)
			mcts_player = game.players[0]

			print("mcts hp: " + str(game.players[0].hero.health) + ", enemy hp: "+ str(game.players[1].hero.health))
			print("mcts hand count:"+str(len(game.players[0].hand))+" , graveyard count:"+str(len(game.players[0].graveyard))+" ,deck count: "+str(len(game.players[0].deck)))
			print("mcts field count, max mana count:"+str(len(game.players[0].field))+" , "+str(game.players[0]._max_mana))
			print("enemy hand count:" + str(len(game.players[1].hand)) + " , graveyard count:" + str(len(game.players[1].graveyard)) + " ,deck count: " + str(len(game.players[1].deck)))
			print("enemy field count, max mana count:" + str(len(game.players[1].field)) + " , " + str(game.players[1]._max_mana))
			print("board minion total count: "+str(len(game.board)))
			if mcts_player.playstate == PlayState.WON:
				won += 1
				print("won game on turn: "+str(game.ended_on)+", currently:" + str(won) + "/" + str(i+1) + "(tied:"+str(tied)+")")
			elif mcts_player.playstate == PlayState.TIED:
				tied += 1
				print("tied game on turn: " + str(game.ended_on) + ", currently:" + str(won) + "/" + str(i + 1) + "(tied:" + str(tied) + ")")
			else:
				lost += 1
				print("lost game on turn: "+str(game.ended_on)+", currently:" + str(won) + "/" + str(i+1))
			i = i + 1
		print("w/l")
		print(won)
		print(lost)
		print(float(won/lost))



def main():
	cards.db.initialize()
	if len(sys.argv) > 1:
		numgames = sys.argv[1]
		if not numgames.isdigit():
			sys.stderr.write("Usage: %s [NUMGAMES]\n" % (sys.argv[0]))
			exit(1)
		for i in range(int(numgames)):
			test_full_game()
	else:
		test_full_game()


if __name__ == "__main__":
	main()
