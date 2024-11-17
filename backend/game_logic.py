from enum import Enum
from typing import List, Tuple, Dict, Any
from collections import namedtuple
import random
from itertools import groupby

from utils.logger import get_logger

logger = get_logger(__name__)

class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

class Suit(Enum):
    CLUBS = 1
    DIAMONDS = 2
    HEARTS = 3
    SPADES = 4

Card = namedtuple("Card", ["rank", "suit"])

class Street(Enum):
    FRONT = 1
    MIDDLE = 2
    BACK = 3

class Board:
    def __init__(self):
        self.front = []
        self.middle = []
        self.back = []

    def __repr__(self):
        return f"Front: {self.front}, Middle: {self.middle}, Back: {self.back}"

class Player:
    def __init__(self, name: str):
        self.name = name
        self.hand: List[Card] = []
        self.board = Board()
        self.score = 0

hand_ranks = {
    "High Card": 1,
    "One Pair": 2,
    "Two Pair": 3,
    "Three of a Kind": 4,
    "Straight": 5,
    "Flush": 6,
    "Full House": 7,
    "Four of a Kind": 8,
    "Straight Flush": 9,
}

class Game:
    def __init__(self, players: List[Player], ai_agent):
        self.players = players
        self.deck: List[Card] = []
        self.current_player_index = 0
        self.ai_agent = ai_agent
        self.current_street = Street.FRONT

    def create_deck(self):
        self.deck = [Card(rank, suit) for rank in Rank for suit in Suit]
        random.shuffle(self.deck)

    def deal_cards(self, num_cards: int) -> List[Card]:
        return [self.deck.pop() for _ in range(num_cards)]

    def start_game(self):
        self.create_deck()
        for player in self.players:
            player.hand = self.deal_cards(5)
        self.current_street = Street.FRONT

    def _is_flush(self, cards: List[Card]) -> bool:
        return len({card.suit for card in cards}) == 1

    def _is_straight(self, cards: List[Card]) -> bool:
        ranks = sorted([card.rank.value for card in cards])
        return all(ranks[i] + 1 == ranks[i+1] for i in range(len(ranks) - 1)) or ranks == [2, 3, 4, 5, 14]

    def _find_sets(self, cards: List[Card]) -> List[List[Card]]:
        sets = []
        for rank, group in groupby(sorted(cards, key=lambda card: card.rank.value), lambda card: card.rank.value):
            group_list = list(group)
            if len(group_list) >= 3:
                sets.append(group_list[:3])
        return sets

    def _find_pairs(self, cards: List[Card]) -> List[List[Card]]:
        pairs = []
        for rank, group in groupby(sorted(cards, key=lambda card: card.rank.value), lambda card: card.rank.value):
            group_list = list(group)
            if len(group_list) >= 2:
                pairs.append(group_list[:2])
        return pairs

    def _evaluate_hand(self, cards: List[Card]) -> Tuple[str, List[Card]]:
        if self._is_flush(cards) and self._is_straight(cards):
            return "Straight Flush", cards
        sets = self._find_sets(cards)
        if sets:
            return ("Four of a Kind" if len(sets[0]) == 4 else "Three of a Kind"), sets[0]
        if self._is_flush(cards):
            return "Flush", cards
        if self._is_straight(cards):
            return "Straight", cards
        pairs = self._find_pairs(cards)
        if len(pairs) == 2:
            return "Two Pair", pairs[0] + pairs[1]
        if pairs:
            return "One Pair", pairs[0]
        return "High Card", [max(cards, key=lambda card: card.rank.value)]

    def _compare_hands(self, hand1: List[Card], hand2: List[Card]) -> int:
        hand1_eval, hand1_cards = self._evaluate_hand(hand1)
        hand2_eval, hand2_cards = self._evaluate_hand(hand2)

        hand1_rank = hand_ranks[hand1_eval]
        hand2_rank = hand_ranks[hand2_eval]

        if hand1_rank > hand2_rank:
            return 1
        elif hand1_rank < hand2_rank:
            return -1
        else:
            for card1, card2 in zip(sorted(hand1_cards, key=lambda card: card.rank.value, reverse=True),
                                    sorted(hand2_cards, key=lambda card: card.rank.value, reverse=True)):
                if card1.rank.value > card2.rank.value:
                    return 1
                elif card1.rank.value < card2.rank.value:
                    return -1
            return 0

    def calculate_score(self, player1: Player, player2: Player) -> Tuple[int, int]:
        score1 = 0
        score2 = 0

        result_front = self._compare_hands(player1.board.front, player2.board.front)
        result_middle = self._compare_hands(player1.board.middle, player2.board.middle)
        result_back = self._compare_hands(player1.board.back, player2.board.back)

        if result_front == 1:
            score1 += 1
        elif result_front == -1:
            score2 += 1

        if result_middle == 1:
            score1 += 1
        elif result_middle == -1:
            score2 += 1

        if result_back == 1:
            score1 += 1
        elif result_back == -1:
            score2 += 1

        if score1 > score2:
            score1 += 3
        elif score2 > score1:
            score2 += 3

        return score1, score2

    def check_fantasyland(self, player: Player):
        if not player.board.front:
            return False
        hand_eval, _ = self._evaluate_hand(player.board.front)
        if hand_ranks.get(hand_eval, 0) >= hand_ranks["One Pair"] and player.board.front[0].rank == player.board.front[1].rank and player.board.front[0].rank.value >= Rank.QUEEN.value:
            return True
        return False

    def make_move(self, player_index: int, card: Card, street: Street):
        player = self.players[player_index]

        if card not in player.hand:
            raise ValueError("Card not in player's hand")

        if street == Street.FRONT:
            if len(player.board.front) < 3:
                player.board.front.append(card)
                player.hand.remove(card)
            else:
                raise ValueError("Front street is full")
        elif street == Street.MIDDLE:
            if len(player.board.middle) < 5:
                player.board.middle.append(card)
                player.hand.remove(card)
            else:
                raise ValueError("Middle street is full")
        elif street == Street.BACK:
            if len(player.board.back) < 5:
                player.board.append(card)
                player.hand.remove(card)
            else:
                raise ValueError("Back street is full")

        if self.check_fantasyland(player):
            player.hand.extend(self.deal_cards(14))

            fantasy_board = Board()
            remaining_cards = player.hand[:]
            for _ in range(13):
                legal_moves = self.get_legal_moves_fantasy(fantasy_board, remaining_cards)
                if not legal_moves:
                    break

                fantasy_card, fantasy_street = self.ai_agent.choose_move(fantasy_board, remaining_cards, legal_moves, None, think_time=1)
                if fantasy_street == Street.FRONT:
                    fantasy_board.front.append(fantasy_card)
                elif fantasy_street == Street.MIDDLE:
                    fantasy_board.middle.append(fantasy_card)
                elif fantasy_street == Street.BACK:
                    fantasy_board.back.append(fantasy_card)
                remaining_cards.remove(fantasy_card)

            player.board = fantasy_board
            player.hand = remaining_cards
            self.end_game()
            return

        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        if self.current_player_index == 0 and all(len(p.board.front) == 3 for p in self.players):
            self.current_street = Street.MIDDLE
        if self.current_player_index == 0 and all(len(p.board.middle) == 5 for p in self.players):
            self.current_street = Street.BACK

        if all(len(p.board.back) == 5 for p in self.players):
            self.end_game()

        # Ход ИИ
        if self.players[self.current_player_index].name == "AI":
            legal_moves = self.get_legal_moves(self.current_player_index)
            if legal_moves:
                ai_card, ai_street = self.ai_agent.choose_move(self.players[self.current_player_index].board, self.players[self.current_player_index].hand, legal_moves, None, think_time=1)
                self.make_move(self.current_player_index, ai_card, ai_street)

    def get_legal_moves(self, player_index: int) -> List[Tuple[Card, Street]]:
        player = self.players[player_index]
        legal_moves = []
        for card in player.hand:
            for street in Street:
                if street == Street.FRONT and len(player.board.front) < 3:
                    legal_moves.append((card, street))
                elif street == Street.MIDDLE and len(player.board.middle) < 5:
                    legal_moves.append((card, street))
                elif street == Street.BACK and len(player.board.back) < 5:
                    legal_moves.append((card, street))
        return legal_moves

    def get_legal_moves_fantasy(self, board: Board, hand: List[Card]) -> List[Tuple[Card, Street]]:
        legal_moves = []
        for card in hand:
            for street in Street:
                if street == Street.FRONT and len(board.front) < 3:
                    legal_moves.append((card, street))
                elif street == Street.MIDDLE and len(board.middle) < 5:
                    legal_moves.append((card, street))
                elif street == Street.BACK and len(board.back) < 5:
                    legal_moves.append((card, street))
        return legal_moves

    def end_game(self):
        for i in range(len(self.players)):
            for j in range(i + 1, len(self.players)):
                score1, score2 = self.calculate_score(self.players[i], self.players[j])
                self.players[i].score += score1
                self.players[j].score += score2

        winner = max(self.players, key=lambda p: p.score)

        logger.info("Game ended!")
        logger.info(f"Scores: {[p.name: p.score for p in self.players]}")
        logger.info(f"Winner: {winner.name}")

        self.deck = []
        self.current_player_index = 0
        for player in self.players:
            player.hand = []
            player.board = Board()
            player.score = 0
        self.current_street = None

    def get_game_state(self) -> Dict[str, Any]:
        game_state = {
            "players": [
                {
                    "name": player.name,
                    "hand": [{"rank": card.rank.name, "suit": card.suit.name} for card in player.hand],
                    "board": {
                        "front": [{"rank": card.rank.name, "suit": card.suit.name} for card in player.board.front],
                        "middle": [{"rank": card.rank.name, "suit": card.suit.name} for card in player.board.middle],
                        "back": [{"rank": card.rank.name, "suit": card.suit.name} for card in player.board.back],
                    },
                    "score": player.score,
                }
                for player in self.players
            ],
            "current_player_index": self.current_player_index,
            "current_street": self.current_street.name if self.current_street else None,
            "game_over": not self.deck,
            "winner": max(self.players, key=lambda p: p.score).name if not self.deck else None
        }
        return game_state
