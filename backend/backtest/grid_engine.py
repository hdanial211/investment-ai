"""
Grid Paired Orders Backtest Engine
===================================
Simulates the CURRENT live trading system (Grid Paired Orders v5.5+).
Each layer has its own individual sell. Standby cascade buys below.

Matches live_engine.py logic:
- _grid_place_layer_sell()    → sell_price = (cost / net_qty) × (1 + gap)
- _grid_update_standby_buy()  → standby = lowest_entry × (1 - gap)
- _check_grid_orders()        → fill checks per candle
- Multi-group support with new_group_gap_pct spacing

Fee Model (Hata.io):
- Taker: 0.25%  (first entry buy — reacting to signal)
- Maker: 0.00%  (pre-placed sells + standby buys)
"""

import pandas as pd
import numpy as np
import logging
import os
import sys
import math

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from features.indicators import calculate_features

logger = logging.getLogger(__name__)

# ─── Hata Exchange Fee Structure ───────────────────
TAKER_FEE_RATE = 0.0025   # 0.25%
MAKER_FEE_RATE = 0.0000   # 0.00%


def truncate_float(val, decimals):
    """Floor-truncate to N decimals (matches live hata_api.py)."""
    factor = 10 ** decimals
    return math.floor(val * factor + 1e-12) / factor


