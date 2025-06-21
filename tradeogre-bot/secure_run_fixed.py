#!/usr/bin/env python3
"""
Secure TradeOgre Grid Bot - FIXED VERSION
Sells AEGS for USDT at higher prices (sell-side grid trading)
"""

import os
import sys
import time
import signal
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

from secure_tradeogre import SecureTradeOgre, APIResponse
from funcs import generate_grid, ticker_base_currency, ticker_pair_currency, get_time


@dataclass
class OrderState:
    uuid: str
    order_type: str
    price: float
    quantity: float
    market: str
    timestamp: datetime


@dataclass
class BotState:
    start_time: datetime
    total_trades: int = 0
    consecutive_failures: int = 0
    daily_pnl: float = 0.0
    emergency_stop: bool = False
    last_price: float = 0.0
    orders: List[OrderState] = None
    
    def __post_init__(self):
        if self.orders is None:
            self.orders = []


class SecureGridBot:
    """Enhanced grid trading bot with comprehensive safety features"""
    
    def __init__(self):
        self.config = self._load_config()
        self.api = SecureTradeOgre()
        self.logger = self._setup_logging()
        self.bot_state = BotState(start_time=datetime.now(timezone.utc))
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Secure Grid Bot initialized")
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        config_path = os.path.expanduser("~/.config/tradeogre/config.json")
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            print(f"Error loading configuration: {e}")
            sys.exit(1)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        logger = logging.getLogger('tradeogre_bot')
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handler with rotation
        log_file = os.path.expanduser(self.config['security']['log_file'])
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.config['security']['max_log_size'],
            backupCount=self.config['security']['log_backup_count']
        )
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
        self.bot_state.emergency_stop = True
    
    def _validate_market_conditions(self, ticker_data: Dict) -> bool:
        """Validate market conditions before trading"""
        try:
            bid = float(ticker_data['bid'])
            ask = float(ticker_data['ask'])
            price = float(ticker_data['price'])
            
            # Check for reasonable spread
            if bid > 0:
                spread = ((ask - bid) / bid) * 100
                if spread > 50:  # 50% spread threshold
                    self.logger.warning(f"Large spread detected: {spread:.2f}%")
                    return True  # Still allow trading but warn
            
            # Check for price sanity
            if price <= 0 or bid <= 0 or ask <= 0:
                self.logger.error("Invalid price data detected")
                return False
            
            # Check for extreme price movements
            if self.bot_state.last_price > 0:
                price_change = abs(price - self.bot_state.last_price) / self.bot_state.last_price
                if price_change > self.config['trading']['emergency_stop_price_deviation']:
                    self.logger.error(f"Extreme price movement detected: {price_change*100:.2f}%")
                    return False
            
            self.bot_state.last_price = price
            return True
            
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Error validating market conditions: {e}")
            return False
    
    def _get_account_balances(self) -> Optional[Dict[str, float]]:
        """Get account balances using the working bulk endpoint"""
        try:
            response = self.api.balances()
            if not response.success:
                self.logger.error(f"Failed to get balances: {response.error}")
                return None
            
            # Extract available balances
            available_balances = response.data.get('available', {})
            
            # Get the currencies we need
            base_currency = ticker_base_currency(self.config['trading']['bot_ticker'])  # AEGS
            pair_currency = ticker_pair_currency(self.config['trading']['bot_ticker'])  # USDT
            
            balances = {
                base_currency: float(available_balances.get(base_currency, 0)),
                pair_currency: float(available_balances.get(pair_currency, 0))
            }
            
            self.logger.info(f"Account balances - {base_currency}: {balances[base_currency]}, {pair_currency}: {balances[pair_currency]}")
            return balances
            
        except Exception as e:
            self.logger.error(f"Error getting account balances: {e}")
            return None
    
    def _validate_balances(self, balances: Dict[str, float], current_price: float) -> bool:
        """Validate sufficient balances for trading"""
        base_currency = ticker_base_currency(self.config['trading']['bot_ticker'])  # AEGS
        pair_currency = ticker_pair_currency(self.config['trading']['bot_ticker'])  # USDT
        
        base_available = balances.get(base_currency, 0)
        pair_available = balances.get(pair_currency, 0)
        
        # For sell-side grid trading, we need sufficient base currency (AEGS)
        required_base = self.config['trading']['bot_balance']
        
        if base_available < required_base:
            self.logger.error(f"Insufficient {base_currency} balance. Required: {required_base}, Available: {base_available}")
            return False
        
        # Check if orders will meet $1 minimum value requirement
        quantity_per_level = required_base / self.config['trading']['grid_count']
        min_order_value = quantity_per_level * current_price
        
        if min_order_value < 1.0:
            self.logger.warning(f"Order value ${min_order_value:.2f} is below $1 minimum. Consider increasing bot_balance or reducing grid_count.")
            # Calculate minimum required balance for $1 orders
            min_quantity_per_order = 1.0 / current_price
            min_total_balance = min_quantity_per_order * self.config['trading']['grid_count']
            self.logger.info(f"Minimum recommended bot_balance: {min_total_balance:.0f} {base_currency}")
        
        self.logger.info(f"Balance validation passed - {base_currency}: {base_available}, {pair_currency}: {pair_available}")
        self.logger.info(f"Order size: {quantity_per_level:.2f} {base_currency}, Value: ${min_order_value:.2f}")
        return True
    
    def _place_grid_orders(self, ticker_data: Dict, balances: Dict[str, float]) -> bool:
        """Place initial sell-side grid orders"""
        try:
            ask_price = float(ticker_data['ask'])
            base_currency = ticker_base_currency(self.config['trading']['bot_ticker'])  # AEGS
            
            # Calculate grid levels starting from current ask price + buffer
            lower_bound = ask_price + self.config['trading']['buffer']
            upper_bound = self.config['trading']['upper_bound']
            
            if upper_bound <= lower_bound:
                self.logger.error(f"Invalid bounds: upper_bound ({upper_bound}) <= lower_bound ({lower_bound})")
                return False
            
            # Generate grid levels for sell orders
            grid_levels = generate_grid(lower_bound, upper_bound, self.config['trading']['grid_count'])
            if not grid_levels:
                self.logger.error("Failed to generate grid levels")
                return False
            
            # Calculate quantity per level
            total_quantity = self.config['trading']['bot_balance']
            quantity_per_level = total_quantity / self.config['trading']['grid_count']
            
            self.logger.info(f"Placing {self.config['trading']['grid_count']} sell orders with size {quantity_per_level:.2f} each")
            self.logger.info(f"Grid range: {lower_bound:.8f} to {upper_bound:.8f} USDT")
            
            # Place sell orders at each grid level
            orders_placed = 0
            for i, price in enumerate(grid_levels):
                try:
                    order_value = quantity_per_level * price
                    
                    if self.config['trading']['dry_run']:
                        self.logger.info(f"[DRY RUN] Sell order: {quantity_per_level:.2f} {base_currency} @ {price:.8f} USDT (${order_value:.2f})")
                        orders_placed += 1
                    else:
                        # Check minimum order value
                        if order_value < 1.0:
                            self.logger.warning(f"Skipping order below $1 minimum: ${order_value:.2f}")
                            continue
                        
                        response = self.api.sell(
                            market=self.config['trading']['bot_ticker'],
                            quantity=quantity_per_level,
                            price=price
                        )
                        
                        if response.success:
                            order_uuid = response.data.get('uuid')
                            self.logger.info(f"Sell order placed: {quantity_per_level:.2f} @ {price:.8f} (${order_value:.2f}) UUID: {order_uuid}")
                            
                            # Track the order
                            order_state = OrderState(
                                uuid=order_uuid,
                                order_type='sell',
                                price=price,
                                quantity=quantity_per_level,
                                market=self.config['trading']['bot_ticker'],
                                timestamp=datetime.now(timezone.utc)
                            )
                            self.bot_state.orders.append(order_state)
                            orders_placed += 1
                        else:
                            self.logger.error(f"Failed to place sell order at {price:.8f}: {response.error}")
                            self.bot_state.consecutive_failures += 1
                            
                            if self.bot_state.consecutive_failures >= self.config['trading']['max_consecutive_failures']:
                                self.logger.error("Too many consecutive failures, stopping")
                                return False
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"Error placing order at level {i+1}: {e}")
                    continue
            
            self.logger.info(f"Successfully placed {orders_placed} orders")
            return orders_placed > 0
            
        except Exception as e:
            self.logger.error(f"Error placing grid orders: {e}")
            return False
    
    def _monitor_orders(self):
        """Monitor and manage existing orders"""
        if not self.bot_state.orders or self.config['trading']['dry_run']:
            return
        
        try:
            # Get current orders from exchange
            response = self.api.get_orders(market=self.config['trading']['bot_ticker'])
            if not response.success:
                self.logger.error(f"Failed to get orders: {response.error}")
                return
            
            active_orders = {order['uuid']: order for order in response.data}
            
            # Check our tracked orders
            for order in self.bot_state.orders[:]:  # Copy list to allow modification
                if order.uuid not in active_orders:
                    # Order was filled
                    self.logger.info(f"SELL order filled: {order.quantity:.2f} AEGS @ {order.price:.8f} USDT")
                    self.bot_state.orders.remove(order)
                    self.bot_state.total_trades += 1
            
        except Exception as e:
            self.logger.error(f"Error monitoring orders: {e}")
    
    def _check_emergency_conditions(self) -> bool:
        """Check for emergency stop conditions"""
        if self.bot_state.emergency_stop:
            return True
        
        # Check consecutive failures
        if self.bot_state.consecutive_failures >= self.config['trading']['max_consecutive_failures']:
            self.logger.error("Emergency stop: Too many consecutive failures")
            self.bot_state.emergency_stop = True
            return True
        
        # Check daily loss limit
        if self.bot_state.daily_pnl < -self.config['trading']['max_daily_loss']:
            self.logger.error(f"Emergency stop: Daily loss limit exceeded ({self.bot_state.daily_pnl})")
            self.bot_state.emergency_stop = True
            return True
        
        return False
    
    def _cleanup(self):
        """Perform cleanup operations"""
        self.logger.info("Performing cleanup...")
        
        if not self.config['trading']['dry_run'] and self.bot_state.orders:
            self.logger.info("Cancelling open orders...")
            try:
                # Cancel all orders
                response = self.api.cancel_order(uuid='all')
                if response.success:
                    self.logger.info("All orders cancelled successfully")
                else:
                    self.logger.error(f"Failed to cancel orders: {response.error}")
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")
        
        # Log final statistics
        uptime = datetime.now(timezone.utc) - self.bot_state.start_time
        self.logger.info(f"Final stats - Uptime: {uptime}, Total trades: {self.bot_state.total_trades}")
    
    def run(self):
        """Main bot execution loop"""
        try:
            self.logger.info("Starting Secure Grid Bot")
            
            # Initialize API
            if not self.api.load_key(self.config['security']['api_key_file']):
                self.logger.error("Failed to initialize API")
                return False
            
            # Test API connection
            test_response = self.api.ticker(self.config['trading']['bot_ticker'])
            if not test_response.success:
                self.logger.error(f"API connection test failed: {test_response.error}")
                return False
            
            self.logger.info("API connection established successfully")
            
            # Validate market conditions
            if not self._validate_market_conditions(test_response.data):
                self.logger.error("Market conditions validation failed")
                return False
            
            # Get and validate balances
            balances = self._get_account_balances()
            if not balances:
                self.logger.error("Failed to retrieve account balances")
                return False
            
            current_price = float(test_response.data['price'])
            if not self._validate_balances(balances, current_price):
                self.logger.error("Balance validation failed")
                return False
            
            # Place initial grid orders
            if not self._place_grid_orders(test_response.data, balances):
                self.logger.error("Failed to place initial grid orders")
                return False
            
            # Main trading loop
            self.running = True
            self.logger.info("Entering main trading loop...")
            
            while self.running and not self._check_emergency_conditions():
                try:
                    # Monitor existing orders
                    self._monitor_orders()
                    
                    # Get current market data
                    ticker_response = self.api.ticker(self.config['trading']['bot_ticker'])
                    if ticker_response.success:
                        if not self._validate_market_conditions(ticker_response.data):
                            self.logger.warning("Market conditions validation failed, continuing...")
                    else:
                        self.logger.warning(f"Failed to get ticker data: {ticker_response.error}")
                        self.bot_state.consecutive_failures += 1
                    
                    # Reset consecutive failures on success
                    if ticker_response.success:
                        self.bot_state.consecutive_failures = 0
                    
                    # Sleep between iterations
                    time.sleep(self.config['trading']['pulse_interval'])
                    
                except KeyboardInterrupt:
                    self.logger.info("Received keyboard interrupt")
                    break
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    self.bot_state.consecutive_failures += 1
                    time.sleep(5)  # Wait before retrying
            
            return True
            
        except Exception as e:
            self.logger.error(f"Critical error in bot execution: {e}")
            return False
        finally:
            self._cleanup()


def main():
    """Main entry point"""
    try:
        bot = SecureGridBot()
        success = bot.run()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
