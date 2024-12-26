
file_abs = "C:\GIT\lux_AI\lux_ai_output_1735179921592393400.txt"
with open(file_abs, 'r') as file:
    # Write the string to the file
    steps_data = eval(file.read())
    print(steps_data)

file_name = file_abs.split('\\')[-1][:-4]+'.xlsx'

import json
import pandas as pd

dictt = {}
for i in range(len(steps_data)):
    dictt[str(i)] = [json.dumps(steps_data[i], indent=4)]

df = pd.DataFrame(dictt)
print(df)
df.to_excel(file_name,index = False)
















