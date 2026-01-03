import random
import itertools
import re
import os

color_map = {"black": "\x1b[90m", "red": "\x1b[91m"}

class Card():
	def __init__(self, suit, value) -> None:
		self.suit = suit
		self.value = value
		self.color = "black" if self.suit in "♠♣B" else "red"
	
	def __repr__(self) -> str:
		return f"{color_map[self.color]}{' ' if self.value != 10 else ''}{self.value} {self.suit}\x1b[0m"
	
	def locate(self):
		for p in Player.players:
			if self in p.hand:
				return p
			
	def get_value(self):
		return f"{color_map[self.color]}{self.value}\x1b[0m"
	
	def get_suit(self):
		return f"{color_map[self.color]}{self.suit}\x1b[0m"
	
	def get_group(self):
		vals = [{"2", "3", "4", "5", "6", "7"}, {"9", "10", "J", "Q", "K", "A"}]
		suits = {"♠", "♣", "♥", "♦"}

		if self.value == "8":
			s_g = suits.copy()
			s_g.remove(self.suit)
			return [get_card(s, "8") for s in s_g] + [get_card(s, "★") for s in "RB"]
		elif self.value in "★":
			return [get_card(s, "8") for s in suits] + [get_card("B" if self.suit == "R" else "R", "★")]
		
		v_g = set()
		for g in vals:
			if self.value in g:
				v_g = g.copy()
				v_g.remove(self.value)
				break
		return [get_card(self.suit, v) for v in v_g]

def cards_in_play():
	return [c for p in Player.players for c in p.hand]

def players_playing():
	return [str(player.name) for player in Player.players]

def get_card(suit, value):
	for p in Player.players:
		for c in p.hand:
			if c.suit == suit and c.value == value:
				return c
			
def get_player(name):
	for p in Player.players:
		if p.name == name:
			return p
		
def get_hand(fisher):
	print(f"Your hand:", str(fisher.hand)[1:-1])

def get_team(i):
	return [p for p in Player.players if p.team == i]

def get_teams(top_of_list=None):
	team0 = [p for p in Player.players if p.team == 0]
	team1 = [p for p in Player.players if p.team == 1]

	def fmt_team(team, highlight_name=None):
		if not team:
			return ""
		score = team[0].score // 6
		names = []
		for p in team:
			if highlight_name and p.name == highlight_name:
				names.append(f"\x1b[1m{p.name}\x1b[0m\x1b[4m")
			else:
				names.append(p.name)
		return f"{' & '.join(names)} ― {score}"

	if top_of_list:
		fisher = get_player(top_of_list)
		if fisher and fisher.team == 0:
			print("\x1b[4m", end="")
			print(fmt_team(team0, highlight_name=top_of_list))
			print("\x1b[0m", end="")
			print(fmt_team(team1))
		else:
			print("\x1b[4m", end="")
			print(fmt_team(team1, highlight_name=top_of_list))
			print("\x1b[0m", end="")
			print(fmt_team(team0))
	else:
		print(fmt_team(team0))
		print(fmt_team(team1))
	
class Deck():
	cards = []
	def __init__(self) -> None:
		# Make deck
		for value in ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"):
			for suit in ("♠", "♣", "♥", "♦"):
				Deck.cards.append(Card(suit, value))

		Deck.cards.append(Card("R", "★"))
		Deck.cards.append(Card("B", "★"))

	def shuffle(self):
		random.shuffle(Deck.cards)

	def play_with(self, players):
		if isinstance(players, int):
			players = range(players)
		for player in players:
			Player.players.append(Player(str(player)))

		for i, p in enumerate(Player.players):
			p.team = 0 if i % 2 == 0 else 1

	def deal(self):
		player_iter = itertools.cycle(Player.players)
		while len(Deck.cards) > 0:
			next(player_iter).hand.add(Deck.cards.pop())

