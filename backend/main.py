from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from typing import List, Dict
import json
import uvicorn
from pathlib import Path

from game_logic import Game, Player, Card, Street, Board
from agents.rl.dqn import DQNAgent  # Или любой другой агент по умолчанию
from agents.rl.a3c import A3CAgent
from agents.rl.ppo import PPOAgent
from utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI()

# Глобальные переменные
game: Game = None
ai_agents: Dict[str, object] = {}

# Путь к frontend сборке
frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"

@app.get("/")
async def get():
    index_path = frontend_build_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        logger.error("Frontend build not found. Run 'npm run build' in the frontend directory.")
        return HTMLResponse(content="<h1>Error: Frontend build not found.</h1>", status_code=500)

@app.get("/static/{rest_of_path:path}")
async def serve_static(rest_of_path: str):
    """Обслуживание статических файлов из frontend сборки."""
    file_path = frontend_build_path / "static" / rest_of_path
    if file_path.exists():
        return FileResponse(file_path)
    else:
        return HTMLResponse(status_code=404)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global game, ai_agents
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get("action")

            if action == "start_game":
                player_names = message.get("player_names", ["Player 1", "AI"])
                ai_agent_name = message.get("ai_agent", "DQN")

                if ai_agent_name in ai_agents:
                    ai_agent = ai_agents[ai_agent_name]
                else:
                    if ai_agent_name == "DQN":
                        ai_agent = DQNAgent.load_latest(name=ai_agent_name, state_size=225, action_size=15, config={})
                    elif ai_agent_name == "A3C":
                        ai_agent = A3CAgent.load_latest(name=ai_agent_name, state_size=225, action_size=15, config={})
                    elif ai_agent_name == "PPO":
                        ai_agent = PPOAgent.load_latest(name=ai_agent_name, state_size=225, action_size=15, config={})
                    else:
                        ai_agent = DQNAgent.load_latest(name="DQN", state_size=225, action_size=15, config={})  # Default agent
                    ai_agents[ai_agent_name] = ai_agent

                players = [Player(name) for name in player_names]
                game = Game(players, ai_agent)
                game.start_game()
                await send_game_state(websocket)

            elif action == "make_move":
                player_index = message.get("player_index")
                card_index = message.get("card_index")
                street_name = message.get("street")

                if game and 0 <= player_index < len(game.players):
                    try:
                        card = game.players[player_index].hand[card_index]
                        street = Street[street_name]
                        game.make_move(player_index, card, street)
                        await send_game_state(websocket)

                        if game and game.players[game.current_player_index].name == "AI" and not game.get_game_state()["game_over"]:
                            ai_legal_moves = game.get_legal_moves(game.current_player_index)
                            if ai_legal_moves:
                                ai_card, ai_street = game.ai_agent.choose_move(
                                    game.players[game.current_player_index].board,
                                    game.players[game.current_player_index].hand,
                                    ai_legal_moves,
                                    None,
                                    think_time=1
                                )
                                game.make_move(game.current_player_index, ai_card, ai_street)
                                await send_game_state(websocket)

                    except (IndexError, ValueError, KeyError, AttributeError) as e:
                        logger.error(f"Invalid move: {e}")
                        await websocket.send_json({"error": str(e)})

            elif action == "load_ai_model":
                agent_name = message.get("agent_name")
                filepath = message.get("filepath")
                try:
                    if agent_name == "DQN":
                        agent = DQNAgent.load_latest(name=agent_name, state_size=225, action_size=15, config={})
                        agent.load_model(filepath)
                    elif agent_name == "A3C":
                        agent = A3CAgent.load_latest(name=agent_name, state_size=225, action_size=15, config={})
                        agent.load(filepath)
                    elif agent_name == "PPO":
                        agent = PPOAgent.load_latest(name=agent_name, state_size=225, action_size=15, config={})
                        agent.load(filepath)
                    else:
                        raise ValueError(f"Unknown AI agent: {agent_name}")
                    ai_agents[agent_name] = agent
                    await websocket.send_json({"message": f"AI model '{agent_name}' loaded successfully."})
                except Exception as e:
                    logger.error(f"Failed to load AI model: {e}")
                    await websocket.send_json({"error": str(e)})

    except WebSocketDisconnect:
        pass

async def send_game_state(websocket: WebSocket):
    if game:
        game_state = game.get_game_state()
        await websocket.send_json(game_state)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
