from abc import ABC, abstractmethod
from src.event.event import Event


class DataSource(ABC):
    
    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def get_event(self) -> Event:
        pass

    @property
    @abstractmethod
    def eos(self) -> bool:
        pass

    def stream(self):
        while not self.eos:
            event = self.get_event()
            yield event
