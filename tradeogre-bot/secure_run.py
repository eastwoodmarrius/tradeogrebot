#!/usr/bin/env python3
"""
Secure TradeOgre Grid Bot with enhanced safety features
"""

import os
import sys
import time
import signal
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from config import ConfigManager, TradingConfig
from secure_tradeogre import SecureTradeOgre, APIResponse
from funcs import generate_grid, ticker_base_currency, ticker_pair_currency, get_time


@dataclass
class OrderState:
    """Track order state"""
    uuid: str
    order_type: str  # 'buy' or 'sell'
    price: float
    quantity: float
    market: str
    timestamp: datetime


@dataclass
class BotState:
    """Track bot state and statistics"""
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
    """Secure grid trading bot with comprehensive safety features"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_manager = ConfigManager(config_file)
        self.config_manager.load_config()
        
        if not self.config_manager.validate_config():
            raise ValueError("Invalid configuration")
        
        self.trading_config = self.config_manager.trading_config
        self.security_config = self.config_manager.security_config
        self.logger = self.config_manager.logger
        
        # Initialize API client
        self.api = SecureTradeOgre()
        
        # Bot state
        self.bot_state = BotState(start_time=datetime.utcnow())
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Secure Grid Bot initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    def initialize_api(self) -> bool:
        """Initialize API connection with credentials"""
        try:
            api_key, api_secret = self.config_manager.get_api_credentials()
            self.api.key = api_key
            self.api.secret = api_secret
            
            # Test connection
            if not self.api.get_connection_status():
                self.logger.error("Failed to connect to TradeOgre API")
                return False
            
            self.logger.info("API connection established successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize API: {e}")
            return False
    
    def validate_market_conditions(self) -> bool:
        """Validate market conditions before starting"""
        try:
            # Check if market exists
            ticker_response = self.api.ticker(self.trading_config.bot_ticker)
            if not ticker_response.success:
                self.logger.error(f"Market {self.trading_config.bot_ticker} not found")
                return False
            
            ticker_data = ticker_response.data
            current_price = float(ticker_data['price'])
            ask_price = float(ticker_data['ask'])
            bid_price = float(ticker_data['bid'])
            
            self.bot_state.last_price = current_price
            
            # Validate price bounds
            lower_bound = ask_price + self.trading_config.buffer
            if self.trading_config.upper_bound <= lower_bound:
                self.logger.error(f"Upper bound ({self.trading_config.upper_bound}) must be greater than lower bound ({lower_bound})")
                return False
            
            # Check spread
            spread = (ask_price - bid_price) / bid_price * 100
            if spread > 10:  # 10% spread warning
                self.logger.warning(f"Large spread detected: {spread:.2f}%")
            
            # Check balances
            base_currency = ticker_base_currency(self.trading_config.bot_ticker)
            pair_currency = ticker_pair_currency(self.trading_config.bot_ticker)
            
            base_balance_response = self.api.balance(base_currency)
            pair_balance_response = self.api.balance(pair_currency)
            
            if not base_balance_response.success or not pair_balance_response.success:
                self.logger.error("Failed to retrieve account balances")
                return False
            
            base_available = float(base_balance_response.data.get('available', 0))
            pair_available = float(pair_balance_response.data.get('available', 0))
            
            self.logger.info(f"Account balances - {base_currency}: {base_available}, {pair_currency}: {pair_available}")
            
            # Check if we have enough balance
            if pair_available < self.trading_config.bot_balance:
                self.logger.error(f"Insufficient {pair_currency} balance. Required: {self.trading_config.bot_balance}, Available: {pair_available}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating market conditions: {e}")
            return False
    
    def place_initial_grid(self) -> bool:
        """Place initial grid orders"""
        try:
            # Get current market data
            ticker_response = self.api.ticker(self.trading_config.bot_ticker)
            if not ticker_response.success:
                return False
            
            ask_price = float(ticker_response.data['ask'])
            lower_bound = ask_price + self.trading_config.buffer
            
            # Generate grid levels
            grid_levels = generate_grid(
                lower_bound, 
                self.trading_config.upper_bound, 
                self.trading_config.grid_count
            )
            
            if not grid_levels:
                self.logger.error("Failed to generate grid levels")
                return False
            
            trade_size = self.trading_config.bot_balance / self.trading_config.grid_count
            
            self.logger.info(f"Placing {len(grid_levels)} sell orders with size {trade_size} each")
            
            # Place sell orders
            for i, price in enumerate(grid_levels):
                if not self.running:
                    break
                
                if self.trading_config.dry_run:
                    # Simulate order placement
                    fake_uuid = f"dry-run-{i:04d}-{int(time.time())}"
                    order_state = OrderState(
                        uuid=fake_uuid,
                        order_type='sell',
                        price=price,
                        quantity=trade_size,
                        market=self.trading_config.bot_ticker,
                        timestamp=datetime.utcnow()
                    )
                    self.bot_state.orders.append(order_state)
                    self.logger.info(f"[DRY RUN] Sell order: {trade_size} @ {price}")
                else:
                    # Place real order
                    response = self.api.sell(self.trading_config.bot_ticker, trade_size, price)
                    if response.success:
                        order_state = OrderState(
                            uuid=response.data['uuid'],
                            order_type='sell',
                            price=price,
                            quantity=trade_size,
                            market=self.trading_config.bot_ticker,
                            timestamp=datetime.utcnow()
                        )
                        self.bot_state.orders.append(order_state)
                        self.logger.info(f"Sell order placed: {trade_size} @ {price} (UUID: {response.data['uuid']})")
                    else:
                        self.logger.error(f"Failed to place sell order: {response.error}")
                        self.bot_state.consecutive_failures += 1
                        if self.bot_state.consecutive_failures >= self.trading_config.max_consecutive_failures:
                            self.logger.error("Too many consecutive failures, stopping")
                            return False
                
                # Rate limiting
                time.sleep(0.5)
            
            self.logger.info(f"Initial grid placement completed. {len(self.bot_state.orders)} orders placed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error placing initial grid: {e}")
            return False
    
    def check_emergency_conditions(self) -> bool:
        """Check for emergency stop conditions"""
        try:
            # Check price deviation
            ticker_response = self.api.ticker(self.trading_config.bot_ticker)
            if ticker_response.success:
                current_price = float(ticker_response.data['price'])
                if self.bot_state.last_price > 0:
                    price_change = abs(current_price - self.bot_state.last_price) / self.bot_state.last_price
                    if price_change > self.trading_config.emergency_stop_price_deviation:
                        self.logger.error(f"Emergency stop: Price deviation {price_change:.2%} exceeds threshold")
                        return True
                
                self.bot_state.last_price = current_price
            
            # Check consecutive failures
            if self.bot_state.consecutive_failures >= self.trading_config.max_consecutive_failures:
                self.logger.error(f"Emergency stop: {self.bot_state.consecutive_failures} consecutive failures")
                return True
            
            # Check daily loss limit
            if self.bot_state.daily_pnl < -self.trading_config.max_daily_loss:
                self.logger.error(f"Emergency stop: Daily loss {self.bot_state.daily_pnl} exceeds limit")
                return True
            
            # Check maximum position
            total_position = sum(order.quantity for order in self.bot_state.orders if order.order_type == 'sell')
            if total_position > self.trading_config.max_position:
                self.logger.error(f"Emergency stop: Position {total_position} exceeds maximum")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking emergency conditions: {e}")
            return True  # Err on the side of caution
    
    def update_orders(self) -> bool:
        """Update order states and handle fills"""
        try:
            if self.trading_config.dry_run:
                # Simulate order fills for dry run
                return self._simulate_order_fills()
            
            # Get current open orders from exchange
            orders_response = self.api.orders(self.trading_config.bot_ticker)
            if not orders_response.success:
                self.logger.error(f"Failed to get open orders: {orders_response.error}")
                self.bot_state.consecutive_failures += 1
                return False
            
            open_order_uuids = {order['uuid'] for order in orders_response.data}
            grid_spacing = (self.trading_config.upper_bound - 
                          (float(self.api.ticker(self.trading_config.bot_ticker).data['ask']) + 
                           self.trading_config.buffer)) / self.trading_config.grid_count
            
            # Check for filled orders
            for i, order in enumerate(self.bot_state.orders):
                if order.uuid not in open_order_uuids:
                    self.logger.info(f"Order filled: {order.order_type} @ {order.price}")
                    
                    # Place opposite order
                    if order.order_type == 'sell':
                        new_price = order.price - grid_spacing
                        response = self.api.buy(order.market, order.quantity, new_price)
                        new_type = 'buy'
                    else:
                        new_price = order.price + grid_spacing
                        response = self.api.sell(order.market, order.quantity, new_price)
                        new_type = 'sell'
                    
                    if response.success:
                        # Update order state
                        self.bot_state.orders[i] = OrderState(
                            uuid=response.data['uuid'],
                            order_type=new_type,
                            price=new_price,
                            quantity=order.quantity,
                            market=order.market,
                            timestamp=datetime.utcnow()
                        )
                        
                        self.bot_state.total_trades += 1
                        self.bot_state.consecutive_failures = 0
                        self.logger.info(f"New {new_type} order placed @ {new_price}")
                    else:
                        self.logger.error(f"Failed to place {new_type} order: {response.error}")
                        self.bot_state.consecutive_failures += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating orders: {e}")
            self.bot_state.consecutive_failures += 1
            return False
    
    def _simulate_order_fills(self) -> bool:
        """Simulate order fills for dry run mode"""
        # Simple simulation: randomly fill some orders
        import random
        
        for i, order in enumerate(self.bot_state.orders):
            if random.random() < 0.01:  # 1% chance per cycle
                self.logger.info(f"[DRY RUN] Order filled: {order.order_type} @ {order.price}")
                
                # Simulate placing opposite order
                grid_spacing = (self.trading_config.upper_bound - 
                              (self.bot_state.last_price + self.trading_config.buffer)) / self.trading_config.grid_count
                
                if order.order_type == 'sell':
                    new_price = order.price - grid_spacing
                    new_type = 'buy'
                else:
                    new_price = order.price + grid_spacing
                    new_type = 'sell'
                
                fake_uuid = f"dry-run-{i:04d}-{int(time.time())}"
                self.bot_state.orders[i] = OrderState(
                    uuid=fake_uuid,
                    order_type=new_type,
                    price=new_price,
                    quantity=order.quantity,
                    market=order.market,
                    timestamp=datetime.utcnow()
                )
                
                self.bot_state.total_trades += 1
                self.logger.info(f"[DRY RUN] New {new_type} order placed @ {new_price}")
        
        return True
    
    def run(self) -> bool:
        """Main bot execution loop"""
        try:
            self.logger.info("Starting Secure Grid Bot")
            
            # Initialize API
            if not self.initialize_api():
                return False
            
            # Validate market conditions
            if not self.validate_market_conditions():
                return False
            
            # Place initial grid
            if not self.place_initial_grid():
                return False
            
            self.running = True
            pulse_count = 0
            
            self.logger.info("Entering main trading loop...")
            
            while self.running:
                pulse_count += 1
                
                # Check emergency conditions
                if self.check_emergency_conditions():
                    self.bot_state.emergency_stop = True
                    break
                
                # Update orders
                if not self.update_orders():
                    if self.bot_state.consecutive_failures >= self.trading_config.max_consecutive_failures:
                        break
                
                # Status update every minute
                if pulse_count % (60 // self.trading_config.pulse_interval) == 0:
                    uptime = datetime.utcnow() - self.bot_state.start_time
                    self.logger.info(f"Status - Uptime: {uptime}, Trades: {self.bot_state.total_trades}, "
                                   f"Active Orders: {len(self.bot_state.orders)}")
                
                time.sleep(self.trading_config.pulse_interval)
            
            self.logger.info("Bot stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Critical error in main loop: {e}")
            return False
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Cleanup resources and optionally cancel orders"""
        self.logger.info("Performing cleanup...")
        
        if not self.trading_config.dry_run:
            # Optionally cancel all orders on shutdown
            response = input("Cancel all open orders? (y/N): ")
            if response.lower() == 'y':
                cancel_response = self.api.cancel('all')
                if cancel_response.success:
                    self.logger.info("All orders cancelled")
                else:
                    self.logger.error(f"Failed to cancel orders: {cancel_response.error}")
        
        # Log final statistics
        uptime = datetime.utcnow() - self.bot_state.start_time
        self.logger.info(f"Final stats - Uptime: {uptime}, Total trades: {self.bot_state.total_trades}")


def main():
    """Main entry point"""
    try:
        # Check for config file argument
        config_file = sys.argv[1] if len(sys.argv) > 1 else None
        
        # Create and run bot
        bot = SecureGridBot(config_file)
        success = bot.run()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nBot interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()