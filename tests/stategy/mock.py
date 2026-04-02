from collections import deque
from dataclasses import dataclass, field

from src.broker.backtest import Backtest
from src.datasource.dataframe import DataFrame
from src.event.event import Event
from src.core import run
from src.strategy.strategy import Strategy
from tests.datasource.dataframe import _load_market_df

import time

import numpy as np

@dataclass
class MockStrategy(Strategy):
    closes: deque[float] = field(default_factory=lambda: deque(maxlen=201))
    close_returns: deque[float] = field(default_factory=lambda: deque(maxlen=200))
    momentum_200: float = field(init=False)
    broker: Backtest = field(default_factory=Backtest)

    def __post_init__(self) -> None:
        self.broker.connect()


    def onEvent(self, event: Event) -> None:
        if event["type"] == "tick":
            self.onTick(event)
        
        elif event["type"] == "EOS":
            self.onEOS()

    def onTick(self, event: Event) -> None:
        last_close = self.closes[-1] if len(self.closes) > 0 else event["data"]["Close"]
        self.closes.append(event["data"]["Close"])
        self.close_returns.append(event["data"]["Close"] / last_close)
        self.momentum_200 = np.prod(self.close_returns)

        if self.momentum_200 > 1:
            close = event["data"]["Close"]
            self.broker.buy_at_market(close, 1.0)
        elif len(self.broker.current_position) > 0:
            self.broker.sell_at_market(event["data"]["Close"], 1.0)
        else:
            pass

    def onEOS(self) -> None:
        self.broker.stats()
        self.broker.disconnect()

    def next(self) -> None:
        pass

    def core(self) -> None:
        pass

if __name__ == "__main__":
    strategy = MockStrategy()
    source = DataFrame(_load_market_df())
    run(source, strategy)