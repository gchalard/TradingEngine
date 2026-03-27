from collections import deque
from dataclasses import dataclass, field

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
    momentum_200: float =field(init=False)


    def onEvent(self, event: Event) -> None:
        last_close = self.closes[-1] if len(self.closes) > 0 else event["data"]["Close"]
        self.closes.append(event["data"]["Close"])
        self.close_returns.append(event["data"]["Close"] / last_close)
        self.momentum_200 = np.prod(self.close_returns)

        if self.momentum_200 > 1:
            print("Buy")
        else:
            print("Hold")


    def next(self) -> None:
        time.sleep(1)

    def core(self) -> None:
        pass

if __name__ == "__main__":
    strategy = MockStrategy()
    source = DataFrame(_load_market_df())
    run(source, strategy)