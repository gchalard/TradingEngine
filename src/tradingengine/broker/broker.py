from abc import ABC, abstractmethod
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dataclasses import dataclass, field
from datetime import datetime

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

    def stats(self) -> None:

        table = Table(title="Broker stats")

        table.add_column("Metric", justify="right")
        table.add_column("Value", justify="left")

        table.add_row("Initial capital", f"{self.initial_capital} €")
        table.add_row("Current capital", f"{self.current_capital} €")
        table.add_row("Number of positions", f"{len(self.historical_positions)}")
        table.add_row("Current position", f"{self.current_position}")
        table.add_row("Total fees", f"{self.historical_positions.cumulative_fees[-1]} €")
        table.add_row("Return", f"{self.returns:.2f}%")
        table.add_row("Win rate", f"{self.historical_positions.win_rate:.2f}%")
        table.add_row("Average win", f"{self.historical_positions.average_win:.2f} €")
        table.add_row("Average loss", f"{self.historical_positions.average_loss:.2f} €")
        table.add_row("Expected return", f"{self.historical_positions.expected_return:.2f} €")
        table.add_row("Std pnl", f"{self.historical_positions.std_pnl:.2f} €")
        table.add_row("Sharpe ratio", f"{self.historical_positions.sharpe_ratio:.2f}")

        rprint(table)

    def plot(self, closes: list[float] = None, timestamps: list[datetime] = None) -> None:
        fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])

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

        if closes is not None:
            fig.add_trace(
                go.Scatter(
                    x=X,
                    y=closes,
                    name="Closes",
                    yaxis="y2",
                ),
            )

            fig.update_yaxes(
                title="Closes",
                secondary_y=True,
            )


        fig.show()