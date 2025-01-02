import random

class Random_bot:
    def __init__(self, seed):
        self.random_gen = random.Random(seed)

    def ba(self,actions = ['n', 's', 'e', 'w', 'c']):
        return self.random_gen.choice(actions)


if __name__ == '__main__':

    r_bot1 = Random_bot(seed=42)
    r_bot2 = Random_bot(seed=42)

    for _ in range(5):
        print("Bot 1 action:", r_bot1.ba())
        print("Bot 2 action:", r_bot2.ba())























