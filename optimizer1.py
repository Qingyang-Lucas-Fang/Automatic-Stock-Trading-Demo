import os
import json
import time
import pandas as pd
import numpy as np


# ==========================================
# STRATEGY LOGIC (HARDENED)
# ==========================================

def weighted_sharpe(returns, positions, span=180):
    """Calculates a more realistic Sharpe for HFT."""
    if len(returns) < 20 or returns.std() == 0:
        return -10.0

    # Penalty: If the strategy trades less than 5 times in 180 mins, it's probably noise
    trades = positions.diff().fillna(0).abs().sum()
    if trades < 3: return -5.0

    weights = np.exp(np.linspace(-1., 0., len(returns)))
    weights /= weights.sum()

    w_mean = np.sum(returns.values * weights)
    w_var = np.sum(weights * (returns.values - w_mean) ** 2)
    w_std = np.sqrt(w_var)

    if w_std == 0: return -10.0

    # Annualized Sharpe (1-min bars)
    sharpe = (w_mean / w_std) * np.sqrt(98280)  # 252*6.5*60
    return float(np.clip(sharpe, -20, 20))  # Cap it to prevent UI breaking


def run_mfi(df, boundary, period):
    df = df.copy()
    df.columns = [x.lower() for x in df.columns]
    tp = (df['high'] + df['low'] + df['close']) / 3
    mf = tp * df['volume']
    change = df['close'].diff()

    pmf = pd.Series(np.where(change > 0, mf, 0), index=df.index)
    nmf = pd.Series(np.where(change < 0, mf, 0), index=df.index)

    mfi = 100 - (100 / (1 + (pmf.rolling(period).sum() / nmf.rolling(period).sum().replace(0, 1e-9))))

    df['pos'] = 0
    df.loc[mfi.shift(1) < (50 - boundary), 'pos'] = 1
    df.loc[mfi.shift(1) > (50 + boundary), 'pos'] = -1

    strat_ret = df['close'].pct_change() * df['pos'].shift(1)
    return weighted_sharpe(strat_ret.dropna(), df['pos']), float(df['pos'].iloc[-1])


def run_mean_reversion(df, sensitivity, period):
    df = df.copy()
    df.columns = [x.lower() for x in df.columns]
    roll_max = df['high'].rolling(sensitivity).max().shift(1)
    roll_min = df['low'].rolling(sensitivity).min().shift(1)
    atr = (df['high'] - df['low']).rolling(period).mean().shift(1)

    df['pos'] = 0
    df.loc[df['close'] < (roll_min - 2.5 * atr), 'pos'] = 1
    df.loc[df['close'] > (roll_max + 2.5 * atr), 'pos'] = -1

    strat_ret = df['close'].pct_change() * df['pos'].shift(1)
    return weighted_sharpe(strat_ret.dropna(), df['pos']), float(df['pos'].iloc[-1])


def run_rsi_breakout(df, rsi_period, rsi_norm_window):
    df = df.copy()
    df.columns = [x.lower() for x in df.columns]
    delta = df['close'].diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / rsi_period).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1 / rsi_period).mean()
    rsi = 100 - (100 / (1 + (gain / loss.replace(0, 1e-9))))
    z_score = (rsi - rsi.rolling(rsi_norm_window).mean()) / rsi.rolling(rsi_norm_window).std()

    df['pos'] = 0
    df.loc[z_score.shift(1) > 1.5, 'pos'] = 1
    df.loc[z_score.shift(1) < -1.5, 'pos'] = -1

    strat_ret = df['close'].pct_change() * df['pos'].shift(1)
    return weighted_sharpe(strat_ret.dropna(), df['pos']), float(df['pos'].iloc[-1])


# ==========================================
# OPTIMIZER & EXECUTOR
# ==========================================

def optimize_and_execute():
    equity = 100000.0
    while True:
        try:
            full_df = pd.read_csv("shared_live_data.csv", index_col=0, parse_dates=True)
            df = full_df.iloc[-180:].copy()

            best_sr = -100
            best_config = {"name": "MFI", "p1": 20, "p2": 14, "sr": 0}

            # Brute Force
            for bdr in range(10, 35, 5):
                for prd in range(10, 40, 5):
                    sr, _ = run_mfi(df, bdr, prd)
                    if sr > best_sr:
                        best_sr = sr
                        best_config = {"name": "MFI", "p1": bdr, "p2": prd, "sr": sr}

            for s in range(5, 30, 5):
                for prd in range(5, 20, 5):
                    sr, _ = run_mean_reversion(df, s, prd)
                    if sr > best_sr:
                        best_sr = sr
                        best_config = {"name": "MR", "p1": s, "p2": prd, "sr": sr}

            # Write current best config
            with open("strategy_config.json", "w") as f:
                json.dump(best_config, f)

            # Execute current signal for the Dashboard log
            if best_config['name'] == "MFI":
                _, pos = run_mfi(full_df, best_config['p1'], best_config['p2'])
            elif best_config['name'] == "MR":
                _, pos = run_mean_reversion(full_df, best_config['p1'], best_config['p2'])
            else:
                _, pos = run_rsi_breakout(full_df, 14, 30)

            # Update mock equity for Dashboard
            ret = full_df['close'].pct_change().iloc[-1] if len(full_df) > 1 else 0
            equity *= (1 + (ret * pos))

            log_data = pd.DataFrame([[full_df.index[-1], full_df['close'].iloc[-1], pos, equity]],
                                    columns=["timestamp", "price", "pos", "equity"])
            log_data.to_csv("live_trade_log.csv", mode='a', header=not os.path.exists("live_trade_log.csv"),
                            index=False)

            print(f"Cycle Complete. Best: {best_config['name']} | SR: {best_sr:.2f}")

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(12)  # Check every 12 seconds for new data (5 times/min)


if __name__ == "__main__":
    optimize_and_execute()