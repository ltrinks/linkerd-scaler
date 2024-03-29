import pandas as pd
import matplotlib.pyplot as plt
import json
import sys
import math

run_file_name = sys.argv[1]
run_file = open(run_file_name)
run = json.load(run_file)

web_cpu_utilization = [i["metrics"]["web"]["cpu"] for i in run]
print(web_cpu_utilization)

ema_cpu = pd.DataFrame({"previous": web_cpu_utilization}).ewm(com=0.9).mean()["previous"].tolist()

# if the change between two values is greater than 20%, trim it to 20%
gradual_change = []
for i, value in enumerate(web_cpu_utilization):
    if i == 0:
        gradual_change.append(value)
        continue
    
    prev = gradual_change[-1]
    change = value - prev
    percent_change = abs(change) / prev
    if percent_change > 0.05:
        direction = 1
        if change < 0:
            direction = -1
        gradual_change.append(prev + (direction * prev * 0.05))
        continue
    gradual_change.append(value)


x_axis = [i for i in range(len(web_cpu_utilization))]

plt.plot(x_axis, web_cpu_utilization, label="Raw", color="blue")
plt.plot(x_axis, gradual_change, label="Gradual", color="grey")
plt.legend()

plt.show()
