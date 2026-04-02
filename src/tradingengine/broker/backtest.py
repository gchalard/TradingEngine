from typing import Literal, Optional
from dataclasses import dataclass, field
from datetime import datetime
import random

from tradingengine.broker.broker import Broker

from tradingengine.enums.fees import Fees
from tradingengine.enums.position_status import PositionStatus
from tradingengine.enums.side import Side

from tradingengine.positions.position import Position
from tradingengine.positions.position_data import PositionData

@dataclass
class Backtest(Broker):

    initial_capital: float = 1_000
    
    current_position: Optional[Position] = field(default=None, init=False)
    current_capital: float = field(init=False)

    fees: dict[Fees, float] = field(default_factory=dict)
    slippage: float = 1e-3
    
    def __post_init__(self) -> None:
        self.current_capital = self.initial_capital
        self.fees = {
            Fees.TAKER: 1e-3,
            Fees.MAKER: 5e-4,
        }

    def _compute_fees(self, price: float, quantity: float, type: Fees) -> float:
        return price * quantity * self.fees[type]

    def _compute_slippage(self, price: float) -> float:
        """
        Compute the slippage for a given price.
        Returns the price after slippage.
        """

        return price * (1 + random.uniform(-self.slippage, self.slippage))

    def connect(self) -> None:
        print("Connected to backtest broker")

    def disconnect(self) -> None:
        print("Disconnected from backtest broker")

    def _at_market(self, price: float, quantity: float, side: Side) -> None:
        if not self.current_position:
            self.current_position = Position(
                side=side,
                quantity=quantity,
                open=PositionData(
                    price=self._compute_slippage(price),
                    fees=self._compute_fees(price, quantity, Fees.TAKER),
                    timestamp=datetime.now(),
                )
            )
            self.current_capital -= (self.current_position.open["price"] * self.current_position.quantity + self.current_position.open["fees"])
            self.historical_positions.append(self.current_position)
        elif self.current_position.side == side:
            print(f"Already in a {side.value} position")
        else:
            print(f"Closing a {side.value} position")
            self.current_position.close = PositionData(
                price=self._compute_slippage(price),
                fees=self._compute_fees(price, quantity, Fees.TAKER),
                timestamp=datetime.now(),
            )
            self.current_position.status = PositionStatus.CLOSED
            self.current_capital += self.current_position.net_pnl
            self.historical_positions[-1] = self.current_position
            self.current_position = None

    def buy_at_market(self, price: float, quantity: float) -> None:
        self._at_market(price, quantity, Side.LONG)


    def sell_at_market(self, price: float, quantity: float) -> None:

        self._at_market(price, quantity, Side.SHORT)