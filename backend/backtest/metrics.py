import backtrader as bt
import logging

logger = logging.getLogger(__name__)

def add_analyzers(cerebro):
    """
    Add necessary analyzers to cerebro instance.
    """
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.0, annualize=True, timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

def print_metrics(strategy):
    """
    Print the metrics from the analyzers of a completed strategy.
    """
    logger.info("--- BACKTEST METRICS ---")
    
    # Returns
    rets = strategy.analyzers.returns.get_analysis()
    rtot = rets.get('rtot', 0)
    logger.info(f"Total Return: {rtot * 100:.2f}%")
    
    # Drawdown
    dd = strategy.analyzers.drawdown.get_analysis()
    max_dd = dd.get('max', {}).get('drawdown', 0)
    logger.info(f"Max Drawdown: {max_dd:.2f}%")
    
    # Sharpe
    sharpe = strategy.analyzers.sharpe.get_analysis()
    logger.info(f"Sharpe Ratio: {sharpe.get('sharperatio', 'N/A')}")
    
    # SQN (System Quality Number)
    sqn = strategy.analyzers.sqn.get_analysis()
    logger.info(f"SQN: {sqn.get('sqn', 'N/A')}")
    
    # Trade Analyzer
    trades = strategy.analyzers.trades.get_analysis()
    total_trades = trades.get('total', {}).get('closed', 0)
    logger.info(f"Total Closed Trades: {total_trades}")
    
    if total_trades > 0:
        won = trades.get('won', {}).get('total', 0)
        lost = trades.get('lost', {}).get('total', 0)
        win_rate = (won / total_trades) * 100
        logger.info(f"Win Rate: {win_rate:.2f}% ({won} W / {lost} L)")
        
        # Profit Factor
        gross_profit = trades.get('won', {}).get('pnl', {}).get('total', 0)
        gross_loss = abs(trades.get('lost', {}).get('pnl', {}).get('total', 0))
        
        profit_factor = "N/A"
        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
            logger.info(f"Profit Factor: {profit_factor:.2f}")
        else:
            logger.info("Profit Factor: INF (No losses)")
            
        pnl_net = trades.get('pnl', {}).get('net', {}).get('total', 0)
        logger.info(f"Net PnL from trades: {pnl_net:.2f}")
    else:
        logger.info("No closed trades to analyze.")
        
    logger.info("------------------------")

def get_metrics_dict(strategy):
    """
    Return the metrics as a dictionary.
    """
    metrics = {}
    
    # Returns
    rets = strategy.analyzers.returns.get_analysis()
    metrics['total_return_pct'] = rets.get('rtot', 0) * 100
    
    # Drawdown
    dd = strategy.analyzers.drawdown.get_analysis()
    metrics['max_drawdown_pct'] = dd.get('max', {}).get('drawdown', 0)
    
    # Trade Analyzer
    trades = strategy.analyzers.trades.get_analysis()
    total_trades = trades.get('total', {}).get('closed', 0)
    metrics['total_closed_trades'] = total_trades
    
    if total_trades > 0:
        won = trades.get('won', {}).get('total', 0)
        lost = trades.get('lost', {}).get('total', 0)
        metrics['win_rate_pct'] = (won / total_trades) * 100
        metrics['won_trades'] = won
        metrics['lost_trades'] = lost
        
        # Profit Factor
        gross_profit = trades.get('won', {}).get('pnl', {}).get('total', 0)
        gross_loss = abs(trades.get('lost', {}).get('pnl', {}).get('total', 0))
        metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else 9999.99
            
        metrics['net_pnl'] = trades.get('pnl', {}).get('net', {}).get('total', 0)
    else:
        metrics['win_rate_pct'] = 0.0
        metrics['won_trades'] = 0
        metrics['lost_trades'] = 0
        metrics['profit_factor'] = 0.0
        metrics['net_pnl'] = 0.0
        
    return metrics
