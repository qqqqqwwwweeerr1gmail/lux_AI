import random

random.seed(42)  # Set the seed
def bot_action():
    actions = ['move', 'stay', 'attack']
    return random.choice(actions)

# Simulate actions
for _ in range(5):
    print(bot_action())




