class Player():
	players = []
	def __init__(self, name) -> None:
		self.name = name
		self.hand = set()
		self.team = None
		self.score = 0

	def add(self, card: Card):
		self.hand.add(card)

	def remove(self, card: Card):
		self.hand.remove(card)
		if len(self) == 0:
			Player.players.remove(self)

	def has_group_of(self, card): 
		if not set(card.get_group()).isdisjoint(self.hand):
			return True
		return False

	def __repr__(self) -> str:
		return f"{self.name}: {self.hand}"
		# return str(self.name)
	
	def __len__(self) -> int:
		return len(self.hand)
	
	def all_in_hand(self, card) -> bool:
		if all(c in self.hand for c in card.get_group()):
			return True
		return False

def play(deck):
	finished = set()
	fisher = Player.players[0]
	while len(finished) < 54:

		CARD_SPLIT_RE = r"[;,*\n\s]+"

		def reader(prompt: str):
			raw = sci(input(prompt))
			normalized = raw.replace("", " ")[1:-1].replace("1 0", "10")
			tokens = [t for t in re.split(CARD_SPLIT_RE, normalized) if t]
			return tokens

		def parser(tokens):
			if not tokens:
				return []
			if tokens == ['-']:
				return '-'
			if len(tokens) % 2 != 0:
				return None

			pairs = list(zip(tokens[::2], tokens[1::2]))
			cards = []
			for value, suit in pairs:
				c = get_card(suit, value)
				cards.append(c)
			return cards

		def prompt_declare(fisher, target_player):
			while True:
				prompt = f"What do you declare {target_player.name} to have? (ENTER to ask, - if none) "
				tokens = reader(prompt)

				# ENTER
				if not tokens:
					return None
				declared = parser(tokens)
				if declared is None:
					print("That's not a card.")
					continue
					
				# Validate cards first
				all_valid = True
				for c in declared:
					if c == '-':
						continue
					elif c not in cards_in_play():
						print("This card is invalid or not in play anymore.")
						all_valid = False
					elif len(declare_list) != 0 and c is not declare_list[0][0] and c not in declare_list[0][0].get_group():
						print(f"{c} is not in the same group.")
						all_valid = False
					elif c is not declared[0] and c not in declared[0].get_group(): # type: ignore
						print(f"{c} is not in the same group.")
						all_valid = False
					elif c not in target_player.hand and target_player is fisher:
						print(f"You don't have {c} in your hand.")
						all_valid = False
					elif c in fisher.hand and target_player is not fisher:
						print(f"{c} is in your hand, not with {target_player.name}.")
						all_valid = False
					elif declared.count(c) > 1:
						print(f"You already declared {c}.")
						all_valid = False
						break
					elif c in [x for y in declare_list for x in y]:
						print(f"You already declared {c}.")
						all_valid = False
				if all_valid:
					return declared

		fish = None
		valid_fish = False

		while not valid_fish:
			fishee = None

			# Select opponent OR enter declare mode
			while fishee is None or (fishee != "" and fishee not in opps): # type: ignore

				os.system("clear")
				get_teams(fisher.name) # type: ignore
				get_hand(fisher)

				for f in Player.players:
					if f is not fisher:
						print(f"{f.name} has {len(f)} cards.")

				opps = players_playing()
				for p in [pl for pl in Player.players if pl.team == fisher.team]:
					if p.name in opps:
						opps.remove(p.name)

				fishee = input(f"Who are you asking? ({str(opps)[2:-2].replace(r"', '", r', ')}, ENTER to declare) ")

				# Declare mode
				if fishee == "":
					declare_list = []

					exited_to_ask = False
					for t in get_team(fisher.team):  # type: ignore
						declared_cards = prompt_declare(fisher, t)
						if declared_cards is None:
							exited_to_ask = True
							break
						print(*declared_cards)
						if '-' not in declared_cards:
							declare_list.append(declared_cards)
					if exited_to_ask:
						# ENTER
						fishee = None
						continue
					if sum(len(group) for group in declare_list) != 6:
						print("You need six cards to make a group.")
						fishee = None
						continue
					# Checks if the declaration is valid (painfully and unnecessarily complicated)
					if ((lambda group: ((set().union(*[(set(p.hand) & group) for p in get_team(fisher.team)]) if get_team(fisher.team) else set()) == group # type: ignore
								and sorted([frozenset(set(p.hand) & group) for p in get_team(fisher.team) if (set(p.hand) & group)]) == sorted([frozenset(t) for t in declare_list])))(set(declare_list[0][0].get_group() + [declare_list[0][0]]))): # type: ignore
						print("Declaration correct.")
						for t in declare_list:
							for c in t:
								finished.add(c)
								# For rounding reasons, score will always be six times too high. The printout will change this.
								for p in Player.players:
									if p.team == fisher.team: # type: ignore
										p.score += 1
								c.locate().remove(c)
						print(*[x for y in declare_list for x in y])
					else:
						print("Declaration incorrect.")
						for t in declare_list:
							for c in t:
								finished.add(c)
								s = 0
								for p in Player.players:
									if c in p.hand:
										print(f"{p.name} had {c}")
										# If at least one card is not on the fisher's team
										if p != fisher.team: # type: ignore
											s = 1
									# Other team gets 0 or 1 point
									if p.team != fisher.team: # type: ignore
										p.score += s
								c.locate().remove(c)
						fisher = Player.players[(Player.players.index(fisher) + 1) % len(Player.players)]
					fishee = None
					input("ENTER to continue... ")
					continue

			# asking
			fishee = get_player(fishee)

			while True:
				tokens = reader("What card are you asking for? (value then suit) (S = ♠, C = ♣, H = ♥, D = ♦, * = ★, B = Black, R = Red) ")

				if len(tokens) != 2:
					continue

				fish = get_card(tokens[1], tokens[0])
				if fish not in cards_in_play():
					print("This card is invalid or not in play anymore.")
				elif fish in fisher.hand:  # type: ignore
					print("This card is already in your hand.")
				elif not fisher.has_group_of(fish):  # type: ignore
					print("You can't ask for that card. (You don't have a card in the same group.)")
				else:
					valid_fish = True
					break

		# did you get it?
		if fish in fishee.hand: # type: ignore
			print(f"You have received {fish} from {fishee.name}.") # type: ignore
			fishee.remove(fish) # type: ignore
			fisher.add(fish) # type: ignore
			get_hand(fisher)

			# Auto-declaration
			for card in fisher.hand: # type: ignore
				if fisher.all_in_hand(card): # type: ignore
					for sibling in card.get_group():
						finished.add(sibling)
					finished.add(card)
					# For rounding reasons, score will always be six times too high. The printout will change this.
					for p in Player.players:
						if p.team == fisher.team: # type: ignore
							p.score += 1
			for card in finished:
				if card in fisher.hand: # type: ignore
					fisher.remove(card) # type: ignore
					print(finished)
		else:
			print(f"{fishee.name} does not have the {Card.get_value(fish)} of {Card.get_suit(fish)}.") # type: ignore
			fisher = fishee # type: ignore

			input(f"ENTER to clear screen for {fisher.name}... ") # type: ignore
			os.system("clear")
		input("ENTER to continue... ")

	# Final scores
	team0 = [p for p in Player.players if p.team == 0]
	team1 = [p for p in Player.players if p.team == 1]
	score0 = team0[0].score if team0 else 0
	score1 = team1[0].score if team1 else 0
	winners = team0 if score0 >= score1 else team1
	print(f"{' and '.join([p.name for p in winners])} have won with {(winners[0].score if winners else 0) // 6} groups.")

def sci(string):
	return string.upper().translate(str.maketrans({"S": "♠", "C": "♣", "H": "♥", "D": "♦", "*": "★"}))

def main():
	print("Welcome to Literature/Fish")
	d = Deck()
	d.shuffle()

	players = None
	while players == None or players % 2 != 0 and players <= 54:
		try:
			players = int(input("How many players? (must be even) "))
		except:
			pass
	
	names = None
	while not isinstance(names, int) and (not isinstance(names, list) or len(names) != players) and names != ['']:
		names = re.split(r'[;,*\n\s]+', input("Any names? (alternate the two teams, first typed goes first, ENTER to skip and go with numbers) "))

	if names != ['']:
		players = names

	d.play_with(players)
	d.deal()
	play(d)
	input("ENTER to play again. ")
	os.system("clear")
	main()
main()