from typing import TypedDict
from datetime import datetime

class PositionData(TypedDict):
    price: float
    fees: float
    timestamp: datetime