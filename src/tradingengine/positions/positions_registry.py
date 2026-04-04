from tradingengine.positions.position import Position
from tradingengine.enums.position_status import PositionStatus

from datetime import datetime

import numpy as np


class PositionsRegistry(list[Position]):


    @property
    def cumulative_fees(self) -> np.ndarray:
        return np.cumsum([
            (position.open["fees"] + position.close["fees"]) for position in self if position.status == PositionStatus.CLOSED
        ])

    @property
    def gross_equity_curve(self) -> np.ndarray:
        return np.cumsum([
            (position.gross_pnl) for position in self if position.status == PositionStatus.CLOSED
        ])

    @property
    def net_equity_curve(self) -> np.ndarray:
        return self.gross_equity_curve - self.cumulative_fees

    @property
    def exit_timestamps(self) -> list[datetime]:
        return [
            position.close["timestamp"] for position in self if position.status == PositionStatus.CLOSED
        ]

    @property
    def open_timestamps(self) -> list[datetime]:
        return [
            position.open["timestamp"] for position in self if position.status == PositionStatus.CLOSED
        ]

    @property
    def open_prices(self) -> list[float]:
        return [
            position.open["price"] for position in self if position.status == PositionStatus.CLOSED
        ]

    @property
    def close_prices(self) -> list[float]:
        return [
            position.close["price"] for position in self if position.status == PositionStatus.CLOSED
        ]

    @property
    def win_rate(self) -> float:
        return np.mean([
            position.net_pnl > 0 for position in self if position.status == PositionStatus.CLOSED
        ])

    @property
    def average_win(self) -> float:
        return np.mean([
            position.net_pnl for position in self if position.net_pnl > 0 and position.status == PositionStatus.CLOSED
        ])

    @property
    def average_loss(self) -> float:
        return np.mean([
            position.net_pnl for position in self if position.net_pnl < 0 and position.status == PositionStatus.CLOSED
        ])


    @property
    def expected_return(self) -> float:
        return self.win_rate * self.average_win + (1 - self.win_rate) * self.average_loss

    @property
    def std_pnl(self) -> float:
        return np.std([
            position.net_pnl for position in self if position.status == PositionStatus.CLOSED
        ])

    @property
    def sharpe_ratio(self) -> float:
        return self.expected_return / self.std_pnl