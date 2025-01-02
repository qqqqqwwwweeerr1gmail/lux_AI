import random

class Bot:
    def __init__(self, seed):
        self.random_gen = random.Random(seed)

    def bot_action(self):
        actions = ['move', 'stay', 'attack']
        return self.random_gen.choice(actions)

bot1 = Bot(seed=42)
bot2 = Bot(seed=42)

# for _ in range(5):
#     print("Bot 1 action:", bot1.bot_action())
#     print("Bot 2 action:", bot2.bot_action())

for _ in range(100_000_000):
    if bot1.bot_action() != bot2.bot_action():
        print('un :', _)

print('a')












