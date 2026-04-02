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