import os
import json
import time
import pandas as pd
import numpy as np
def profit_factor(returns, positions):
    if len(returns) < 20:
        return -1.0

    trades = positions.diff().abs().sum()
    if trades < 5:
        return -1.0

    pos_ret = returns[returns > 0].sum()
    neg_ret = returns[returns < 0].sum()

    if neg_ret == 0:
        return 10.0  # cap to avoid runaway

    return float(pos_ret / abs(neg_ret))

def diagnostic_sharpe(returns):
    if returns.std() == 0:
        return 0.0
    return float((returns.mean() / returns.std()) * (252 ** 0.5))

def run_mfi(df, boundary, period):
    df = df.copy()
    df.columns = [x.lower() for x in df.columns]

    tp = (df['high'] + df['low'] + df['close']) / 3
    mf = tp * df['volume']
    change = df['close'].diff()

    pmf = pd.Series(np.where(change > 0, mf, 0), index=df.index)
    nmf = pd.Series(np.where(change < 0, mf, 0), index=df.index)

    mfi = 100 - (100 / (1 + pmf.rolling(period).sum() /
                        nmf.rolling(period).sum().replace(0, 1e-9)))

    signal = pd.Series(0, index=df.index)
    signal.loc[mfi < (50 - boundary)] = 1
    signal.loc[mfi > (50 + boundary)] = -1

    pos = signal.shift(1).fillna(0)
    strat_ret = df['close'].pct_change() * pos

    pf = profit_factor(strat_ret.dropna(), pos)
    sr = diagnostic_sharpe(strat_ret.dropna())

    return pf, sr, float(signal.iloc[-1])

def run_mean_reversion(df, sensitivity, period):
    df = df.copy()
    df.columns = [x.lower() for x in df.columns]

    roll_max = df['high'].rolling(sensitivity).max()
    roll_min = df['low'].rolling(sensitivity).min()
    atr = (df['high'] - df['low']).rolling(period).mean()

    signal = pd.Series(0, index=df.index)
    signal.loc[df['close'] < (roll_min - 2.5 * atr)] = 1
    signal.loc[df['close'] > (roll_max + 2.5 * atr)] = -1

    pos = signal.shift(1).fillna(0)
    strat_ret = df['close'].pct_change() * pos

    pf = profit_factor(strat_ret.dropna(), pos)
    sr = diagnostic_sharpe(strat_ret.dropna())

    return pf, sr, float(signal.iloc[-1])

def run_rsi_breakout(df, rsi_period, rsi_norm_window):
    df = df.copy()
    df.columns = [x.lower() for x in df.columns]

    delta = df['close'].diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / rsi_period).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1 / rsi_period).mean()

    rsi = 100 - (100 / (1 + gain / loss.replace(0, 1e-9)))
    z = (rsi - rsi.rolling(rsi_norm_window).mean()) / \
        rsi.rolling(rsi_norm_window).std().replace(0, 1e-9)

    signal = pd.Series(0, index=df.index)
    signal.loc[z > 1.5] = 1
    signal.loc[z < -1.5] = -1

    pos = signal.shift(1).fillna(0)
    strat_ret = df['close'].pct_change() * pos

    pf = profit_factor(strat_ret.dropna(), pos)
    sr = diagnostic_sharpe(strat_ret.dropna())

    return pf, sr, float(signal.iloc[-1])

def optimize_and_execute():
    while True:
        try:
            full_df = pd.read_csv("shared_live_data.csv", index_col=0, parse_dates=True)
            df = full_df.iloc[-180:].copy()

            best_pf = -1
            best_cfg = {}

            for bdr in range(10, 35):
                for prd in range(5, 40):
                    pf, sr, _ = run_mfi(df, bdr, prd)
                    if pf > best_pf:
                        best_pf = pf
                        best_cfg = {"name": "MFI", "p1": bdr, "p2": prd, "pf": pf, "sr": sr}

            for s in range(5, 45):
                for prd in range(5, 60):
                    pf, sr, _ = run_mean_reversion(df, s, prd)
                    if pf > best_pf:
                        best_pf = pf
                        best_cfg = {"name": "MR", "p1": s, "p2": prd, "pf": pf, "sr": sr}

            for s in range(5, 45):
                for prd in range(5, 60):
                    pf, sr, _ = run_rsi_breakout(df, s, prd)
                    if pf > best_pf:
                        best_pf = pf
                        best_cfg = {"name": "RSI", "p1": s, "p2": prd, "pf": pf, "sr": sr}

            with open("strategy_config.json", "w") as f:
                json.dump(best_cfg, f)

        except Exception as e:
            print("Optimizer Error:", e)

        time.sleep(18)
