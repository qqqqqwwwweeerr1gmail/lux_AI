import random


def bot_action():
  """
  This function defines the bot's action based on the provided seed.

  Args:
    seed: The seed value for the random number generator.

  Returns:
    The bot's action (e.g., 'rock', 'paper', 'scissors').
  """


  actions = ['a', 'b', 'c', 'd', 'e']
  return random.choice(actions)

# Example usage:
seed_value = 42  # Replace with your desired seed value
random.seed(seed_value)
bot1_action = bot_action()
bot2_action = bot_action()

for i in range(10):
    print(f"Bot 1 action: {bot1_action}")
    print(f"Bot 2 action: {bot2_action}")























