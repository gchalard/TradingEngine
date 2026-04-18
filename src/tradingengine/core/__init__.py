from typing import Any, Optional
from datetime import datetime

from tradingengine.datasource.datasource import DataSource
from tradingengine.strategy.strategy import Strategy


def run(
    datasource: DataSource,
    strategy: Strategy,
    closes: Optional[list[float]] = None,
    timestamps: Optional[list[datetime]] = None,
    regimes: Optional[list[float | int]] = None,
    plot: bool = True,
    **kwargs: Any
) -> None:
    datasource.connect()
    while not datasource.eos:
        event = datasource.get_event()
        strategy.onEvent(event)
        strategy.next()
    strategy.onEvent({"type": "EOS", **kwargs})

    broker = getattr(strategy, "broker", None)
    if broker is not None and plot and (
        closes is not None or timestamps is not None or regimes is not None
    ):
        broker.plot(closes=closes, timestamps=timestamps, regimes=regimes)