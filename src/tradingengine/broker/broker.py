from abc import ABC, abstractmethod
import plotly.graph_objects as go
from dataclasses import dataclass, field


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

    def plot(self) -> None:
        fig = go.Figure()

        fig.show()