class GridBacktestEngine:
    """
    Pure-Python grid trading simulation matching live_engine.py logic.

    Processes 1-minute candles and simulates:
    - ML signal → first entry buy (taker fee)
    - Per-layer sell placement with fee recovery
    - Standby buy cascade (maker fee)
    - Multi-group concurrent positions
    - Balance / frozen_myr tracking
    """

    def __init__(self, initial_cash=1000.0, trade_amount=50.0,
                 grid_gap_pct=0.01, max_layers=5, max_groups=3,
                 new_group_gap_pct=0.02, progress_callback=None,
                 total_candles=0):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.trade_amount = trade_amount
        self.grid_gap_pct = grid_gap_pct
        self.max_layers = max_layers
        self.max_groups = max_groups
        self.new_group_gap_pct = new_group_gap_pct
        self.progress_callback = progress_callback
        self.total_candles = total_candles

        # ─── State ─────────────────────────────────
        self.groups = []
        self._next_group_id = 1
        self._next_layer_id = 1

        # ─── Tracking ──────────────────────────────
        self.completed_trades = []
        self.peak_value = initial_cash
        self.max_drawdown_pct = 0.0
        self.last_progress_pct = 0

    # ────────────────────────────────────────────────
    # Portfolio Valuation
    # ────────────────────────────────────────────────

    def _portfolio_value(self, price):
        """Total portfolio = cash + mark-to-market of all holdings."""
        holding_value = sum(
            layer['net_qty'] * price
            for group in self.groups
            for layer in group['layers']
            if layer['status'] == 'HOLDING'
        )
        return self.cash + holding_value

    def _update_drawdown(self, price):
        """Track max drawdown."""
        value = self._portfolio_value(price)
        if value > self.peak_value:
            self.peak_value = value
        if self.peak_value > 0:
            dd = (self.peak_value - value) / self.peak_value * 100
            if dd > self.max_drawdown_pct:
                self.max_drawdown_pct = dd

    # ────────────────────────────────────────────────
    # Fee Calculation (matches _extract_hata_exec_data)
    # ────────────────────────────────────────────────

    def _simulate_buy_fill(self, price, amount_myr, is_maker=False):
        """
        Simulate a BUY fill.

        Fee is deducted in COIN units (you receive less coin).
        Returns fill data dict.
        """
        fee_rate = MAKER_FEE_RATE if is_maker else TAKER_FEE_RATE
        exec_qty = amount_myr / price
        fee_qty = exec_qty * fee_rate
        net_qty = exec_qty - fee_qty
        fee_myr = fee_qty * price
        return {
            'exec_qty': exec_qty,
            'fee_qty': fee_qty,
            'net_qty': net_qty,
            'actual_cost_myr': amount_myr,
            'fee_myr': fee_myr,
            'fee_role': 'maker' if is_maker else 'taker',
        }

    def _calc_sell_price(self, actual_cost, net_qty):
        """
        sell_price = (actual_cost / net_qty) × (1 + grid_gap_pct)

        This formula automatically recovers buy fees:
        - Taker buy → net_qty < exec_qty → higher avg_entry → higher sell
        - Maker buy → net_qty == exec_qty → normal sell price
        """
        if net_qty <= 0:
            return 0
        avg_entry = actual_cost / net_qty
        return round(avg_entry * (1.0 + self.grid_gap_pct), 2)

    # ────────────────────────────────────────────────
    # Layer / Group Creation
    # ────────────────────────────────────────────────

    def _create_layer(self, entry_price, amount_myr, is_maker=False):
        """Create a HOLDING layer from a filled buy order."""
        fill = self._simulate_buy_fill(entry_price, amount_myr, is_maker)
        sell_price = self._calc_sell_price(fill['actual_cost_myr'], fill['net_qty'])

        layer_id = self._next_layer_id
        self._next_layer_id += 1

        return {
            'id': layer_id,
            'entry_price': entry_price,
            'amount_myr': amount_myr,
            'exec_qty': fill['exec_qty'],
            'fee_qty': fill['fee_qty'],
            'net_qty': fill['net_qty'],
            'actual_cost_myr': fill['actual_cost_myr'],
            'fee_myr': fill['fee_myr'],
            'fee_role': fill['fee_role'],
            'status': 'HOLDING',
            'sell_target_price': sell_price,
        }

    def _calc_standby_price(self, from_price, current_price):
        """
        Standby BUY = lowest_entry × (1 - gap_pct).
        Capped to below current market price to ensure MAKER 0%.
        """
        standby = round(from_price * (1.0 - self.grid_gap_pct), 2)
        if standby >= current_price:
            standby = round(current_price * 0.9995, 2)
        return max(standby, 0.01)  # Floor at RM0.01

    # ────────────────────────────────────────────────
    # Entry Logic (matches process_kline)
    # ────────────────────────────────────────────────

    def _try_entry(self, signal, current_price, timestamp):
        """Attempt new group entry on ML signal == 1."""
        if signal != 1:
            return

        # Max groups check
        if len(self.groups) >= self.max_groups:
            return

        # Spacing check: new group must be >= new_group_gap_pct below lowest existing
        if self.groups:
            all_entries = [
                layer['entry_price']
                for g in self.groups for layer in g['layers']
                if layer['status'] == 'HOLDING'
            ]
            if all_entries:
                lowest = min(all_entries)
                min_required = lowest * (1.0 - self.new_group_gap_pct)
                if current_price > min_required:
                    return

        # Balance check
        if self.cash < self.trade_amount:
            return

        # Entry price = 0.1% below current (matches live engine)
        entry_price = round(current_price * 0.999, 2)
        if entry_price <= 0:
            return

        # Min notional check (RM10)
        qty = self.trade_amount / entry_price
        if entry_price * qty < 10.0:
            return

        # ★ First entry is TAKER (reacting to ML signal)
        layer = self._create_layer(entry_price, self.trade_amount, is_maker=False)

        # Create new group
        group_id = self._next_group_id
        self._next_group_id += 1

        standby_price = self._calc_standby_price(entry_price, current_price)

        group = {
            'id': group_id,
            'layers': [layer],
            'standby_buy_price': standby_price,
            'has_standby': True,
        }

        self.groups.append(group)
        self.cash -= self.trade_amount

        if self.progress_callback:
            self.progress_callback({
                "type": "trade",
                "message": f"[{timestamp}] 🟢 GRID ENTRY Group#{group_id} "
                           f"at RM{entry_price:.2f} | Layer 1 | "
                           f"Sell@{layer['sell_target_price']:.2f}"
            })

    # ────────────────────────────────────────────────
    # Fill Checks (per candle)
    # ────────────────────────────────────────────────

    def _check_sell_fills(self, candle_high, current_price, timestamp):
        """Check if any HOLDING layer's sell target is reached."""
        for group in self.groups:
            layers_to_remove = []

            for layer in group['layers']:
                if layer['status'] != 'HOLDING':
                    continue
                if candle_high < layer['sell_target_price']:
                    continue

                # ★ SELL FILLED (MAKER 0% fee — pre-placed limit order)
                sell_revenue = layer['net_qty'] * layer['sell_target_price']
                buy_cost = layer['actual_cost_myr']
                pnl = sell_revenue - buy_cost

                self.cash += sell_revenue
                self.completed_trades.append({
                    'buy_cost': buy_cost,
                    'sell_revenue': sell_revenue,
                    'pnl': pnl,
                    'fee_buy': layer['fee_myr'],
                    'fee_sell': 0.0,
                })
                layers_to_remove.append(layer['id'])

                if self.progress_callback:
                    self.progress_callback({
                        "type": "trade",
                        "message": f"[{timestamp}] 🔴 SELL FILLED G#{group['id']} "
                                   f"L#{layer['id']} at RM{layer['sell_target_price']:.2f} "
                                   f"| PnL: RM{pnl:+.2f}"
                    })

            # Remove completed layers
            group['layers'] = [l for l in group['layers']
                               if l['id'] not in layers_to_remove]

            # Re-anchor standby if layers remain
            if layers_to_remove and group['layers']:
                holding = [l for l in group['layers'] if l['status'] == 'HOLDING']
                if holding:
                    lowest = min(l['entry_price'] for l in holding)
                    group['standby_buy_price'] = self._calc_standby_price(
                        lowest, current_price)
                    group['has_standby'] = len(holding) < self.max_layers
                else:
                    group['has_standby'] = False

    def _check_standby_fills(self, candle_low, current_price, timestamp):
        """Check if any group's standby buy fills (cascade trigger)."""
        for group in self.groups:
            if not group.get('has_standby'):
                continue

            standby_price = group.get('standby_buy_price', 0)
            if standby_price <= 0:
                continue

            holding_count = len([l for l in group['layers']
                                 if l['status'] == 'HOLDING'])
            if holding_count >= self.max_layers:
                group['has_standby'] = False
                continue

            if candle_low > standby_price:
                continue

            # Balance check
            if self.cash < self.trade_amount:
                continue

            # ★ STANDBY BUY FILLED (MAKER 0% — pre-placed limit order)
            layer = self._create_layer(standby_price, self.trade_amount,
                                       is_maker=True)
            group['layers'].append(layer)
            self.cash -= self.trade_amount

            if self.progress_callback:
                self.progress_callback({
                    "type": "trade",
                    "message": f"[{timestamp}] 🔵 CASCADE BUY G#{group['id']} "
                               f"L#{layer['id']} at RM{standby_price:.2f} | "
                               f"Sell@{layer['sell_target_price']:.2f}"
                })

            # Place new standby below this layer (cascade continues)
            new_holding = len([l for l in group['layers']
                               if l['status'] == 'HOLDING'])
            if new_holding < self.max_layers:
                group['standby_buy_price'] = self._calc_standby_price(
                    standby_price, current_price)
                group['has_standby'] = True
            else:
                group['has_standby'] = False

    # ────────────────────────────────────────────────
    # Main Simulation Loop
    # ────────────────────────────────────────────────

    def run(self, df, signals):
        """
        Run grid backtest simulation candle-by-candle.

        Args:
            df: DataFrame with OHLCV (index=timestamp or integer).
            signals: Array of ML signals (1=buy, 0=hold).

        Returns:
            dict: Metrics compatible with get_metrics_dict().
        """
        total = len(df)

        for i in range(total):
            row = df.iloc[i]
            price = float(row['close'])
            high = float(row['high'])
            low = float(row['low'])
            signal = int(signals[i]) if i < len(signals) else 0

            # Timestamp for logging
            if hasattr(df.index, 'strftime'):
                try:
                    timestamp = df.index[i].strftime('%Y-%m-%d %H:%M')
                except Exception:
                    timestamp = str(i)
            else:
                timestamp = str(i)

            # Progress
            if self.total_candles > 0:
                pct = int((i / self.total_candles) * 100)
                if pct > self.last_progress_pct and self.progress_callback:
                    self.progress_callback({"type": "progress", "percent": pct})
                    self.last_progress_pct = pct

            # ──── Order of Operations (matches live engine) ────
            # 1. Check sell fills first (frees cash)
            self._check_sell_fills(high, price, timestamp)

            # 2. Check standby buy fills / cascade
            self._check_standby_fills(low, price, timestamp)

            # 3. Remove empty groups (all layers sold)
            self.groups = [g for g in self.groups if g['layers']]

            # 4. Try new entry on ML signal
            self._try_entry(signal, price, timestamp)

            # 5. Track drawdown
            self._update_drawdown(price)

        return self._compute_metrics(float(df.iloc[-1]['close']))

    # ────────────────────────────────────────────────
    # Metrics
    # ────────────────────────────────────────────────

    def _compute_metrics(self, final_price):
        """Compute metrics dict compatible with dca_engine / metrics.py output."""
        final_value = self._portfolio_value(final_price)
        total_return = ((final_value - self.initial_cash) / self.initial_cash) * 100

        total_trades = len(self.completed_trades)
        won = sum(1 for t in self.completed_trades if t['pnl'] > 0)
        lost = total_trades - won
        win_rate = (won / total_trades * 100) if total_trades > 0 else 0.0

        gross_profit = sum(t['pnl'] for t in self.completed_trades if t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in self.completed_trades if t['pnl'] <= 0))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 9999.99

        net_pnl = sum(t['pnl'] for t in self.completed_trades)
        total_fees = sum(t['fee_buy'] + t['fee_sell'] for t in self.completed_trades)

        open_layers = sum(
            len([l for l in g['layers'] if l['status'] == 'HOLDING'])
            for g in self.groups
        )

        return {
            'total_return_pct': total_return,
            'max_drawdown_pct': self.max_drawdown_pct,
            'total_closed_trades': total_trades,
            'win_rate_pct': win_rate,
            'won_trades': won,
            'lost_trades': lost,
            'profit_factor': profit_factor,
            'net_pnl': net_pnl,
            'final_value': final_value,
            'total_fees': total_fees,
            'open_positions': open_layers,
            'total_groups_created': self._next_group_id - 1,
        }


