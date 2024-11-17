from abc import ABC, abstractmethod
from typing import Tuple, List, Optional, Dict, Any
import numpy as np

from core.card import Card
from core.board import Street, Board
from utils.logger import get_logger

logger = get_logger(__name__)

class RLAgent(ABC):
    def __init__(self, name: str, state_size: int, action_size: int, config: dict, think_time: int = 30):
        self.name = name
        self.state_size = state_size
        self.action_size = action_size
        self.config = config
        self.think_time = think_time # Время на ход для агента
        self.gamma = config.get('gamma', 0.99)  # Коэффициент дисконтирования
        self.learning_rate = config.get('learning_rate', 0.001)
        self.epsilon = config.get('epsilon', 1.0)  # Epsilon для epsilon-greedy
        self.epsilon_min = config.get('epsilon_min', 0.01)
        self.epsilon_decay = config.get('epsilon_decay', 0.995)
        self.memory = [] # Replay buffer для DQN
        self.training_history = [] # История обучения
        self.reset_stats()

    @classmethod
    def load_latest(cls, name: str = None, state_size: int = None, action_size: int = None, config: dict = None, think_time: int = 30):
        return cls(name=name, state_size=state_size, action_size=action_size, config=config, think_time=think_time)

    def save_model(self, filepath: str) -> None:
        pass  # Реализация сохранения модели в подклассах

    def load_model(self, filepath: str) -> None:
        pass  # Реализация загрузки модели в подклассах

    @abstractmethod
    def choose_move(self,
                   board: Board,
                   cards: List[Card],
                   legal_moves: List[Tuple[Card, Street]],
                   opponent_board: Optional[Board] = None,
                   think_time: Optional[int] = None) -> Tuple[Card, Street]:
        pass

    def _get_legal_action_mask(self, legal_moves):
        mask = np.zeros(self.action_size)
        card_street_to_index = {
            (Card(Rank(rank), Suit(suit)), Street(street)): index
            for index, (rank, suit, street) in enumerate(
                [(rank.value, suit.value, street.value) for rank in Rank for suit in Suit for street in Street]
            )
        }
        for move in legal_moves:
            mask[card_street_to_index.get(move, 0)] = 1  # Присваиваем 1 только легальным действиям
        return mask

    def notify_game_start(self, initial_cards: List[Card]) -> None:
        self.reset_stats()
        self.current_cards = initial_cards.copy()

    def notify_opponent_move(self, card: Card, street: Street, board_state: Dict) -> None:
        pass

    def notify_move_result(self, card: Card, street: Street,
                          success: bool, board_state: Dict) -> None:
        pass

    def notify_game_end(self, result: Dict[str, Any]) -> None:
        pass

    def reset_stats(self) -> None:
        self.games_played = 0
        self.games_won = 0
        self.total_score = 0
        self.moves = []
        self.opponent_moves = []
        self.current_cards = []
        self.game_history = []

    def get_stats(self) -> Dict[str, Any]:
        stats = {
            'name': self.name,
            'games_played': self.games_played,
            'games_won': self.games_won,
            'win_rate': self.games_won / self.games_played if self.games_played > 0 else 0,
            'average_score': self.total_score / self.games_played if self.games_played > 0 else 0,
            'total_moves': len(self.moves),
            'successful_moves': sum(1 for move in self.moves if move['success']),
            'think_time': self.think_time
        }
        return stats

    def save_game_stats(self, result: Dict[str, Any]) -> None:
        pass
