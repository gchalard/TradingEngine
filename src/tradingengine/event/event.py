from datetime import datetime
from typing import Literal, TypedDict

EventType = Literal["tick", "trade", "order"]

class Event(TypedDict):
    timestamp: datetime
    type: EventType
    data: dict