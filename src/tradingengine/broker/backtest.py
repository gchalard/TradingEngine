from typing import Optional
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
    
    current_positions: Optional[dict[str, list[Position]]] = field(default=None, init=False)
    current_capital: float = field(init=False)
    _cash_events: list[tuple[datetime, float]] = field(default_factory=list, init=False)
    verbose: bool = False

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

    def add_capital(self, amount: float, timestamp: datetime) -> None:
        """Record a cash deposit (e.g. recurring investment) for portfolio history."""
        self.current_capital += amount
        self._cash_events.append((timestamp, amount))

    def _record_cash_delta(self, timestamp: datetime, delta: float) -> None:
        if delta != 0:
            self._cash_events.append((timestamp, delta))

    def _at_market(
        self,
        price: float,
        quantity: float,
        side: Side,
        timestamp: datetime,
        ticker: Optional[str] = "default",
        *,
        record_cash: bool = True,
    ) -> None:
        capital_before = self.current_capital
        if self.current_positions is None or (self.current_positions.get(ticker) is None or len(self.current_positions[ticker]) == 0):
            if self.current_positions is None:
                self.current_positions = {
                    ticker: [Position(
                        ticker=ticker,
                        side=side,
                        quantity=quantity,
                        open=PositionData(
                            price=self._compute_slippage(price),
                            fees=self._compute_fees(price, quantity, Fees.TAKER),
                            timestamp=timestamp,
                        )
                    )]
                }
            elif self.current_positions.get(ticker) is None or len(self.current_positions[ticker]) == 0:
                self.current_positions[ticker] = [Position(
                        ticker=ticker,
                        side=side,
                        quantity=quantity,
                        open=PositionData(
                            price=self._compute_slippage(price),
                            fees=self._compute_fees(price, quantity, Fees.TAKER),
                            timestamp=timestamp,
                        )
                )]
            debit = self.current_positions[ticker][-1].open["price"] * self.current_positions[ticker][-1].quantity + self.current_positions[ticker][-1].open["fees"]
            self.current_capital -= debit

            self.historical_positions.append(self.current_positions[ticker][-1])
        elif self.current_positions[ticker][-1].side == side:
            if self.verbose:
                print(f"Adding to {side.value} position")
            self.current_positions[ticker].append(
                Position(
                    ticker=ticker,
                    side=side,
                    quantity=quantity,
                    open=PositionData(
                        price=self._compute_slippage(price),
                        fees=self._compute_fees(price, quantity, Fees.TAKER),
                        timestamp=timestamp,
                    ),
                )
            )
            pos = self.current_positions[ticker][-1]
            debit = pos.open["price"] * pos.quantity + pos.open["fees"]
            self.current_capital -= debit
            self.historical_positions.append(pos)
        else:
            positions_to_close = [
                position for position in self.current_positions[ticker] if position.side != side and position.quantity <= quantity
            ]

            def quantity_to_close():
                return sum([position.quantity for position in positions_to_close])

            while quantity_to_close() > quantity:
                positions_to_close.pop()

            if self.verbose:
                if quantity_to_close() == quantity:
                    print(f"Closing {Side.LONG.value.upper() if side == Side.SHORT else Side.SHORT.value.upper()} positions")
                else:
                    print(f"Closing {Side.LONG.value.upper() if side == Side.SHORT else Side.SHORT.value.upper()} positions and opening a new {Side.LONG.value.upper() if side == Side.SHORT else Side.SHORT.value.upper()} position")
            
            for position in positions_to_close:
                closing_price = self._compute_slippage(price)
                hist_idx = self.historical_positions.index(position)
                position.close = PositionData(
                    price=closing_price,
                    fees=self._compute_fees(closing_price, position.quantity, Fees.TAKER),
                    timestamp=timestamp,
                )
                position.status = PositionStatus.CLOSED
                self.current_capital += position.net_proceeds
                self.historical_positions[hist_idx] = position
                open_idx = self.current_positions[ticker].index(position)
                self.current_positions[ticker].pop(open_idx)

            if len(self.current_positions[ticker]) == 0:
                del self.current_positions[ticker]

            if quantity_to_close() < quantity:
                q_to_open = quantity - quantity_to_close()
                self._at_market(
                    price=price,
                    quantity=q_to_open,
                    side=Side.LONG if side == Side.SHORT else Side.SHORT,
                    timestamp=timestamp,
                    ticker=ticker,
                    record_cash=False,
                )

        if record_cash:
            self._record_cash_delta(timestamp, self.current_capital - capital_before)



    def buy_at_market(self, price: float, quantity: float, timestamp: datetime, ticker: Optional[str] = "default") -> None:
        self._at_market(price, quantity, Side.LONG, timestamp, ticker)


    def sell_at_market(self, price: float, quantity: float, timestamp: datetime, ticker: Optional[str] = "default") -> None:
        self._at_market(price, quantity, Side.SHORT, timestamp, ticker)
