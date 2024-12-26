








from kaggle_environments import make, evaluate

# Run a single match against a random agent
# results = evaluate("lux_ai_2021", ["simple_agent", "simple_agent"], num_episodes=1)
# results = evaluate("lux_ai_2021", ["simple_agent", "agent1_multi_.py"], num_episodes=1)
# results = evaluate("lux_ai_2021", ["agent2_jp_comesido.py", "agent1_multi_.py"], num_episodes=1)
# results = evaluate("lux_ai_2021", ["agent2_jp_comesido.py", "agent_basic.py"], num_episodes=1)
# results = evaluate("lux_ai_2021", ["agent2_jp_comesido.py", "agent2_jp_comesido.py"], num_episodes=100)
results = evaluate("lux_ai_2021", ["agent_basic_ws_1.py", "agent_basic_ws.py"], num_episodes=10)
print(results)

# results = [[110013, 30004], [50005, 30005], [100010, 40005], [30003, 30004], [70007, 100010], [70007, 80008], [80008, 50006], [30003, 30004], [70007, 70010], [40005, 70008]]

player1_win_rate = sum([1 if i[0] > i[1] else 0 for i in results])/len(results)
print(player1_win_rate)

draw_rate = sum([1 if i[0] == i[1] else 0 for i in results])/len(results)
print(draw_rate)

player2_win_rate = 1 - player1_win_rate - draw_rate
print(player2_win_rate)









