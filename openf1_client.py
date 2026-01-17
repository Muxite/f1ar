"""
OpenF1 API client for fetching car location and telemetry data.

Provides async methods to query OpenF1 REST API endpoints and retrieve
car position data over time, with optional visualization capabilities.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any, Protocol
from datetime import datetime
import json
import os
import hashlib
from pathlib import Path


class HTTPClient(Protocol):
    """
    Protocol for HTTP client dependency injection.
    
    Allows injecting different HTTP clients (httpx, aiohttp, etc.)
    for testing purposes.
    """
    
    async def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform async GET request.
        
        :param url: URL to request
        :param params: Query parameters
        :returns: JSON response as dictionary
        """
        ...


class OpenF1Client:
    """
    Async client for OpenF1 API with dependency injection support.
    
    Fetches car location and timing data from OpenF1 REST endpoints.
    Supports filtering by driver, track, session, and date.
    """
    
    BASE_URL = "https://api.openf1.org/v1"
    
    def __init__(self, http_client: HTTPClient, cache_dir: str = ".cache"):
        """
        Initialize OpenF1 client with HTTP client dependency.
        
        :param http_client: HTTP client implementation (httpx.AsyncClient, etc.)
        :param cache_dir: Directory to store cached JSON files
        """
        self.http_client = http_client
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _generate_cache_filename(self, endpoint: str, params: Dict[str, Any]) -> Path:
        """
        Generate cache filename based on endpoint and parameters.
        
        :param endpoint: API endpoint name (e.g., 'location', 'car_data')
        :param params: Query parameters dictionary
        :returns: Path to cache file
        """
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:12]
        
        date_str = params.get("date", params.get("date_start", ""))
        if date_str:
            date_str = date_str.replace("-", "")
        else:
            date_str = datetime.now().strftime("%Y%m%d")
        
        driver_str = f"_driver{params.get('driver_number', '')}" if params.get('driver_number') else ""
        session_str = f"_session{params.get('session_key', '')}" if params.get('session_key') else ""
        meeting_str = f"_meeting{params.get('meeting_key', '')}" if params.get('meeting_key') else ""
        
        filename = f"{endpoint}_{date_str}{driver_str}{session_str}{meeting_str}_{param_hash}.json"
        return self.cache_dir / filename
    
    def _load_from_cache(self, cache_file: Path) -> Optional[List[Dict[str, Any]]]:
        """
        Load data from cache file if it exists.
        
        :param cache_file: Path to cache file
        :returns: Cached data or None if file doesn't exist
        """
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None
    
    def _save_to_cache(self, cache_file: Path, data: List[Dict[str, Any]]) -> None:
        """
        Save data to cache file.
        
        :param cache_file: Path to cache file
        :param data: Data to cache
        """
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass
    
    async def get_location_data(
        self,
        driver_number: Optional[int] = None,
        session_key: Optional[int] = None,
        meeting_key: Optional[int] = None,
        date: Optional[str] = None,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch car location data from OpenF1 API.
        
        :param driver_number: Filter by driver number
        :param session_key: Filter by session key
        :param meeting_key: Filter by meeting key
        :param date: Filter by specific date (YYYY-MM-DD)
        :param date_start: Start of date range (YYYY-MM-DD)
        :param date_end: End of date range (YYYY-MM-DD)
        :param use_cache: If True, load from cache if available; if False, force API call
        :returns: List of location data points with time and coordinates
        """
        url = f"{self.BASE_URL}/location"
        params = {}
        
        if driver_number is not None:
            params["driver_number"] = driver_number
        if session_key is not None:
            params["session_key"] = session_key
        if meeting_key is not None:
            params["meeting_key"] = meeting_key
        if date is not None:
            params["date"] = date
        if date_start is not None:
            params["date_start"] = date_start
        if date_end is not None:
            params["date_end"] = date_end
        
        cache_file = self._generate_cache_filename("location", params)
        
        if use_cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data is not None:
                return cached_data
        
        response = await self.http_client.get(url, params)
        result = response if isinstance(response, list) else []
        
        if use_cache:
            self._save_to_cache(cache_file, result)
        
        return result
    
    async def get_car_data(
        self,
        driver_number: Optional[int] = None,
        session_key: Optional[int] = None,
        meeting_key: Optional[int] = None,
        date: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch car telemetry data from OpenF1 API.
        
        :param driver_number: Filter by driver number
        :param session_key: Filter by session key
        :param meeting_key: Filter by meeting key
        :param date: Filter by specific date (YYYY-MM-DD)
        :param use_cache: If True, load from cache if available; if False, force API call
        :returns: List of car telemetry data points
        """
        url = f"{self.BASE_URL}/car_data"
        params = {}
        
        if driver_number is not None:
            params["driver_number"] = driver_number
        if session_key is not None:
            params["session_key"] = session_key
        if meeting_key is not None:
            params["meeting_key"] = meeting_key
        if date is not None:
            params["date"] = date
        
        cache_file = self._generate_cache_filename("car_data", params)
        
        if use_cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data is not None:
                return cached_data
        
        response = await self.http_client.get(url, params)
        result = response if isinstance(response, list) else []
        
        if use_cache:
            self._save_to_cache(cache_file, result)
        
        return result
    
    async def get_sessions(
        self,
        meeting_key: Optional[int] = None,
        date: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch session metadata to help identify session keys.
        
        :param meeting_key: Filter by meeting key
        :param date: Filter by specific date (YYYY-MM-DD)
        :param use_cache: If True, load from cache if available; if False, force API call
        :returns: List of session metadata
        """
        url = f"{self.BASE_URL}/sessions"
        params = {}
        
        if meeting_key is not None:
            params["meeting_key"] = meeting_key
        if date is not None:
            params["date"] = date
        
        cache_file = self._generate_cache_filename("sessions", params)
        
        if use_cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data is not None:
                return cached_data
        
        response = await self.http_client.get(url, params)
        result = response if isinstance(response, list) else []
        
        if use_cache:
            self._save_to_cache(cache_file, result)
        
        return result
    
    async def get_drivers(
        self,
        session_key: Optional[int] = None,
        meeting_key: Optional[int] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch driver metadata to help identify driver numbers.
        
        :param session_key: Filter by session key
        :param meeting_key: Filter by meeting key
        :param use_cache: If True, load from cache if available; if False, force API call
        :returns: List of driver metadata
        """
        url = f"{self.BASE_URL}/drivers"
        params = {}
        
        if session_key is not None:
            params["session_key"] = session_key
        if meeting_key is not None:
            params["meeting_key"] = meeting_key
        
        cache_file = self._generate_cache_filename("drivers", params)
        
        if use_cache:
            cached_data = self._load_from_cache(cache_file)
            if cached_data is not None:
                return cached_data
        
        response = await self.http_client.get(url, params)
        result = response if isinstance(response, list) else []
        
        if use_cache:
            self._save_to_cache(cache_file, result)
        
        return result
    
    async def get_time_and_location(
        self,
        driver_number: int,
        session_key: Optional[int] = None,
        meeting_key: Optional[int] = None,
        date: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get time and location data for a specific driver.
        
        Returns JSON array with time and location (x, y, z) coordinates.
        
        :param driver_number: Driver number to query
        :param session_key: Optional session key filter
        :param meeting_key: Optional meeting key filter
        :param date: Optional date filter (YYYY-MM-DD)
        :param use_cache: If True, load from cache if available; if False, force API call
        :returns: List of dictionaries with date, x, y, z coordinates
        """
        location_data = await self.get_location_data(
            driver_number=driver_number,
            session_key=session_key,
            meeting_key=meeting_key,
            date=date,
            use_cache=use_cache
        )
        
        result = []
        for point in location_data:
            result.append({
                "time": point.get("date"),
                "x": point.get("x"),
                "y": point.get("y"),
                "z": point.get("z"),
                "driver_number": point.get("driver_number"),
                "session_key": point.get("session_key")
            })
        
        return result
    
    def debug_plot_path(
        self,
        location_data: List[Dict[str, Any]],
        driver_number: Optional[int] = None,
        show_plot: bool = True
    ) -> None:
        """
        Plot car path using matplotlib for debugging purposes.
        
        Creates a 2D plot showing the car's path on track (x, y coordinates).
        
        :param location_data: List of location data points from get_time_and_location
        :param driver_number: Optional driver number for title
        :param show_plot: Whether to display the plot immediately
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib is required for debug_plot_path. Install with: pip install matplotlib")
        
        if not location_data:
            print("No location data to plot")
            return
        
        x_coords = [point.get("x") for point in location_data if point.get("x") is not None]
        y_coords = [point.get("y") for point in location_data if point.get("y") is not None]
        
        if not x_coords or not y_coords:
            print("No valid coordinates found in location data")
            return
        
        plt.figure(figsize=(10, 8))
        plt.plot(x_coords, y_coords, 'b-', linewidth=1.5, alpha=0.7, label='Car Path')
        plt.scatter(x_coords[0], y_coords[0], color='green', s=100, marker='o', label='Start', zorder=5)
        plt.scatter(x_coords[-1], y_coords[-1], color='red', s=100, marker='s', label='End', zorder=5)
        
        plt.xlabel('X Position (m)', fontsize=12)
        plt.ylabel('Y Position (m)', fontsize=12)
        
        title = f"Car Path Visualization"
        if driver_number is not None:
            title += f" - Driver #{driver_number}"
        plt.title(title, fontsize=14, fontweight='bold')
        
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.axis('equal')
        
        if show_plot:
            plt.show()
    
    async def get_time_and_location_json(
        self,
        driver_number: int,
        session_key: Optional[int] = None,
        meeting_key: Optional[int] = None,
        date: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """
        Get time and location data as JSON string.
        
        :param driver_number: Driver number to query
        :param session_key: Optional session key filter
        :param meeting_key: Optional meeting key filter
        :param date: Optional date filter (YYYY-MM-DD)
        :param use_cache: If True, load from cache if available; if False, force API call
        :returns: JSON string with time and location data
        """
        data = await self.get_time_and_location(
            driver_number=driver_number,
            session_key=session_key,
            meeting_key=meeting_key,
            date=date,
            use_cache=use_cache
        )
        return json.dumps(data, indent=2)
