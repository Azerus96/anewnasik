import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import json
import time

from agents.rl.base import RLAgent
from core.board import Board, Street
from core.card import Card
from utils.logger import get_logger

logger = get_logger(__name__)

class DQNAgent(RLAgent):
    """Deep Q-Network агент"""

    def __init__(self, name: str, state_size: int, action_size: int, config: dict, think_time: int = 30):
        super().__init__(name, state_size, action_size, config, think_time=think_time)
        self.batch_size = config.get('batch_size', 32)
        self.target_update_freq = config.get('target_update_freq', 1000)
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()

    def _build_model(self):
        model = Sequential([
            Dense(256, input_dim=self.state_size, activation='relu'),
            Dropout(0.2),
            Dense(256, activation='relu'),
            Dropout(0.2),
            Dense(128, activation='relu'),
            Dense(self.action_size, activation='linear')
        ])
        model.compile(optimizer=Adam(learning_rate=self.learning_rate), loss='mse')
        return model

    def update_target_model(self):
        self.target_model.set_weights(self.model.get_weights())

    def choose_move(self, board: Board, cards: List[Card],
                   legal_moves: List[Tuple[Card, Street]],
                   opponent_board: Optional[Board] = None,
                   think_time: Optional[int] = None) -> Tuple[Card, Street]:
        current_think_time = think_time or self.think_time
        start_time = time.time()
        state = self.encode_state(board, cards, opponent_board if opponent_board else Board()) # Передаем пустую доску, если opponent_board is None

        if np.random.rand() <= self.epsilon:
            action = random.choice(legal_moves)
            return action

        q_values = self.model.predict(state.reshape(1, -1), timeout=current_think_time)[0]
        legal_actions = self._get_legal_action_mask(legal_moves)
        q_values = q_values * legal_actions
        best_action_idx = np.argmax(q_values)
        action = legal_moves[best_action_idx]

        elapsed_time = time.time() - start_time
        if elapsed_time > current_think_time:
            logger.warning(f"DQN Think time exceeded: {elapsed_time:.2f}s > {current_think_time}s")

        return action

    def encode_state(self, board: Board, cards: List[Card], opponent_board: Board) -> np.ndarray:
        front_cards = self._encode_cards(board.front, 3)
        middle_cards = self._encode_cards(board.middle, 5)
        back_cards = self._encode_cards(board.back, 5)
        hand_cards = self._encode_cards(cards, len(cards))
        free_streets = np.array([1 if street in board.get_free_streets(cards) else 0 for street in Street])
        state = np.concatenate([front_cards, middle_cards, back_cards, hand_cards, free_streets])
        return state

    def _encode_cards(self, cards: List[Card], max_cards: int) -> np.ndarray:
        encoding = np.zeros(52)
        for card in cards:
            idx = (card.rank.value - 2) * 4 + card.suit.value - 1
            encoding[idx] = 1
        padding = np.zeros(52 * (max_cards - len(cards)))
        return np.concatenate([encoding, padding])

    def remember(self, state, action_index, reward, next_state, done):
        self.memory.append((state, action_index, reward, next_state, done))

    def replay(self):
        if len(self.memory) < self.batch_size:
            return {}

        minibatch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = [np.array(x) for x in zip(*minibatch)]

        targets = self.model.predict(states)
        next_q_values = self.target_model.predict(next_states)

        for i in range(self.batch_size):
            if dones[i]:
                targets[i][actions[i]] = rewards[i]
            else:
                targets[i][actions[i]] = rewards[i] + self.gamma * np.max(next_q_values[i])

        history = self.model.fit(states, targets, epochs=1, verbose=0)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        self.steps += 1
        if self.steps % self.target_update_freq == 0:
            self.update_target_model()

        return history.history

    def load(self, filepath: str) -> None:
        self.model.load_weights(filepath)
        self.target_model.load_weights(filepath)

    def save(self, filepath: str) -> None:
        self.model.save_weights(filepath)
        self.target_model.save_weights(filepath.replace('_main', '_target'))

    def get_stats(self) -> Dict[str, Any]:
        base_stats = super().get_stats()
        dqn_stats = {
            'epsilon': self.epsilon,
            'model_summary': str(self.model.summary()),
        }
        return {**base_stats, **dqn_stats}
