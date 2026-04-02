from abc import ABC, abstractmethod
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dataclasses import dataclass, field
from datetime import datetime


from tradingengine.positions.positions_registry import PositionsRegistry

@dataclass
class Broker(ABC):

    historical_positions: PositionsRegistry = field(default_factory=PositionsRegistry)

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass


    def stats(self) -> None:
        print(f"Initial capital: {self.initial_capital}")
        print(f"Current capital: {self.current_capital}")
        print(f"Number of positions: {len(self.historical_positions)}")
        print(f"Current position: {self.current_position}")
        print(f"Gross equity curve: {self.historical_positions.gross_equity_curve}")

    def plot(self, closes: list[float] = None, timestamps: list[datetime] = None) -> None:
        fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])

        X = timestamps if timestamps is not None else list(range(len(closes)))

        fig.add_trace(
            go.Scatter(
                x=X,
                y=self.historical_positions.gross_equity_curve,
                name="Gross equity curve",
                yaxis="y1",
            ),
        )

        fig.update_layout(
            title="Gross equity curve",
            xaxis_title="Timestamp" if timestamps is not None else "Index",
            yaxis={
                "title": "Gross equity curve",
            }

        )

        if closes:
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