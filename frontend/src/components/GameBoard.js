import React, { useState, useEffect } from 'react';
import Player from './Player';
import '../styles.css';

const GameBoard = ({ gameState, makeMove }) => {
    const { players, current_player_index, current_street, game_over, winner } = gameState || {};
    const [gameOver, setGameOver] = useState(false);
    const [winnerName, setWinnerName] = useState(null);

    useEffect(() => {
        if (gameState) {
            setGameOver(game_over);
            setWinnerName(winner);
        }
    }, [gameState]);

    const handleCardClick = (playerIndex, cardIndex) => {
        if (!gameOver && players[current_player_index].name !== 'AI') { // Проверка на завершение игры и ход ИИ
            makeMove(playerIndex, cardIndex, current_street);
        }
    };

    if (gameOver) {
        return (
            <div className="game-over">
                <h2>Game Over!</h2>
                <p>Winner: {winnerName}</p>
                <button onClick={() => { setGameOver(false); setWinnerName(null); }}>Play Again</button>
            </div>
        );
    }

    return (
        <div className="game-board">
            <div className="players">
                {players && players.map((player, index) => (
                    <Player
                        key={index}
                        player={player}
                        isCurrentPlayer={index === current_player_index}
                        onCardClick={handleCardClick}
                        current_street={current_street}
                    />
                ))}
            </div>
            {gameState && (
                <div className="game-info">
                    <p>Current Player: {players[current_player_index]?.name}</p>
                    <p>Current Street: {current_street}</p>
                </div>
            )}
        </div>
    );
};

export default GameBoard;
