import unittest
from datetime import datetime

import pandas as pd
import polars as pl
import yfinance as yf

from src.datasource.dataframe import DataFrame


def _load_market_df():
    # Use live market data to avoid static fixtures.
    df = yf.download(
        tickers="AAPL",
        period="max",
        interval="1d",
        auto_adjust=False,
        progress=False,
    )
    if df is None or df.empty:
        raise unittest.SkipTest("No data returned by yfinance")
    print(df)
    df = df.reset_index()
    if isinstance(df.columns, pd.MultiIndex) and df.columns.nlevels >= 2:
        df.columns = df.columns.droplevel(-1)
    print(df)
    if hasattr(df.columns, "levels"):
        flat_columns = []
        for col in df.columns:
            if isinstance(col, tuple):
                flat = "_".join(str(part) for part in col if part)
            else:
                flat = str(col)
            flat_columns.append(flat)
        df.columns = flat_columns

    if "Date" in df.columns:
        df = df.rename(columns={"Date": "timestamp"})
    elif "Datetime" in df.columns:
        df = df.rename(columns={"Datetime": "timestamp"})
    else:
        raise unittest.SkipTest("No Date/Datetime column returned by yfinance")

    return df


class TestDataFrameDataSource(unittest.TestCase):
    def setUp(self):
        market_df = _load_market_df()
        market_df = pl.DataFrame(market_df.to_dict(orient="list"))
        print(market_df)
        self.source = DataFrame(market_df)

    def test_get_event_returns_tick_event(self):
        self.source.connect()
        event = self.source.get_event()

        self.assertEqual(event["type"], "tick")
        self.assertIsInstance(event["timestamp"], datetime)
        self.assertIsInstance(event["data"], dict)
        self.assertNotIn("timestamp", event["data"])
        self.assertGreaterEqual(len(event["data"]), 1)

    def test_stream_consumes_until_eos(self):
        self.source.connect()
        events = list(self.source.stream())

        self.assertGreater(len(events), 0)
        self.assertTrue(self.source.eos)

        i = 0
        for event in events:
            self.assertEqual(event["type"], "tick")
            if i%10 == 0:
                print(event)
            i += 1

    def test_get_event_requires_connect(self):
        with self.assertRaises(RuntimeError):
            self.source.get_event()


if __name__ == "__main__":
    unittest.main()
