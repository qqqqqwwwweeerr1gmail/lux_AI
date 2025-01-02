from kaggle_environments import make, evaluate

# Run a single match against a random agent
# results = evaluate("lux_ai_2021", ["simple_agent", "simple_agent"], num_episodes=1)
# results = evaluate("lux_ai_2021", ["simple_agent", "agent1_multi_.py"], num_episodes=1)
# results = evaluate("lux_ai_2021", ["agent2_jp_comesido.py", "agent1_multi_.py"], num_episodes=1)
# results = evaluate("lux_ai_2021", ["agent2_jp_comesido.py", "agent_basic.py"], num_episodes=1)
# results = evaluate("lux_ai_2021", ["agent2_jp_comesido.py", "agent2_jp_comesido.py"], num_episodes=100)
# results = evaluate("lux_ai_2021", ["agent_basic_ws_1.py", "agent_basic_ws.py"], num_episodes=10)
# results = evaluate("lux_ai_2021", ["a1231_1_wc.py", "a1231_1_w.py"], num_episodes=30)   #0.3 0.1 0.6
# results = evaluate("lux_ai_2021", ["a1231_1_wc.py", "a1231_1_c.py"], num_episodes=30)   # 0.7 0.26 0.03

race = ["a1231_1_w.py", "a1231_1_3w1c.py"]  # 0.4 0.2  0.3999    #  0.93  0.03  0.03  #  0.56  0.36  0.06    #  0.7  0.1  0.20
race = ["a1231_1_w.py", "agent2_jp_comesido.py"]  #  0.0  0.0  1.0
race = ["agent1_multi_.py", "agent2_jp_comesido.py"]
race = ["simple_agent", "a1231_1_3w1c.py"]    #  0.93  0.06  -1.3
race = ["simple_agent", "a1231_1_w.py"]   #  0.86  0.0  0.13
race = ["simple_agent", "simple_agent"]  #  0.0  1.0  0.0
race = ["simple_agent", "agent2_jp_comesido.py"]   #  0.0  0.06  0.93
agents = ["a1231_2_wr.py", "a1231_1_3w1c.py"]  #  0.16  0.03  0.8
results = evaluate("lux_ai_2021", agents, num_episodes=30)
print(results)

# results = [[110013, 30004], [50005, 30005], [100010, 40005], [30003, 30004], [70007, 100010], [70007, 80008], [80008, 50006], [30003, 30004], [70007, 70010], [40005, 70008]]

player1_win_rate = sum([1 if i[0] > i[1] else 0 for i in results])/len(results)
print(player1_win_rate)

draw_rate = sum([1 if i[0] == i[1] else 0 for i in results])/len(results)
print(draw_rate)

player2_win_rate = 1 - player1_win_rate - draw_rate
print(player2_win_rate)

print('  # ',str(player1_win_rate)[:4]+'  '+str(draw_rate)[:4]+'  '+str(player2_win_rate)[:4])







