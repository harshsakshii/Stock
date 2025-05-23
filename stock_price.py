# -*- coding: utf-8 -*-
"""stock_price.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ulalV3eE5vpNz7ho8ymawXZahe3DWJt3
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import torch
import torch.nn as nn


# Create sequences for time-series data
def create_sequences(data, seq_length):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i + seq_length])
        y.append(data[i + seq_length])
    return torch.tensor(np.array(X), dtype=torch.float32), torch.tensor(np.array(y), dtype=torch.float32)

# Hybrid BiGRU-LSTM Model
class HybridBiGRU_LSTM(nn.Module):
    def __init__(self, input_size, gru_hidden_size, lstm_hidden_size1, lstm_hidden_size2, dropout_rate=0.2):
        super(HybridBiGRU_LSTM, self).__init__()
        # BiGRU layer
        self.bi_gru = nn.GRU(input_size, gru_hidden_size, batch_first=True, bidirectional=True)

        # First LSTM layer
        self.lstm1 = nn.LSTM(gru_hidden_size * 2, lstm_hidden_size1, batch_first=True)

        # Second and third LSTM layers
        self.lstm2 = nn.LSTM(lstm_hidden_size1, lstm_hidden_size2, batch_first=True)
        self.lstm3 = nn.LSTM(lstm_hidden_size2, lstm_hidden_size2, batch_first=True)

        # Dropout layers
        self.dropout1 = nn.Dropout(dropout_rate)
        self.dropout2 = nn.Dropout(dropout_rate)
        self.dropout3 = nn.Dropout(dropout_rate)

        # Dense (fully connected) layer
        self.fc = nn.Linear(lstm_hidden_size2, input_size)

    def forward(self, x):
        # BiGRU layer
        x, _ = self.bi_gru(x)

        # First LSTM layer
        x, _ = self.lstm1(x)
        x = self.dropout1(x)

        # Second LSTM layer
        x, _ = self.lstm2(x)
        x = self.dropout2(x)

        # Third LSTM layer
        x, _ = self.lstm3(x)
        x = self.dropout3(x)

        # Fully connected layer (using only the last time step output)
        x = self.fc(x[:, -1, :])
        return x

# Train the Model
def train_model(model, train_loader, val_loader, criterion, optimizer, num_epochs, device="cpu"):
    model.to(device)
    history = {"train_loss": [], "val_loss": []}

    for epoch in range(num_epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        for inputs, targets in train_loader:
            inputs, targets = inputs.to(device), targets.to(device)

            # Forward pass
            outputs = model(inputs)
            loss = criterion(outputs, targets)

            # Backward pass and optimization
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)
        history["train_loss"].append(train_loss)

        # Validation phase
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                val_loss += loss.item()

        val_loss /= len(val_loader)
        history["val_loss"].append(val_loss)

        print(f"Epoch [{epoch + 1}/{num_epochs}], Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

    # Plot the loss curves
    plt.figure(figsize=(10, 6))
    plt.plot(history["train_loss"], label="Train Loss", marker='o')
    plt.plot(history["val_loss"], label="Validation Loss", marker='o')
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    plt.title("Training and Validation Loss")
    plt.legend()
    plt.grid()
    plt.show()

    return model, history

# Plot Predictions
def plot_predictions(dates, y_train, y_pred_train, y_val, y_pred_val, feature_names=None):
    # Determine number of features
    num_features = y_train.shape[1] if len(y_train.shape) > 1 else 1

    # Create subplot grid
    fig, axes = plt.subplots(num_features, 1, figsize=(16, 4*num_features), sharex=True)

    # If only one feature, convert axes to list for consistent indexing
    if num_features == 1:
        axes = [axes]

    # Ensure feature names
    if feature_names is None:
        feature_names = [f'Feature {i+1}' for i in range(num_features)]

    # Split dates for trainning and validation
    train_dates = dates[:len(y_train)]
    val_dates = dates[len(y_train):]

    # Plot for each feature
    for i in range(num_features):
        # Extract i-th feature
        train_true = y_train[:,i] if num_features > 1 else y_train
        train_pred = y_pred_train[:,i] if num_features > 1 else y_pred_train
        val_true = y_val[:,i] if num_features > 1 else y_val
        val_pred = y_pred_val[:,i] if num_features > 1 else y_pred_val

        # Plot on corresponding subplot
        axes[i].plot(train_dates, train_true, label="Train True", alpha=0.7)
        axes[i].plot(train_dates, train_pred, label="Train Pred", alpha=0.7)
        axes[i].plot(val_dates, val_true, label="Val True", alpha=0.7)
        axes[i].plot(val_dates, val_pred, label="Val Pred", alpha=0.7)

        axes[-1].xaxis.set_major_locator(mdates.DayLocator())  # Adjust for your frequency (e.g., daily, monthly)
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d-%m-%Y"))
        plt.xticks(rotation=60)  # Rotate dates for better readability

        # Set title, labels, legend, and grid
        axes[i].set_title(f"{feature_names[i]} - True vs Predicted")
        axes[i].set_ylabel("Value")
        axes[i].set_xlabel("Time")
        axes[i].legend()
        axes[i].grid()

    # Set common x-label
    axes[-1].set_xlabel("Time")

    plt.tight_layout()
    plt.show()

# Data from Yahoo Finance
# Import data from yahoo finance
#import yfinance as yf

# Define the ticker symbol
#tickerSymbol = 'MSFT'

# Get data on this ticker
#tickerData = yf.Ticker(tickerSymbol)

# Get the historical prices for this ticker
#tickerDf = tickerData.history(
 #   start='2024-01-01',
   # interval='1d'
  #  )
import pandas as pd

# Only need the open, close, low, high
data = pd.read_csv(r'/content/Book1.csv')

# Print the data
print(data.head())

# Save the data to a csv file
#data.to_csv(f'{tickerSymbol}.csv')

# Training & Prediction
import pandas as pd
# Load the dataset
data.columns = [i.lower() for i in data.columns]

data.isna().any()

data.duplicated().sum()

data['date'] = pd.to_datetime(data['date'])
data.set_index('date',inplace=True)
data.head()

# plot the data
import matplotlib.pyplot as plt

plt.figure(figsize=(15, 6))
plt.plot(data['close'])
plt.xlabel('Date')
plt.ylabel('Close Price')
plt.title('Stock Price Over Time')
plt.show()

# Function to generate feature technical indicators
def get_technical_indicators(dataset):

    # Create 7 and 21 days Moving Average
    dataset['ma7'] = dataset['close'].rolling(window = 7).mean()
    dataset['ma21'] = dataset['close'].rolling(window = 21).mean()

    # Create MACD
    dataset['12ema'] = dataset['close'].ewm(span=12).mean()
    dataset['26ema'] = dataset['close'].ewm(span=26).mean()
    dataset['MACD'] = (dataset['12ema']-dataset['26ema'])

    # Create Bollinger Bands
    dataset['20sd'] = dataset['close'].rolling(window = 20).std()
    dataset['upper_band'] = (dataset['close'].rolling(window = 20).mean()) + (dataset['20sd']*2)
    dataset['lower_band'] = (dataset['close'].rolling(window = 20).mean()) - (dataset['20sd']*2)

    # Create Exponential moving average
    dataset['ema'] = dataset['close'].ewm(com=0.5).mean()

    # Create Momentum
    dataset['momentum'] = (dataset['close']/100)-1

    return dataset

technical_data = data.copy()
technical_data = get_technical_indicators(technical_data)

def plot_technical_indicators(dataset, last_days):
    plt.figure(figsize=(16, 10), dpi=1000)

    dataset = dataset.iloc[-last_days:, :]
    x_ = range(3, dataset.shape[0])
    x_ =list(dataset.index)

    # Plot first subplot
    plt.subplot(2, 1, 1)
    plt.plot(dataset['ma7'],label='MA 7', color='g',linestyle='--')
    plt.plot(dataset['close'],label='Closing Price', color='b')
    plt.plot(dataset['ma21'],label='MA 21', color='r',linestyle='--')
    plt.plot(dataset['upper_band'],label='Upper Band', color='c')
    plt.plot(dataset['lower_band'],label='Lower Band', color='c')
    plt.fill_between(x_, dataset['lower_band'], dataset['upper_band'], alpha=0.25)
    plt.title('Technical indicators for Stock Prices - last {} days.'.format(last_days))
    plt.ylabel('USD')
    plt.legend()

    # Plot second subplot
    plt.subplot(2, 1, 2)
    plt.title('MACD')
    plt.plot(dataset['MACD'],label='MACD', linestyle='-.')
    plt.plot(dataset['momentum'],label='Momentum', color='b',linestyle='-')
    plt.hlines(15, dataset.index.min(), dataset.index.max(), colors='g', linestyles='--')
    plt.hlines(-15, dataset.index.min(), dataset.index.max(), colors='g', linestyles='--')

    plt.legend()
    plt.show()

plot_technical_indicators(technical_data, 365)

from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data)

sequence_length = 30
X, y = create_sequences(scaled_data, seq_length=sequence_length)
print(X.shape, y.shape)

# Split into training and validation datasets
split_idx = int(len(X) * 0.8)
X_train, y_train = X[:split_idx], y[:split_idx]
X_val, y_val = X[split_idx:], y[split_idx:]

# Create DataLoaders
batch_size = 32
train_dataset = TensorDataset(X_train, y_train)
val_dataset = TensorDataset(X_val, y_val)
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

# Model initialization
input_size = len(data.columns)
gru_hidden_size = 100
lstm_hidden_size1 = 100
lstm_hidden_size2 = 50
dropout_rate = 0.2

model = HybridBiGRU_LSTM(input_size, gru_hidden_size, lstm_hidden_size1, lstm_hidden_size2, dropout_rate)
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# Training
num_epochs = 20
device = "cuda" if torch.cuda.is_available() else "cpu"
print(device)
trained_model, loss_history = train_model(model, train_loader, val_loader, criterion, optimizer, num_epochs, device=device)

# save model
torch.save(trained_model.state_dict(), f'{tickerSymbol}.pt')

# Evaluate model
model.eval()
with torch.no_grad():
    y_pred_train = model(X_train.to(device)).cpu().numpy()
    y_pred_val = model(X_val.to(device)).cpu().numpy()

dates = data.index[sequence_length:]

num_points = 20
dates = dates[len(y_train)-num_points:len(y_train)+num_points]
y_train = scaler.inverse_transform(y_train)[-num_points:]
y_pred_train = scaler.inverse_transform(y_pred_train)[-num_points:]
y_val = scaler.inverse_transform(y_val)[:num_points]
y_pred_val = scaler.inverse_transform(y_pred_val)[:num_points]

print(len(dates), len(y_train), len(y_pred_train), len(y_val), len(y_pred_val))

plot_predictions(
    dates,
    y_train,
    y_pred_train,
    y_val,
    y_pred_val,
    feature_names=['open', 'close', 'high', 'low']
)

