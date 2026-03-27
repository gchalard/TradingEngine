from src.event.event import Event, EventType
from datetime import datetime
from typing import Literal, Optional, TypedDict

class TickData(TypedDict):
    symbol: str
    price: float
    volume: Optional[float] = None
    type: Literal["Open", "High", "Low", "Close", ]


class Tick(Event):
    timestamp: datetime
    type: EventType = "tick"
    data: TickData