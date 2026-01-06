import time
import json
import pandas as pd
import optimizer
import os


def execution_engine():
    equity = 100.0
    last_close = None

    if not os.path.exists("trade_log.csv"):
        pd.DataFrame(columns=["timestamp", "price", "pos", "equity"]).to_csv("trade_log.csv", index=False)

    while True:
        try:
            # 1. Load Strategy Config
            with open("strategy_config.json", "r") as f:
                conf = json.load(f)

            # 2. Load Latest Data
            df = pd.read_csv("shared_live_data.csv", index_col=0, parse_dates=True)
            current_price = df['close'].iloc[-1]

            # 3. Calculate Signal based on active strategy
            if conf['name'] == "MFI":
                _, _, pos = optimizer.run_mfi(df, conf['p1'], conf['p2'])
            elif conf['name'] == "MR":
                _, _, pos = optimizer.run_mean_reversion(df, conf['p1'], conf['p2'])
            else:
                _, _, pos = optimizer.run_rsi_breakout(df, conf['p1'], conf['p2'])

            # 4. Update Equity (Simplified)
            if last_close is not None:
                returns = (current_price - last_close) / last_close
                equity *= (1 + ((returns * pos)*100))

            last_close = current_price

            # 5. Log for Dashboard
            new_log = pd.DataFrame([[df.index[-1], current_price, pos, equity]],
                                   columns=["timestamp", "price", "pos", "equity"])
            new_log.to_csv("trade_log.csv", mode='a', header=False, index=False)

            print(f"Executing {conf['name']} | Pos: {pos} | Equity: {equity:.2f}")

        except Exception as e:
            print(f"Execution Error: {e}")

        time.sleep(12)  # Matches your 5 updates per minute


if __name__ == "__main__":
    execution_engine()