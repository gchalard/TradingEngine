from typing import Optional
from dataclasses import dataclass, field

from tradingengine.positions.position_data import PositionData
from tradingengine.enums.side import Side
from tradingengine.enums.position_status import PositionStatus



@dataclass
class Position:
    side: Side
    quantity: float
    open: PositionData
    status: PositionStatus = PositionStatus.OPEN
    close: Optional[PositionData] = field(default=None, init=False)

    @property
    def gross_pnl(self) -> float:
        side = 1 if self.side == Side.LONG else -1

        return 0 if self.status == PositionStatus.OPEN else (
            (self.close["price"] - self.open["price"]) * self.quantity * side
        )

    @property
    def net_pnl(self) -> float:
        if self.status == PositionStatus.OPEN:
            return -self.open["fees"]
        assert self.close is not None
        return self.gross_pnl - (self.close["fees"] + self.open["fees"])