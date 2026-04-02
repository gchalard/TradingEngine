from src.datasource.datasource import DataSource
from src.strategy.strategy import Strategy

def run(datasource: DataSource, strategy: Strategy) -> None:
    datasource.connect()
    while not datasource.eos:
        event = datasource.get_event()
        strategy.onEvent(event)
        strategy.next()
    strategy.onEvent({"type": "EOS"})