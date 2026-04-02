from abc import ABC, abstractmethod
import plotly.graph_objects as go

class Broker(ABC):

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

    def plot(self) -> None:
        fig = go.Figure()

        fig.show()