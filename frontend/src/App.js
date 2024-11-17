import React, { useState, useEffect } from 'react';
import GameBoard from './components/GameBoard';
import './styles.css';

function App() {
    const [gameState, setGameState] = useState(null);
    const [ws, setWs] = useState(null);
    const [aiAgent, setAiAgent] = useState("DQN"); // Выбранный ИИ
    const [playerNames, setPlayerNames] = useState(["Player 1", "AI"]); // Имена игроков

    useEffect(() => {
        const newWs = new WebSocket('ws://localhost:8000/ws');

        newWs.onopen = () => {
            setWs(newWs);
            console.log('WebSocket connection opened');
        };

        newWs.onmessage = (event) => {
            const newGameState = JSON.parse(event.data);
            setGameState(newGameState);
            console.log('Received game state:', newGameState);
        };

        newWs.onclose = () => {
            console.log('WebSocket connection closed');
            setWs(null);
            setGameState(null);
        };

        return () => {
            if (newWs) {
                newWs.close();
            }
        };
    }, []);

    const startGame = () => {
        if (ws) {
            ws.send(JSON.stringify({
                action: 'start_game',
                player_names: playerNames,
                ai_agent: aiAgent,
            }));
        }
    };

    const makeMove = (playerIndex, cardIndex, street) => {
        if (ws) {
            ws.send(JSON.stringify({
                action: 'make_move',
                player_index: playerIndex,
                card_index: cardIndex,
                street: street,
            }));
        }
    };

    const handleAiAgentChange = (event) => {
        setAiAgent(event.target.value);
    };

    const handlePlayerNameChange = (index, event) => {
        const newPlayerNames = [...playerNames];
        newPlayerNames[index] = event.target.value;
        setPlayerNames(newPlayerNames);
    };

    return (
        <div className="app">
            <h1>OFC Pineapple Poker</h1>

            <div>
                <label htmlFor="aiAgentSelect">Select AI Agent:</label>
                <select id="aiAgentSelect" value={aiAgent} onChange={handleAiAgentChange}>
                    <option value="DQN">DQN</option>
                    <option value="A3C">A3C</option>
                    <option value="PPO">PPO</option>
                </select>
            </div>

            <div>
                {playerNames.map((name, index) => (
                    <div key={index}>
                        <label htmlFor={`playerName${index}`}>Player {index + 1} Name:</label>
                        <input
                            type="text"
                            id={`playerName${index}`}
                            value={name}
                            onChange={(e) => handlePlayerNameChange(index, e)}
                        />
                    </div>
                ))}
            </div>

            <button onClick={startGame} disabled={gameState !== null}>Start Game</button>

            {gameState && <GameBoard gameState={gameState} makeMove={makeMove} />}
        </div>
    );
}

export default App;
