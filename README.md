# Automatic-Stock-Trading-Demo
This is a fully automatic stock trading engine with high performance in backtest.
# AlphaForge-HFT: Dynamic Multi-Strategy Execution Engine Intro
AlphaForge-HFT (my repo) is a modular high-frequency trading (HFT) framework designed for intraday equity trading. The platform integrates real-time data ingestion, a rolling 8-minute optimization engine, and a vectorized execution layer to dynamically adapt to shifting market regimes.

# System Architecture
## Workers
The platform operates on a Controller-Worker architecture, decoupling data ingestion from heavy computation to ensure ultra-low latency in signal execution.

1. Data Ingestion Layer: Polls Twelve Data API at 12s intervals (5x/min) for sub-minute tick analysis.
2. Optimization Engine (The Brain): Every 8 minutes, the system performs a brute-force parameter sweep across three distinct strategies using a 180-minute lookback window with Exponentially Weighted Moving Average (EWM) weighting.
3. Execution Layer: Implements the optimal parameter set from the backtest in real-time without computational overhead at the execution stage.
4. Monitoring Interface: A Dash-based interactive dashboard visualizing equity curves and real-time position markers.

## Quant Trading Startegies Used
| Strategy | Logic | Optimization Parameters |
| :--- | :--- | :--- |
| **MFI Adaptive** | Volume-weighted momentum focusing on money flow divergence. | Boundary sensitivity & Lookback period |
| **Mean Reversion** | Volatility-adjusted bands using ATR for dynamic expansion/contraction. | Sensitivity factor & ATR Rolling window |
| **RSI Breakout** | Z-score normalized RSI to identify extreme regime shifts and momentum bursts. | RSI Period & Normalization window |

## Optimization Objective
EWM Weighted Sharpe
Unlike standard backtests, our engine uses a Weighted Sharpe Ratio. We apply a decay factor to the 180-minute lookback window to prioritize recent price action, ensuring the selected strategy is "fit for purpose" for the immediate market micro-structure.
$$Sharpe_{Weighted} = \frac{\mu_{w}}{\sigma_{w}} \times \sqrt{252 \times 6.5 \times 60}$$

# Install Info
## Prerequisites
Twelve Data API Key
Python 3.9+ Intepretor

## Installation Steps
Clone the repository:
git clone https://github.com/yourusername/AlphaForge-HFT.git
cd AlphaForge-HFT

Install dependencies:
pip install pandas numpy dash plotly twelvedata

## Execution Pipeline
To run the full suite, execute the following components in order:

Data Loader: python dataloader.py (Starts data ingestion)

Optimizer Engine: python optimizer1.py
Executor Trader: python execution1.py
Dashboard: python dashboard.py 
(Launch visualization at localhost:8050)

# Tech Stack
Language: Python 3.9

Data Science: Pandas, NumPy (Vectorized Backtesting)

Data Provider: Twelve Data API

Visualization: Plotly Dash

Inter-process Communication: File-based State Management (JSON/CSV)
