import React from 'react';
import { Card as PlayingCard } from 'playing-cards.js';
import '../styles.css';

const Card = ({ card, onClick, clickable }) => {
    if (!card) {
        return <div className="card empty-card"></div>;
    }

    const playingCard = new PlayingCard(card.rank, card.suit);
    const cardString = playingCard.toString();

    return (
        <div
            className={`card ${clickable ? 'clickable' : ''}`}
            onClick={onClick}
        >
            {cardString}
        </div>
    );
};

export default Card;
