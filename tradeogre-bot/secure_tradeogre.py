#!/usr/bin/env python3
"""
Secure TradeOgre API wrapper with enhanced error handling and security features
"""

import requests
import time
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class APIResponse:
    """Standardized API response wrapper"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class RateLimiter:
    """Rate limiting to prevent API abuse"""
    
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.logger = logging.getLogger('tradeogre_bot.ratelimiter')
    
    def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded"""
        now = datetime.utcnow()
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < timedelta(minutes=1)]
        
        if len(self.calls) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.calls[0]).total_seconds()
            if sleep_time > 0:
                self.logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self.calls.append(now)


class SecureTradeOgre:
    """Enhanced TradeOgre API wrapper with security and error handling"""
    
    def __init__(self, key: Optional[str] = None, secret: Optional[str] = None, 
                 timeout: int = 30, max_retries: int = 3):
        self.key = key
        self.secret = secret
        self.uri = 'https://tradeogre.com/api/v1'
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.rate_limiter = RateLimiter()
        self.logger = logging.getLogger('tradeogre_bot.api')
        
        # Set session headers
        self.session.headers.update({
            'User-Agent': 'TradeOgrePyGridBot/2.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def load_key(self, path: str) -> bool:
        """Load API key and secret from file with validation"""
        try:
            with open(path, 'r') as f:
                lines = f.read().strip().split('\n')
                if len(lines) < 2:
                    raise ValueError("Key file must contain key on first line and secret on second line")
                
                self.key = lines[0].strip()
                self.secret = lines[1].strip()
                
                if not self.key or not self.secret:
                    raise ValueError("Key and secret cannot be empty")
                
                self.logger.info("API credentials loaded successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error loading API credentials: {e}")
            return False
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     auth_required: bool = False) -> APIResponse:
        """Make HTTP request with error handling and retries"""
        url = f"{self.uri}{endpoint}"
        
        # Check authentication
        if auth_required and (not self.key or not self.secret):
            return APIResponse(
                success=False,
                error="API key and secret required for this endpoint"
            )
        
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        for attempt in range(self.max_retries + 1):
            try:
                # Prepare request
                kwargs = {
                    'timeout': self.timeout,
                    'data': data if data else None
                }
                
                if auth_required:
                    kwargs['auth'] = (self.key, self.secret)
                
                # Make request
                if method.upper() == 'GET':
                    response = self.session.get(url, **kwargs)
                elif method.upper() == 'POST':
                    response = self.session.post(url, **kwargs)
                else:
                    return APIResponse(
                        success=False,
                        error=f"Unsupported HTTP method: {method}"
                    )
                
                # Check response
                response.raise_for_status()
                
                try:
                    json_data = response.json()
                except ValueError:
                    return APIResponse(
                        success=False,
                        error="Invalid JSON response",
                        status_code=response.status_code
                    )
                
                # Check for API errors
                if isinstance(json_data, dict) and json_data.get('success') is False:
                    return APIResponse(
                        success=False,
                        error=json_data.get('error', 'Unknown API error'),
                        status_code=response.status_code
                    )
                
                self.logger.debug(f"API request successful: {method} {endpoint}")
                return APIResponse(
                    success=True,
                    data=json_data,
                    status_code=response.status_code
                )
                
            except requests.exceptions.Timeout:
                error_msg = f"Request timeout (attempt {attempt + 1}/{self.max_retries + 1})"
                self.logger.warning(error_msg)
                if attempt == self.max_retries:
                    return APIResponse(success=False, error="Request timeout after retries")
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.exceptions.ConnectionError:
                error_msg = f"Connection error (attempt {attempt + 1}/{self.max_retries + 1})"
                self.logger.warning(error_msg)
                if attempt == self.max_retries:
                    return APIResponse(success=False, error="Connection error after retries")
                time.sleep(2 ** attempt)
                
            except requests.exceptions.HTTPError as e:
                error_msg = f"HTTP error: {e.response.status_code}"
                self.logger.error(error_msg)
                return APIResponse(
                    success=False,
                    error=error_msg,
                    status_code=e.response.status_code
                )
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.logger.error(error_msg)
                return APIResponse(success=False, error=error_msg)
        
        return APIResponse(success=False, error="Max retries exceeded")
    
    def markets(self) -> APIResponse:
        """Retrieve all markets"""
        return self._make_request('GET', '/markets')
    
    def order_book(self, market: str) -> APIResponse:
        """Retrieve order book for a market"""
        if not self._validate_market_format(market):
            return APIResponse(success=False, error="Invalid market format")
        
        return self._make_request('GET', f'/orders/{market}')
    
    def ticker(self, market: str) -> APIResponse:
        """Retrieve ticker for a market"""
        if not self._validate_market_format(market):
            return APIResponse(success=False, error="Invalid market format")
        
        return self._make_request('GET', f'/ticker/{market}')
    
    def history(self, market: str) -> APIResponse:
        """Retrieve trade history for a market"""
        if not self._validate_market_format(market):
            return APIResponse(success=False, error="Invalid market format")
        
        return self._make_request('GET', f'/history/{market}')
    
    def balance(self, currency: str) -> APIResponse:
        """Get balance for a specific currency"""
        if not currency or not currency.isalnum():
            return APIResponse(success=False, error="Invalid currency format")
        
        data = {"currency": currency}
        return self._make_request('POST', '/account/balance', data=data, auth_required=True)
    
    def balances(self) -> APIResponse:
        """Retrieve all balances"""
        return self._make_request('GET', '/account/balances', auth_required=True)
    
    def buy(self, market: str, quantity: Union[str, float], price: Union[str, float]) -> APIResponse:
        """Submit a buy order"""
        validation_error = self._validate_order_params(market, quantity, price)
        if validation_error:
            return APIResponse(success=False, error=validation_error)
        
        data = {
            "market": market,
            "quantity": str(quantity),
            "price": str(price)
        }
        
        response = self._make_request('POST', '/order/buy', data=data, auth_required=True)
        if response.success:
            self.logger.info(f"Buy order placed: {quantity} {market} @ {price}")
        
        return response
    
    def sell(self, market: str, quantity: Union[str, float], price: Union[str, float]) -> APIResponse:
        """Submit a sell order"""
        validation_error = self._validate_order_params(market, quantity, price)
        if validation_error:
            return APIResponse(success=False, error=validation_error)
        
        data = {
            "market": market,
            "quantity": str(quantity),
            "price": str(price)
        }
        
        response = self._make_request('POST', '/order/sell', data=data, auth_required=True)
        if response.success:
            self.logger.info(f"Sell order placed: {quantity} {market} @ {price}")
        
        return response
    
    def order(self, uuid: str) -> APIResponse:
        """Retrieve information about a specific order"""
        if not self._validate_uuid(uuid):
            return APIResponse(success=False, error="Invalid UUID format")
        
        return self._make_request('GET', f'/account/order/{uuid}', auth_required=True)
    
    def orders(self, market: Optional[str] = None) -> APIResponse:
        """Retrieve active orders"""
        data = {"market": market or ""}
        return self._make_request('POST', '/account/orders', data=data, auth_required=True)
    
    def cancel(self, uuid: str) -> APIResponse:
        """Cancel an order"""
        if uuid != "all" and not self._validate_uuid(uuid):
            return APIResponse(success=False, error="Invalid UUID format")
        
        data = {"uuid": uuid}
        response = self._make_request('POST', '/order/cancel', data=data, auth_required=True)
        
        if response.success:
            self.logger.info(f"Order cancelled: {uuid}")
        
        return response
    
    def _validate_market_format(self, market: str) -> bool:
        """Validate market format (BASE-QUOTE)"""
        if not market or '-' not in market:
            return False
        
        parts = market.split('-')
        if len(parts) != 2:
            return False
        
        base, quote = parts
        if not base.isalnum() or not quote.isalnum():
            return False
        
        return True
    
    def _validate_uuid(self, uuid: str) -> bool:
        """Validate UUID format"""
        if not uuid or len(uuid) != 36:
            return False
        
        # Basic UUID format check
        parts = uuid.split('-')
        if len(parts) != 5:
            return False
        
        expected_lengths = [8, 4, 4, 4, 12]
        for part, expected_length in zip(parts, expected_lengths):
            if len(part) != expected_length or not all(c in '0123456789abcdef-' for c in part.lower()):
                return False
        
        return True
    
    def _validate_order_params(self, market: str, quantity: Union[str, float], 
                              price: Union[str, float]) -> Optional[str]:
        """Validate order parameters"""
        if not self._validate_market_format(market):
            return "Invalid market format"
        
        try:
            qty = float(quantity)
            if qty <= 0:
                return "Quantity must be positive"
        except (ValueError, TypeError):
            return "Invalid quantity format"
        
        try:
            prc = float(price)
            if prc <= 0:
                return "Price must be positive"
        except (ValueError, TypeError):
            return "Invalid price format"
        
        return None
    
    def get_connection_status(self) -> bool:
        """Test API connectivity"""
        response = self.markets()
        return response.success