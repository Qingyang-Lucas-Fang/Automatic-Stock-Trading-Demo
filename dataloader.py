import time
import os
import pandas as pd
from twelvedata import TDClient

API_KEY = "API"
SYMBOL = "AAPL"

td = TDClient(apikey=API_KEY)

def data_stream():
    print("Backfilling historical data...")

    ts = td.time_series(
        symbol=SYMBOL,
        interval="1min",
        outputsize=500,
        order="ASC"
    )

    df = ts.as_pandas()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    df.to_csv("shared_live_data.csv")
    print("Backfill complete.")

    while True:
        try:
            ts = td.time_series(
                symbol=SYMBOL,
                interval="1min",
                outputsize=1,
                order="ASC"
            )

            new_tick = ts.as_pandas()
            new_tick.index = pd.to_datetime(new_tick.index)

            df_current = pd.read_csv(
                "shared_live_data.csv",
                index_col=0,
                parse_dates=True
            )

            df = pd.concat([df_current, new_tick])
            df = df[~df.index.duplicated(keep="last")]
            df = df.sort_index().iloc[-500:]

            tmp = "shared_live_data_tmp.csv"
            df.to_csv(tmp)
            os.replace(tmp, "shared_live_data.csv")

        except Exception as e:
            print("Update error:", e)

        time.sleep(10)

if __name__ == "__main__":
    data_stream()
