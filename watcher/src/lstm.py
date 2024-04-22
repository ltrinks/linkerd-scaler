import pandas
import matplotlib.pyplot as plt
import json
import datetime
import math
import numpy as np
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA
import tensorflow as tf

# load the run
run_file = open("../../runs/long_corekube/run.json")
run = json.load(run_file)

deployment = "corekube-db"

# convert into data frame
def run_to_df(run):
    time_series_worker = [{"start": datetime.datetime.fromtimestamp(i["start_s"]), "cpu": i["metrics"][deployment]["cpu"]} for i in run]
    data_frame = pandas.DataFrame({"time": [i["start"] for i in time_series_worker], "cpu": [i["cpu"] for i in time_series_worker]})
    data_frame.index = [i["start"] for i in time_series_worker]
    data_frame.index = pandas.DatetimeIndex(data_frame.index)
    del data_frame["time"]
    return data_frame

data_frame = run_to_df(run)

# split into test and train
boundary = math.ceil((len(data_frame) * 0.75))
train = data_frame[: boundary]
test = data_frame[boundary: ]

# make input matrix
def df_to_x_y(df, window_size):
    df_as_np = df.to_numpy()
    x = []
    y = []
    for i in range(len(df_as_np) - (window_size + 60)):
        row = [[a] for a in df_as_np[i: i + window_size]]
        x.append(row)
        label = df_as_np[i + window_size + 60]
        y.append(label)
    return np.array(x), np.array(y)

x, y = df_to_x_y(train, 5)

x_val = x[-1000: ]
y_val = y[-1000: ]
print(x_val.shape)

x_test, y_test = df_to_x_y(test, 5)

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import *
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.losses import MeanSquaredError
from tensorflow.keras.metrics import RootMeanSquaredError
from tensorflow.keras.optimizers import Adam

model1 = Sequential()
model1.add(InputLayer((5, 1)))
model1.add(LSTM(140))
model1.add(Dense(8, "relu"))
model1.add(Dense(1, "linear"))
model1.summary()

cp = ModelCheckpoint(f"./{deployment}.keras", save_best_only = True)
model1.compile(loss = MeanSquaredError(), optimizer = Adam(learning_rate = 0.0001), metrics = [RootMeanSquaredError()])
model1.fit(x, y, validation_data=(x_val, y_val), epochs = 100, callbacks=[cp])

from tensorflow.keras.models import load_model

best = load_model(f"./{deployment}.keras")

train_predictions = best.predict(x_test).flatten()
train_results = pandas.DataFrame(data ={"Train Predictions": train_predictions, "Actuals": [i[0] for i in y_test]})

plt.plot(train_results["Train Predictions"], label = 'Predicted', color = "orange")
plt.plot(test.to_numpy(), label = "Actual", color = "blue")
plt.legend()
plt.savefig("./lstm.png")

