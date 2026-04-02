from typing import Literal
from dataclasses import dataclass, field
from datetime import datetime
import random

from tradingengine.broker.broker import Broker

@dataclass
class Backtest(Broker):

    initial_capital: float = 1_000
    historical_positions: list[dict[str, float | str | datetime]] = field(default_factory=list)
    current_position: dict[str, float | str | datetime] = field(default_factory=dict)
    current_capital: float = field(init=False)

    taker_fees: float = 1e-3
    maker_fees: float = 5e-4
    slippage: float = 1e-3
    
    def __post_init__(self) -> None:
        self.current_capital = self.initial_capital

    def _compute_fees(self, price: float, quantity: float, type: Literal["taker", "maker"]) -> float:
        if type == "taker":
            return price * quantity * self.taker_fees
        elif type == "maker":
            return price * quantity * self.maker_fees
        else:
            raise ValueError(f"Invalid type: {type}")

    def _compute_slippage(self, price: float) -> float:
        """
        Compute the slippage for a given price.
        Returns the price after slippage.
        """

        return price * (1 + random.uniform(-self.slippage, self.slippage))

    def _find_position_by_datetime(self, timestamp: datetime) -> dict[str, float | str | datetime] | None:
        return next(
            (position for position in self.historical_positions if position["timestamp"] == timestamp),
            None
        )


    def connect(self) -> None:
        print("Connected to backtest broker")

    def disconnect(self) -> None:
        print("Disconnected from backtest broker")


    def buy_at_market(self, price: float, quantity: float) -> None:
        if not self.current_position:
            self.current_position = {
                "side": "buy",
                "quantity": quantity,
                "status": "open",
                "open": {
                    "price": self._compute_slippage(price),
                    "fees": self._compute_fees(price, quantity, "taker"),
                    "timestamp": datetime.now(),
                }
            }
            self.current_capital -= (self.current_position["open"]["price"] * self.current_position["quantity"] + self.current_position["open"]["fees"])
            self.historical_positions.append(self.current_position)
        elif self.current_position["side"] == "buy":
            print("Already in a buy position")
        else:
            print("Closing a sell position")
            self.current_position = {
                **self.current_position,
                "close": {
                    "price": self._compute_slippage(price),
                    "fees": self._compute_fees(price, quantity, "taker"),
                    "timestamp": datetime.now(),
                }
            }
            gross_pnl = (self.current_position["close"]["price"] - self.current_position["open"]["price"]) * self.current_position["quantity"]
            net_pnl = gross_pnl - (self.current_position["close"]["fees"] + self.current_position["open"]["fees"])
            self.current_position["status"] = "closed"
            self.current_position["gross_pnl"] = gross_pnl
            self.current_position["net_pnl"] = net_pnl
            self.current_capital += net_pnl
            self.historical_positions[-1] = self.current_position
            self.current_position = {}

    def sell_at_market(self, price: float, quantity: float) -> None:

        if not self.current_position:
            self.current_position = {
                "side": "sell",
                "quantity": quantity,
                "status": "open",
                "open": {
                    "price": self._compute_slippage(price),
                    "fees": self._compute_fees(price, quantity, "taker"),
                    "timestamp": datetime.now(),
                }
            }

            self.current_capital -= (self.current_position["open"]["price"] * self.current_position["open"]["quantity"] + self.current_position["open"]["fees"])
            self.historical_positions.append(self.current_position)
        elif self.current_position["side"] == "sell":
            print("Already in a sell position")
        else:
            print("Closing a buy position")
            self.current_position = {
                **self.current_position,
                "close": {
                    "price": self._compute_slippage(price),
                    "fees": self._compute_fees(price, quantity, "taker"),
                    "timestamp": datetime.now(),
                }
            }
            gross_pnl = (self.current_position["open"]["price"] - self.current_position["close"]["price"]) * self.current_position["quantity"]
            net_pnl = gross_pnl - (self.current_position["close"]["fees"] + self.current_position["open"]["fees"])
            self.current_position["status"] = "closed"
            self.current_position["gross_pnl"] = gross_pnl
            self.current_position["net_pnl"] = net_pnl
            self.current_capital += net_pnl
            self.historical_positions[-1] = self.current_position
            self.current_position = {}