import numpy as np


from kaggle_environments import make
env = make("lux_ai_2021", configuration={"seed": 41, "loglevel": 1, "annotations" : True}, debug=True)

print(env.action_space)

state1 = env.reset()
print(state1)






































