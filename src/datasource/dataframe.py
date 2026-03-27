from src.datasource.datasource import DataSource
from src.event.tick import Tick

import pandas as pd
import polars as pl

from datetime import datetime
from typing import Any, Union

class DataFrame(DataSource):
    _df: Union[pd.DataFrame, pl.DataFrame]

    def __init__(self, df: Union[pd.DataFrame, pl.DataFrame]):
        self._df = pl.from_pandas(df) if isinstance(df, pd.DataFrame) else df
        self._idx = 0
        self._connected = False

    def connect(self) -> None:
        self._connected = True
        self._idx = 0

    def disconnect(self) -> None:
        self._connected = False

    def get_event(self) -> Tick:
        if not self._connected:
            raise RuntimeError("DataFrame data source is not connected")
        if self.eos:
            raise StopIteration("End of data source reached")

        row = self._df.row(self._idx, named=True)
        self._idx += 1
        return self._row_to_event(row)

    @property
    def eos(self) -> bool:
        return self._idx >= self._df.height

    def _row_to_event(self, row: dict[str, Any]) -> Tick:
        row_data = dict(row)
        timestamp = self._extract_timestamp(row_data)
        return Tick(timestamp=timestamp, type="tick", data=row_data)

    def _extract_timestamp(self, row_data: dict[str, Any]) -> datetime:
        if "timestamp" not in row_data:
            raise ValueError("DataFrame row must contain a 'timestamp' column")

        raw_timestamp = row_data.pop("timestamp")
        if isinstance(raw_timestamp, datetime):
            return raw_timestamp

        if isinstance(raw_timestamp, str):
            return datetime.fromisoformat(raw_timestamp)

        raise TypeError("Unsupported timestamp type in DataFrame row")