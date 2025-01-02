import random

# Generate a random integer between 0 and 100
random_digit = random.randint(0, 100)

print(random_digit)






import os

# Base path (absolute path of the current file)
a = r"C:\GIT\lux_AI\common\up_yml.py"

# Relative path
b = 'C:\GIT\lux_AI/mid_yml/data.yml'

# Get the directory of the base path
base_directory = os.path.dirname(a)

# Resolve the relative path with respect to the base directory
result_path = os.path.normpath(os.path.join(base_directory, b))

print(result_path)









