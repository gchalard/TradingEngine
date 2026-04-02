from tradingengine.positions.position import Position
from tradingengine.enums.position_status import PositionStatus


class PositionsRegistry(list[Position]):

    @property
    def gross_equity_curve(self) -> list[float]:
        return [
            (position.gross_pnl) for position in self if position.status == PositionStatus.CLOSED
        ]