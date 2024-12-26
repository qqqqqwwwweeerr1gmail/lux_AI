import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import binom

# Parameters
n = 100  # number of trials
p = 0.05  # probability of success

# Calculate the probability mass function (PMF) for each possible sum (0 to 100)
k_values = np.arange(0, n + 1)
probabilities = binom.pmf(k_values, n, p)

# Print probabilities
for k, prob in zip(k_values, probabilities):
    print(f"Sum: {k}, Probability: {prob:.4f}")

# Plot the probability distribution
plt.bar(k_values, probabilities)
plt.xlabel('Sum of 100 Bernoulli Trials')
plt.ylabel('Probability')
plt.title('Probability Distribution of Sum of 100 Bernoulli Trials')
plt.show()