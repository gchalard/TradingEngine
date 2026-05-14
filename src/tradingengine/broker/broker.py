from tradingengine.types import MultivariateTimeseries, UnivariateTimeseries
import warnings
from typing import Optional
from abc import ABC, abstractmethod
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from rich.table import Table
from rich import print as rprint


from tradingengine.positions.positions_registry import PositionsRegistry

@dataclass
class Broker(ABC):

    initial_capital: float = 1_000
    historical_positions: PositionsRegistry = field(default_factory=PositionsRegistry)

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass


    @property
    def returns(self) -> float:
        return (self.current_capital - self.initial_capital) / self.initial_capital * 100

    @property
    def drawdown(self) -> np.ndarray:
        peak = np.maximum.accumulate(self.historical_positions.net_equity_curve)
        return (self.historical_positions.net_equity_curve - peak) / peak * 100

    @property
    def max_drawdown(self) -> float:
        return np.min(self.drawdown)

    def portfolio_value(self, assets: MultivariateTimeseries) -> UnivariateTimeseries:
        """
        Compute the cumulative portfolio value based on the held volumes at each timestamp and the price for each ticker.
        At timestamp t:
        portfolio_value = sum(held_volume_by_ticker_at_t * ticker_price_at_t for ticker in tickers)

        Args:
            assets: list of dictionaries with the following keys: "timestamp" and ticker, their values are the timestamp and the ticker price at the timestamp respectively.
        
        Returns:
            UnivariateTimeseries with the following keys: "timestamp" and "value", their values are the timestamp and the portfolio value at the timestamp respectively.
        """

        held_volume_by_ticker = self.historical_positions.held_volume_by_ticker

        r = {}
        for asset in assets:
            ts = asset["timestamp"]
            tickers = list(set([key for key in asset.keys() if key != "timestamp"]))
            values_at_timestamp = []
            for ticker in tickers:
                matched_held_volumes = [
                    held_volume for held_volume in held_volume_by_ticker[ticker] if held_volume["timestamp"] <= ts
                ]

                vol_t = matched_held_volumes[-1]["volume"] if len(matched_held_volumes) > 0 else 0.
                val_t = vol_t * asset[ticker]
                values_at_timestamp.append(val_t)
            r[ts] = sum(values_at_timestamp)

        return r

        

    def stats(self, benchmark: Optional[list[float]] = None) -> None:

        table = Table(title="Broker stats")

        table.add_column("Metric", justify="right")
        table.add_column("Value", justify="left")

        benchmark_returns = (benchmark[-1] / benchmark[0]) - 1 if benchmark is not None else None

        table.add_row("Initial capital", f"{self.initial_capital} €")
        table.add_row("Current capital", f"{self.current_capital} €")
        table.add_row("Number of positions", f"{len(self.historical_positions)}")
        table.add_row("Current positions: \n", f"{self.current_positions}")
        table.add_row("Total fees", f"{self.historical_positions.cumulative_fees[-1]} €")
        table.add_row("Return", f"{self.returns:.2f}%")
        table.add_row("Benchmark return", f"{benchmark_returns:.2f}%" if benchmark is not None else "N/A")
        table.add_row("Global win rate", f"{self.historical_positions.win_rate:.2f}%")
        table.add_row("Long win rate", f"{self.historical_positions.long_positions.win_rate:.2f}%")
        table.add_row("Short win rate", f"{self.historical_positions.short_positions.win_rate:.2f}%")
        table.add_row("Average win", f"{self.historical_positions.average_win:.2f} €")
        table.add_row("Average loss", f"{self.historical_positions.average_loss:.2f} €")
        table.add_row("Max drawdown", f"{self.max_drawdown:.2f}%")
        table.add_row("Expected return", f"{self.historical_positions.expected_return:.2f} €")
        table.add_row("Std pnl", f"{self.historical_positions.std_pnl:.2f} €")
        table.add_row("Sharpe ratio", f"{self.historical_positions.sharpe_ratio:.2f}")

        rprint(table)

    def plot(self, closes: Optional[list[float]] = None, timestamps: Optional[list[datetime]] = None, regimes: Optional[list[float | int]] = None) -> None:

        if regimes is not None and closes is None:
            warnings.warn("regimes requires closes to be set, setting regimes to None")
            regimes = None
        
        fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])

        open_timestamps, close_timestamps = self.historical_positions.open_timestamps, self.historical_positions.exit_timestamps
        open_prices, close_prices = self.historical_positions.open_prices, self.historical_positions.close_prices

        X = (
            timestamps if timestamps is not None else 
            list(range(len(closes))) if closes is not None else 
            list(range(len(self.historical_positions.gross_equity_curve)))
        )


        fig.add_trace(
            go.Scatter(
                x=self.historical_positions.exit_timestamps,
                y=self.historical_positions.gross_equity_curve,
                name="Gross equity curve",
                yaxis="y1",
            ),
        )

        fig.add_trace(
            go.Scatter(
                x=self.historical_positions.exit_timestamps,
                y=self.historical_positions.net_equity_curve,
                name="Net equity curve",
                yaxis="y1",
            )
        )

        fig.update_layout(
            title="Equity curve vs benchmark",
            xaxis_title="Timestamp" if timestamps is not None else "Index",
            yaxis={
                "title": "Equity curve",
            }
        )

        for o_t, c_t, o_p, c_p, position in zip(open_timestamps, close_timestamps, open_prices, close_prices, self.historical_positions):
            fig.add_shape(
                type="rect",
                xref="x", yref="y2",
                x0=o_t, x1=c_t,
                y0=o_p, y1=c_p,
                fillcolor="green" if position.net_pnl > 0 else "red",
                opacity=0.25,
            )

        if closes is not None:
            fig.add_trace(
                go.Scatter(
                    x=X,
                    y=closes,
                    name="Closes",
                    mode="lines+markers",
                    marker={
                        "color": regimes,
                        "colorscale": "Viridis",
                    } if regimes is not None else None,
                    yaxis="y2",
                ),
            )

            fig.update_yaxes(
                title="Closes",
                secondary_y=True,
            )


        fig.show()

    def plot_porfolio_value(self, assets: MultivariateTimeseries, benchmark: Optional[UnivariateTimeseries] = None) -> None:
        pf_value = self.portfolio_value(assets)
        invested_capital = self.historical_positions.invested_capital

        tickers = []
        for asset in assets:
            tickers.extend([key for key in asset.keys() if key != "timestamp"])
        tickers = list(set(tickers))

        tickers_ts = []
        for ticker in tickers:
            tickers_ts.append(
                {
                    "ticker": ticker,
                    "timestamps": [asset["timestamp"] for asset in assets if asset.get(ticker) is not None],
                    "values": [asset.get(ticker) for asset in assets if asset.get(ticker) is not None],
                }
            )
        tickers_ts = sorted(tickers_ts, key=lambda x: x["timestamps"][0])

        tickers_ts = [
            {
                "ticker": ticker_ts["ticker"],
                "timestamps": [ticker_ts["timestamps"][i] for i in range(1, len(ticker_ts["timestamps"]))],
                "values": [np.log(ticker_ts["values"][i] / ticker_ts["values"][i-1]) for i in range(1, len(ticker_ts["values"]))]
            }
            for ticker_ts in tickers_ts
        ]

        fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=list(pf_value.keys()),
                y=list(pf_value.values()),
                name="Portfolio value",
                yaxis="y1",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=list(invested_capital.keys()),
                y=list(invested_capital.values()),
                name="Invested capital",
                yaxis="y1",
            )
        )

        for ticker_ts in tickers_ts:
            fig.add_trace(
                go.Scatter(
                    x=ticker_ts["timestamps"],
                    y=ticker_ts["values"],
                    name=ticker_ts["ticker"],
                    yaxis="y2",
                )
            )



        fig.update_layout(
            title="Portfolio value",
            xaxis_title="Timestamp",
            yaxis_title="Portfolio value",
        )

        fig.show()