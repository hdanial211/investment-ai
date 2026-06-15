import os
import hmac
import hashlib
import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HataClient:
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or os.getenv("HATA_API_KEY")
        self.api_secret = api_secret or os.getenv("HATA_API_SECRET")
        self.base_url = "https://my-api.hata.io"
        
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        if not params:
            query_string = ""
        else:
            sorted_params = dict(sorted(params.items()))
            query_string = "&".join([f"{k}={v}" for k, v in sorted_params.items()])
            
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _request(self, method: str, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        params = params or {}
        
        headers = {}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        
        if self.api_secret:
            headers["Signature"] = self._generate_signature(params)
            
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                headers["Content-Type"] = "application/json"
                response = requests.post(url, headers=headers, json=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Hata API Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def get_markets(self):
        """Get available markets (no auth required usually)"""
        return self._request("GET", "/api/v1/markets")

    def get_balance(self):
        """Get account balance"""
        return self._request("GET", "/api/v1/account/balances")
