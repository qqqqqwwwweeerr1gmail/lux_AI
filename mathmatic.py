# from scipy.stats import binom
#
# n = 100  # number of trials
# p = 0.5  # probability of success (fair coin)
#
# # Calculate the probability of getting exactly k successes
# k = 50  # for example, calculate probability of 50 successes
# prob = binom.pmf(k, n, p)
# print(f'Probability of {k} successes: {prob}')
#




import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

# Number of trials and repetitions
num_trials = 100
num_repetitions = 10000

# Simulate the Bernoulli trials
sums = [np.sum(np.random.randint(0, 2, num_trials)) for _ in range(num_repetitions)]

# Count the occurrences of each sum
counts = Counter(sums)

# Calculate probabilities
probabilities = {k: v / num_repetitions for k, v in counts.items()}

# Print probabilities
for sum_value, probability in sorted(probabilities.items()):
    print(f"Sum: {sum_value}, Probability: {probability:.4f}")

# Plot the probability distribution
plt.bar(probabilities.keys(), probabilities.values())
plt.xlabel('Sum of 100 Bernoulli Trials')
plt.ylabel('Probability')
plt.title('Probability Distribution of Sum of 100 Bernoulli Trials')
plt.show()

















