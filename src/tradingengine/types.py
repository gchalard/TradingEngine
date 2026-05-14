from datetime import datetime
from typing import List, Literal, Dict

MultivariateTimepoint = Dict[Literal["timestamp", str], Literal[datetime, float]]

UnivariateTimeseries = Dict[datetime, float]
MultivariateTimeseries = List[MultivariateTimepoint]