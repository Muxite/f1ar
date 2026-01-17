"""
HTTP client implementation for OpenF1 client using httpx.
"""
from typing import Optional, Dict, Any
import httpx


class HttpxClient:
    """
    HTTP client implementation using httpx for async requests.
    
    Implements the HTTPClient protocol for use with OpenF1Client.
    """
    
    def __init__(self, timeout: float = 30.0):
        """
        Initialize httpx client.
        
        :param timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform async GET request.
        
        :param url: URL to request
        :param params: Query parameters
        :returns: JSON response as dictionary or list
        """
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        
        response = await self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()
