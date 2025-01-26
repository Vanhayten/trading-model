import click
from src.application.trading_service import TradingService
from src.application.backtesting_service import BacktestingService

@click.group()
def cli():
    pass

@cli.command()
def run_live():
    trading_service = TradingService()
    trading_service.run()

@cli.command()
def run_backtest():
    backtesting_service = BacktestingService()
    results = backtesting_service.run_backtest()
    backtesting_service.analyze_results(results)

if __name__ == '__main__':
    cli()