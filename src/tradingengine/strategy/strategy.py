from abc import ABC, abstractmethod

from tradingengine.event.event import Event

class Strategy(ABC):

    @abstractmethod
    def onEvent(self, event: Event) -> None:
        pass

    @abstractmethod
    def next(self) -> None:
        pass

    @abstractmethod
    def core(self) -> None:
        pass