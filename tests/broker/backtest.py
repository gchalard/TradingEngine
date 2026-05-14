from datetime import datetime
from tradingengine.broker.backtest import Backtest

### No ticker

def test_buy_at_market():
    backtest = Backtest()
    initial_capital = backtest.current_capital
    initial_positions = backtest.historical_positions
    initial_positions_length = len(initial_positions)

    print(initial_capital, initial_positions_length)

    backtest.buy_at_market(100, 1, datetime.now())
    print(backtest.current_capital, len(backtest.historical_positions))
    assert len(backtest.historical_positions) == initial_positions_length + 1

def test_sell_at_market():
    backtest = Backtest()
    initial_capital = backtest.current_capital
    initial_positions = backtest.historical_positions
    initial_positions_length = len(initial_positions)
    print(initial_capital, initial_positions_length)
    backtest.sell_at_market(100, 1, datetime.now())
    print(backtest.current_capital, len(backtest.historical_positions))
    assert len(backtest.historical_positions) == initial_positions_length + 1

def test_buy_and_sell_at_market():
    backtest = Backtest(verbose=True)
    
    initial_positions = backtest.historical_positions
    initial_positions_length = len(initial_positions)
    initial_capital = backtest.current_capital

    print(initial_positions_length)
    
    backtest.buy_at_market(100, 1, datetime.now())
    print(backtest.current_positions)
    backtest.sell_at_market(100, 1, datetime.now())

    print(backtest.historical_positions)

    assert len(backtest.historical_positions) == initial_positions_length + 1
    assert backtest.current_positions.get("default") is None
    assert backtest.current_capital != initial_capital

### With ticker

def test_buy_at_market_with_ticker():
    backtest = Backtest()
    initial_capital = backtest.current_capital
    initial_positions = backtest.historical_positions
    initial_positions_length = len(initial_positions)
    print(initial_capital, initial_positions_length)
    backtest.buy_at_market(100, 1, datetime.now(), "AAPL")
    print(backtest.current_capital, len(backtest.historical_positions))
    assert len(backtest.historical_positions) == initial_positions_length + 1

def test_sell_at_market_with_ticker():
    backtest = Backtest()
    initial_capital = backtest.current_capital
    initial_positions = backtest.historical_positions
    initial_positions_length = len(initial_positions)
    print(initial_capital, initial_positions_length)
    backtest.sell_at_market(100, 1, datetime.now(), "AAPL")
    print(backtest.current_capital, len(backtest.historical_positions))
    assert len(backtest.historical_positions) == initial_positions_length + 1

## Mutiple tickers

def test_buy_multiple_tickers():
    backtest = Backtest(verbose=True)
    initial_positions = backtest.historical_positions
    initial_positions_length = len(initial_positions)
    initial_capital = backtest.current_capital
    
    print(f"Initial positions length: {initial_positions_length}")

    backtest.buy_at_market(100, 1, datetime.now(), "AAPL")
    print("Current positions:")
    print(backtest.current_positions)

    backtest.buy_at_market(100, 1, datetime.now(), "GOOG")
    print("Current positions:")
    print(backtest.current_positions)

    assert len(backtest.historical_positions) == initial_positions_length + 2
    assert backtest.current_positions.get("AAPL") is not None
    assert backtest.current_positions.get("GOOG") is not None
    assert backtest.current_capital != initial_capital

## Multiple positions

def test_multiple_positions():
    backtest = Backtest(verbose=True)

    initial_positions = backtest.historical_positions
    initial_positions_length = len(initial_positions)
    initial_capital = backtest.current_capital

    print(f"Initial positions length: {initial_positions_length}")

    backtest.buy_at_market(100, 1, datetime.now(), "AAPL")
    print("Current positions:")
    print(backtest.current_positions)

    print(f"Current capital: {backtest.current_capital}")

    backtest.buy_at_market(100, 1, datetime.now(), "AAPL")
    print("Current positions:")
    print(backtest.current_positions)

    print(f"Current capital: {backtest.current_capital}")

    assert len(backtest.historical_positions) == initial_positions_length + 2
    assert backtest.current_positions.get("AAPL") is not None
    assert len(backtest.current_positions["AAPL"]) == 2
    assert backtest.current_positions.get("GOOG") is None
    assert backtest.current_capital < initial_capital - (2 * (100 - 1e-3 * 100))