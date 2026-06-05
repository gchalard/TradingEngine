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
from tradingengine.enums.position_status import PositionStatus

@dataclass
class Broker(ABC):

    initial_capital: float = 1_000
    historical_positions: PositionsRegistry = field(default_factory=PositionsRegistry)
    _cash_events: list[tuple[datetime, float]] = field(default_factory=list, init=False)
    _added_capital_events: list[tuple[datetime, float]] = field(default_factory=list, init=False)

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

    def add_capital(self, amount: float, timestamp: datetime) -> None:
        """Record a cash deposit for portfolio history and invested-capital tracking."""
        self._added_capital_events.append((timestamp, amount))
        self._record_cash_delta(timestamp, amount)
        self.current_capital += amount

    def _record_cash_delta(self, timestamp: datetime, delta: float) -> None:
        if delta != 0:
            self._cash_events.append((timestamp, delta))

    @property
    def invested_capital(self) -> UnivariateTimeseries:
        """Cumulative capital added via add_capital over time."""
        deltas_by_timestamp: dict[datetime, float] = {}
        for timestamp, amount in self._added_capital_events:
            deltas_by_timestamp[timestamp] = deltas_by_timestamp.get(timestamp, 0) + amount

        timestamps = sorted(deltas_by_timestamp.keys())
        values = np.cumsum([deltas_by_timestamp[ts] for ts in timestamps])
        return {timestamp: value for timestamp, value in zip(timestamps, values)}

    def _cash_at_timestamp(self, timestamp: datetime) -> float:
        cash = self.initial_capital
        if self._cash_events:
            for event_ts, delta in sorted(self._cash_events, key=lambda event: event[0]):
                if event_ts <= timestamp:
                    cash += delta
                else:
                    break
            return cash

        for position in self.historical_positions:
            if position.open["timestamp"] <= timestamp:
                cash -= position.open["price"] * position.quantity + position.open["fees"]
            if position.status == PositionStatus.CLOSED and position.close is not None:
                if position.close["timestamp"] <= timestamp:
                    cash += position.net_proceeds
        return cash

    def _holdings_value_at_timestamp(
        self,
        timestamp: datetime,
        asset: dict,
        held_volume_by_ticker: dict,
    ) -> float:
        tickers = [key for key in asset.keys() if key != "timestamp"]
        values_at_timestamp = []
        for ticker in tickers:
            ticker_price_t = asset[ticker]
            if ticker_price_t is None:
                continue
            if ticker not in held_volume_by_ticker:
                continue
            matched_held_volumes = [
                held_volume
                for held_volume in held_volume_by_ticker[ticker]
                if held_volume["timestamp"] <= timestamp
            ]
            vol_t = matched_held_volumes[-1]["volume"] if matched_held_volumes else 0.0
            values_at_timestamp.append(vol_t * ticker_price_t)
        return sum(values_at_timestamp)

    def portfolio_value(self, assets: MultivariateTimeseries) -> UnivariateTimeseries:
        """
        Compute net portfolio value (cash + mark-to-market holdings) at each asset timestamp.

        At timestamp t:
        portfolio_value = cash(t) + sum(held_volume_by_ticker_at_t * ticker_price_at_t)
        """
        held_volume_by_ticker = self.historical_positions.held_volume_by_ticker
        return {
            asset["timestamp"]: (
                self._cash_at_timestamp(asset["timestamp"])
                + self._holdings_value_at_timestamp(
                    asset["timestamp"],
                    asset,
                    held_volume_by_ticker,
                )
            )
            for asset in assets
        }

    @staticmethod
    def _forward_fill_timeseries(
        sparse: UnivariateTimeseries,
        timestamps: list[datetime],
    ) -> list[float]:
        if not timestamps:
            return []
        if not sparse:
            return [0.0] * len(timestamps)

        sorted_sparse = sorted(sparse.items())
        values: list[float] = []
        sparse_idx = 0
        current = 0.0
        for timestamp in timestamps:
            while sparse_idx < len(sorted_sparse) and sorted_sparse[sparse_idx][0] <= timestamp:
                current = sorted_sparse[sparse_idx][1]
                sparse_idx += 1
            values.append(current)
        return values

    @staticmethod
    def _equal_weight_benchmark(
        assets: MultivariateTimeseries,
        initial_value: float,
    ) -> UnivariateTimeseries:
        tickers: set[str] = set()
        for asset in assets:
            tickers.update(key for key in asset.keys() if key != "timestamp")

        first_prices: dict[str, float] = {}
        for asset in assets:
            for ticker in tickers:
                price = asset.get(ticker)
                if price is not None and ticker not in first_prices:
                    first_prices[ticker] = price

        benchmark: UnivariateTimeseries = {}
        for asset in assets:
            timestamp = asset["timestamp"]
            normalized = [
                asset[ticker] / first_prices[ticker]
                for ticker in tickers
                if asset.get(ticker) is not None and ticker in first_prices
            ]
            if normalized:
                benchmark[timestamp] = initial_value * sum(normalized) / len(normalized)
        return benchmark

        

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

    def plot_portfolio_value(self, assets: MultivariateTimeseries, benchmark: Optional[UnivariateTimeseries] = None) -> None:
        pf_value = self.portfolio_value(assets)
        invested_capital = self.invested_capital
        asset_timestamps = [asset["timestamp"] for asset in assets]
        invested_capital_filled = self._forward_fill_timeseries(invested_capital, asset_timestamps)
        equal_weight = self._equal_weight_benchmark(assets, self.initial_capital)

        tickers = list({
            key for asset in assets for key in asset.keys() if key != "timestamp"
        })

        first_prices: dict[str, float] = {}
        for asset in assets:
            for ticker in tickers:
                price = asset.get(ticker)
                if price is not None and ticker not in first_prices:
                    first_prices[ticker] = price

        tickers_ts = []
        for ticker in tickers:
            timestamps = [asset["timestamp"] for asset in assets if asset.get(ticker) is not None]
            if not timestamps:
                continue
            tickers_ts.append({
                "ticker": ticker,
                "timestamps": timestamps,
                "values": [
                    self.initial_capital * asset[ticker] / first_prices[ticker]
                    for asset in assets
                    if asset.get(ticker) is not None
                ],
            })

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
                x=asset_timestamps,
                y=invested_capital_filled,
                name="Invested capital",
                yaxis="y1",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=list(equal_weight.keys()),
                y=list(equal_weight.values()),
                name="Equal-weight benchmark",
                yaxis="y1",
            )
        )

        for ticker_ts in tickers_ts:
            fig.add_trace(
                go.Scatter(
                    x=ticker_ts["timestamps"],
                    y=ticker_ts["values"],
                    name=ticker_ts["ticker"],
                    line={"dash": "dash"},
                    yaxis="y2",
                )
            )

        if benchmark is not None:
            sorted_benchmark = sorted(benchmark.items())
            first_benchmark_value = sorted_benchmark[0][1]
            if first_benchmark_value != 0:
                fig.add_trace(
                    go.Scatter(
                        x=[timestamp for timestamp, _ in sorted_benchmark],
                        y=[
                            self.initial_capital * value / first_benchmark_value
                            for _, value in sorted_benchmark
                        ],
                        name="Benchmark",
                        yaxis="y1",
                    )
                )

        fig.update_layout(
            title="Portfolio value",
            xaxis_title="Timestamp",
            yaxis={"title": "Portfolio value (€)"},
            yaxis2={"title": "Ticker buy-and-hold (€)", "overlaying": "y", "side": "right"},
        )

        fig.show()