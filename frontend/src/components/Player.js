import React from 'react';
import Card from './Card';
import '../styles.css';

const Player = ({ player, isCurrentPlayer, onCardClick, current_street }) => {
    const { name, hand, board, score } = player;

    const handleCardClick = (cardIndex) => {
        if (isCurrentPlayer) {
            onCardClick(player.name, cardIndex, current_street);
        }
    };

    return (
        <div className={`player ${isCurrentPlayer ? 'current-player' : ''}`}>
            <h3>{name} (Score: {score})</h3>
            <h4>Hand:</h4>
            <div className="hand">
                {hand.map((card, index) => (
                    <Card
                        key={index}
                        card={card}
                        onClick={() => handleCardClick(index)}
                        clickable={isCurrentPlayer && hand.length > 0}
                    />
                ))}
            </div>
            <div className="board">
                <div className="street">
                    <h4>Front:</h4>
                    {board.front.map((card, index) => (
                        <Card key={index} card={card} />
                    ))}
                </div>
                <div className="street">
                    <h4>Middle:</h4>
                    {board.middle.map((card, index) => (
                        <Card key={index} card={card} />
                    ))}
                </div>
                <div className="street">
                    <h4>Back:</h4>
                    {board.back.map((card, index) => (
                        <Card key={index} card={card} />
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Player;
