from tradingengine.types import UnivariateTimeseries
from typing import Literal
from tradingengine.positions.position import Position
from tradingengine.enums.position_status import PositionStatus
from tradingengine.enums.side import Side

from datetime import datetime

import numpy as np

class PositionsRegistry(list[Position]):
    @property
    def sorted_by_timestamp(self) -> "PositionsRegistry":
        return PositionsRegistry(sorted(self, key=lambda x: x.open["timestamp"]))

    @property
    def open_positions(self) -> "PositionsRegistry":
        return PositionsRegistry([position for position in self if position.status == PositionStatus.OPEN])

    @property
    def closed_positions(self) -> "PositionsRegistry":
        return PositionsRegistry([position for position in self if position.status == PositionStatus.CLOSED])
    
    @property
    def long_positions(self) -> "PositionsRegistry":
        return PositionsRegistry([position for position in self if position.side == Side.LONG])
    
    @property
    def short_positions(self) -> "PositionsRegistry":
        return PositionsRegistry([position for position in self if position.side == Side.SHORT])

    @property
    def positions_by_ticker(self) -> dict[str, "PositionsRegistry"]:
        tickers = list(set([position.ticker if position.ticker is not None else "default" for position in self]))
        return {
            ticker: PositionsRegistry([
                position for position in self if position.ticker == ticker
            ]) for ticker in tickers
        }

    @property
    def cumulative_volume(self) -> np.array:
        return np.cumsum([
            position.quantity for position in self
        ])

    @property
    def cumulative_fees(self) -> np.ndarray:
        return np.cumsum(
            [
                (position.open["fees"] + position.close["fees"]) for position in self.closed_positions
            ] + [
                position.open["fees"] for position in self.open_positions
            ]
        )

    @property
    def gross_equity_curve(self) -> np.ndarray:
        return np.cumsum([
            (position.gross_pnl) for position in self.closed_positions
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

    @property
    def invested_capital(self) -> UnivariateTimeseries:
        sorted_positions = self.sorted_by_timestamp

        timestamps = sorted(list(set([position.open["timestamp"] for position in sorted_positions])))
        values = np.cumsum(
            [position.open["price"] * position.quantity for position in sorted_positions]
        )

        return {
            timestamp: value for timestamp, value in zip(timestamps, values)
        }


    @property
    def held_volume(self) -> list[dict[Literal["timestamp", "volume"], Literal[datetime, float]]]:
        """
        Compute the held volume at each timestamp. 
        At timestamp t:
        held_volume = sum(quantity of positions open at t)

        Returns:
            list of dictionaries with the following keys: "timestamp" and "volume", their values are the timestamp and the held volume at the timestamp respectively.
        """
        r =  [{
            "timestamp": position.open["timestamp"],
            "volume": position.quantity
        } for position in self.open_positions]

        cum_vol = np.cumsum([position.quantity for position in self.open_positions])

        return [
            {
                "timestamp": r[i]["timestamp"],
                "volume": float(cum_vol[i])
            }
            for i in range(len(cum_vol))
        ]

    @property
    def held_volume_by_ticker(self) -> dict[str, list[dict[Literal["timestamp", "volume"], Literal[datetime, float]]]]:
        return {
            ticker: registry.held_volume
            for ticker, registry in self.positions_by_ticker.items()
        }

    @property
    def portfolio_weights(self) -> dict[str, float]:
        open_positions = self.open_positions
        per_ticker = open_positions.positions_by_ticker
        per_ticker_invested_capital = {
            ticker: sum([
                position.open["price"] * position.quantity for position in positions
            ])
            for ticker, positions in per_ticker.items()
        }
        total_invested_capital = sum(per_ticker_invested_capital.values())
        
        return {
            ticker: invested_capital / total_invested_capital
            for ticker, invested_capital in per_ticker_invested_capital.items()
        }