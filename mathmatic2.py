import numpy as np
from scipy.stats import norm

prob_a = 0.51  # Example probability for A
# prob_b = 0.45  # Example probability for B
confidence_level = 0.95

# Function to calculate the number of trials needed
def calculate_trials(prob_a, prob_b, confidence_level):
    trials = 1
    while True:
        # Simulate trials for prob.a and prob.b
        success_a = np.random.binomial(trials, prob_a, 10000)
        success_b = np.random.binomial(trials, prob_b, 10000)
        prob_greater = np.mean(success_a > success_b)
        if prob_greater >= confidence_level:
            return trials
        trials += 1

n_trials = calculate_trials(prob_a, 1-prob_a, confidence_level)
print(f'Required trials: {n_trials}')