# Automatic-Stock-Trading-Demo
This is a fully automatic stock trading engine that can implemented in real trading with high performance in backtest.
# AlphaForge-HFT Introduction
AlphaForge-HFT (my repo) is a modular high-frequency trading (HFT) framework designed for intraday equity trading. The platform integrates real-time data ingestion, a rolling optimization engine with three popular trading strategies integrated, a vectorized execution layer to dynamically adapt to shifting market regimes and a dashboard that can visualize the equity curve and the trading signal exits.

## Results
We successfully capture some position signals, but not all, still making a profit virtually.
<img width="1469" height="830" alt="Screenshot 2026-01-01 at 12 27 02 AM" src="https://github.com/user-attachments/assets/ca320ad8-b2c5-47c3-8177-c78dd8b9d88a" />


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

## Optimization Objective and Contraints
Let:

- \( P_t \): close price at time \( t \)
- \( \text{pos}_t \in \{-1, 0, 1\} \): position held during interval \( t \)

### Price Return
\[
r_t = \frac{P_t - P_{t-1}}{P_{t-1}}
\]

### Strategy Return
\[
R_t = r_t \cdot \text{pos}_t
\]

### Gross Profit (GP)
\[
GP = \sum_{t : R_t > 0} R_t
\]

### Gross Loss (GL)
\[
GL = \sum_{t : R_t < 0} |R_t|
\]

### Definition
\[
\boxed{
\text{Profit Factor (PF)} = \frac{GP}{GL}
}
\]

### Practical Constraints
- If \( GL = 0 \): PF is undefined → strategy rejected
- Minimum trade count is enforced to avoid overfitting

---

### Trade Count (Stability Filter)

Let position changes indicate trades:

\[
\text{Trades} = \sum_{t} \left| \text{pos}_t - \text{pos}_{t-1} \right|
\]

Used as a constraint:
\[
\text{Trades} \ge N_{\min}
\]

# Install Info
## Prerequisites
Twelve Data API Key

Python 3.13 Intepretor

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
