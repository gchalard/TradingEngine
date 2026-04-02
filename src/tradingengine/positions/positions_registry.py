from tradingengine.positions.position import Position
from tradingengine.enums.position_status import PositionStatus

from datetime import datetime


class PositionsRegistry(list[Position]):

    @property
    def gross_equity_curve(self) -> list[float]:
        return [
            (position.gross_pnl) for position in self if position.status == PositionStatus.CLOSED
        ]

    @property
    def exit_timestamps(self) -> list[datetime]:
        return [
            position.close["timestamp"] for position in self if position.status == PositionStatus.CLOSED
        ]