# ════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════

def run_grid_backtest(csv_path, model_path, initial_cash=1000.0,
                      trade_amount=50.0, grid_gap_pct=0.01,
                      max_layers=5, max_groups=3,
                      new_group_gap_pct=0.02,
                      ai_type="xgboost", ai_threshold=0.60,
                      progress_callback=None):
    """
    Run Grid Paired Orders backtest.

    Simulates the v5.5+ live trading system with:
    - Per-layer individual sells with fee recovery
    - Standby buy cascade below lowest layer
    - Multi-group concurrent positions
    - Maker / Taker fee distinction (Hata.io)

    Args:
        csv_path:           Path to OHLCV CSV (1-min candles)
        model_path:         Path to XGBoost (.pkl) or RL (.zip) model
        initial_cash:       Starting MYR balance (default RM1000)
        trade_amount:       MYR per layer (default RM50)
        grid_gap_pct:       Grid gap % (default 0.01 = 1%)
        max_layers:         Max layers per group (default 5)
        max_groups:         Max concurrent groups (default 3)
        new_group_gap_pct:  Min gap to open new group (default 0.02 = 2%)
        ai_type:            "xgboost", "rl_lstm", or "ensemble"
        ai_threshold:       XGBoost probability threshold (default 0.60)
        progress_callback:  Optional fn(dict) for progress/trade updates

    Returns:
        dict with keys: total_return_pct, max_drawdown_pct, total_closed_trades,
                        win_rate_pct, won_trades, lost_trades, profit_factor,
                        net_pnl, final_value, total_fees, open_positions,
                        total_groups_created
    """
    logger.info(f"Preparing data and {ai_type} AI predictions for grid backtest...")

    # ─── Load Data ──────────────────────────────────
    df = pd.read_csv(csv_path)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    df_features = calculate_features(df)
    if 'timestamp' in df_features.columns:
        df_features.set_index('timestamp', inplace=True)

    # ─── Feature Columns ───────────────────────────
    bb_cols = [c for c in df_features.columns if c.startswith('BB')]
    macd_cols = [c for c in df_features.columns if c.startswith('MACD')]
    stoch_cols = [c for c in df_features.columns if c.startswith('STOCH')]
    atr_cols = [c for c in df_features.columns if c.startswith('ATR')]
    feature_cols = (['open', 'high', 'low', 'close', 'volume',
                     'EMA_9', 'EMA_21', 'EMA_Trend', 'RSI_14', 'Volume_ROC']
                    + bb_cols + macd_cols + stoch_cols + atr_cols)
    vwap_col = 'VWAP_D' if 'VWAP_D' in df_features.columns else 'VWAP'
    if vwap_col in df_features.columns:
        feature_cols.append(vwap_col)

    # ─── Generate Signals ──────────────────────────
    import joblib

    signals = np.zeros(len(df_features))

    if ai_type in ("xgboost", "ensemble"):
        logger.info("Loading XGBoost model...")
        if ai_type == "ensemble":
            xgb_path = (model_path
                        .replace("ppo_lstm", "xgboost_scalping")
                        .replace(".zip", "_1y.pkl"))
        else:
            xgb_path = model_path
        model_obj = joblib.load(xgb_path)
        X = df_features[feature_cols]
        probs = model_obj.predict_proba(X)
        signals[probs[:, 1] > ai_threshold] = 1

    if ai_type in ("rl_lstm", "ensemble"):
        logger.info("Loading RL+LSTM model...")
        try:
            from stable_baselines3 import PPO
            rl_path = (model_path if ai_type == "rl_lstm"
                       else model_path
                       .replace("xgboost_scalping", "ppo_lstm")
                       .replace("_1y.pkl", ".zip"))
            rl_model = PPO.load(rl_path.replace('.zip', ''))
            # RL signals merged via OR logic with XGBoost
            obs = df_features[feature_cols].values.astype(np.float32)
            padding = np.zeros((len(obs), 3), dtype=np.float32)
            obs = np.hstack((obs, padding))
            obs = np.nan_to_num(obs, nan=0.0, posinf=0.0, neginf=0.0)
            actions, _ = rl_model.predict(obs, deterministic=True)
            # Ensemble OR: if either XGBoost or RL says buy → buy
            signals[actions == 1] = 1
        except Exception as e:
            logger.error(f"Failed to load RL model: {e}")

    buy_count = int(np.sum(signals == 1))
    logger.info(f"Signal Counts: BUY={buy_count}, "
                f"HOLD={len(signals) - buy_count}")

    # ─── Run Simulation ───────────────────────────
    engine = GridBacktestEngine(
        initial_cash=initial_cash,
        trade_amount=trade_amount,
        grid_gap_pct=grid_gap_pct,
        max_layers=max_layers,
        max_groups=max_groups,
        new_group_gap_pct=new_group_gap_pct,
        progress_callback=progress_callback,
        total_candles=len(df_features),
    )

    logger.info(f"Starting Portfolio Value: RM {initial_cash:.2f}")
    logger.info(f"Grid Config: gap={grid_gap_pct*100:.1f}%, "
                f"max_layers={max_layers}, max_groups={max_groups}, "
                f"trade_amount=RM{trade_amount:.0f}")

    metrics = engine.run(df_features, signals)

    # ─── Print Summary ────────────────────────────
    logger.info("--- GRID BACKTEST METRICS ---")
    logger.info(f"Total Return: {metrics['total_return_pct']:.2f}%")
    logger.info(f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
    logger.info(f"Total Closed Trades: {metrics['total_closed_trades']}")
    if metrics['total_closed_trades'] > 0:
        logger.info(f"Win Rate: {metrics['win_rate_pct']:.2f}% "
                    f"({metrics['won_trades']}W / {metrics['lost_trades']}L)")
        logger.info(f"Profit Factor: {metrics['profit_factor']:.2f}")
        logger.info(f"Net PnL: RM {metrics['net_pnl']:.2f}")
        logger.info(f"Total Fees Paid: RM {metrics['total_fees']:.2f}")
    logger.info(f"Open Positions: {metrics['open_positions']} layers")
    logger.info(f"Groups Created: {metrics['total_groups_created']}")
    logger.info(f"Final Value: RM {metrics['final_value']:.2f}")
    logger.info("-----------------------------")

    return metrics


# ════════════════════════════════════════════════════
# CLI Entry Point
# ════════════════════════════════════════════════════

if __name__ == "__main__":
    import log_config

    dataset_name = sys.argv[1] if len(sys.argv) > 1 else 'ETH_USDT_1m.csv'
    coin = dataset_name.split('_')[0]
    model_name = (sys.argv[2] if len(sys.argv) > 2
                  else f"xgboost_scalping_{coin}_1y.pkl")

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    data_path = os.path.join(base_dir, 'data', dataset_name)
    model_path = os.path.join(base_dir, 'models', model_name)

    if os.path.exists(data_path) and os.path.exists(model_path):
        run_grid_backtest(data_path, model_path, initial_cash=1000.0)
    else:
        logger.error(f"Cannot find data ({data_path}) or model ({model_path})")
