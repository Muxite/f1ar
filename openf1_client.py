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
    
    def plot_3d_track(
        self,
        location_data: List[Dict[str, Any]],
        driver_number: Optional[int] = None,
        animate: bool = False,
        show_plot: bool = True,
        frame_skip: int = 1
    ) -> None:
        """
        Plot 3D track visualization showing car path with optional animation.
        
        Creates a 3D plot showing the car's path on track (x, y, z coordinates).
        Optionally animates the car moving along the track.
        
        :param location_data: List of location data points from get_time_and_location
        :param driver_number: Optional driver number for title
        :param animate: If True, animate car moving along track; if False, show static path
        :param show_plot: Whether to display the plot immediately
        :param frame_skip: Number of frames to skip in animation (1 = show all, 10 = show every 10th)
        """
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            from matplotlib.animation import FuncAnimation
        except ImportError:
            raise ImportError("matplotlib is required for plot_3d_track. Install with: pip install matplotlib")
        
        if not location_data:
            print("No location data to plot")
            return
        
        valid_points = [
            point for point in location_data
            if point.get("x") is not None and point.get("y") is not None and point.get("z") is not None
        ]
        
        if not valid_points:
            print("No valid 3D coordinates found in location data")
            return
        
        x_coords = [point.get("x") for point in valid_points]
        y_coords = [point.get("y") for point in valid_points]
        z_coords = [point.get("z") for point in valid_points]
        
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        if animate:
            ax.plot(x_coords, y_coords, z_coords, 'b-', linewidth=1, alpha=0.3, label='Track Path')
            
            car_point, = ax.plot([], [], [], 'ro', markersize=10, label='Car Position')
            trail_line, = ax.plot([], [], [], 'r-', linewidth=2, alpha=0.6, label='Car Trail')
            
            ax.scatter(x_coords[0], y_coords[0], z_coords[0], 
                      color='green', s=100, marker='o', label='Start', zorder=5)
            ax.scatter(x_coords[-1], y_coords[-1], z_coords[-1], 
                      color='red', s=100, marker='s', label='End', zorder=5)
            
            def update_frame(frame_idx):
                idx = min(frame_idx * frame_skip, len(x_coords) - 1)
                car_point.set_data([x_coords[idx]], [y_coords[idx]])
                car_point.set_3d_properties([z_coords[idx]])
                
                trail_x = x_coords[:idx+1]
                trail_y = y_coords[:idx+1]
                trail_z = z_coords[:idx+1]
                trail_line.set_data(trail_x, trail_y)
                trail_line.set_3d_properties(trail_z)
                
                return car_point, trail_line
            
            num_frames = (len(x_coords) + frame_skip - 1) // frame_skip
            anim = FuncAnimation(fig, update_frame, frames=num_frames, 
                                interval=50, blit=True, repeat=True)
        else:
            ax.plot(x_coords, y_coords, z_coords, 'b-', linewidth=2, alpha=0.8, label='Car Path')
            ax.scatter(x_coords[0], y_coords[0], z_coords[0], 
                      color='green', s=150, marker='o', label='Start', zorder=5)
            ax.scatter(x_coords[-1], y_coords[-1], z_coords[-1], 
                      color='red', s=150, marker='s', label='End', zorder=5)
        
        ax.set_xlabel('X Position (m)', fontsize=11)
        ax.set_ylabel('Y Position (m)', fontsize=11)
        ax.set_zlabel('Z Position (m)', fontsize=11)
        
        title = "3D Track Visualization"
        if driver_number is not None:
            title += f" - Driver #{driver_number}"
        if animate:
            title += " (Animated)"
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        if show_plot:
            plt.show()
    
    def debug_plot_telemetry_json(self, json_file_path: str) -> None:
        """
        Debug function to plot telemetry data from JSON file.
        
        Loads and visualizes the telemetry data structure to understand what's available.
        
        :param json_file_path: Path to JSON file (e.g., '10_tel.json')
        """
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            raise ImportError("matplotlib and numpy are required. Install with: pip install matplotlib numpy")
        
        json_path = Path(json_file_path)
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'tel' not in data:
            raise ValueError("JSON file does not contain 'tel' key")
        
        tel = data['tel']
        
        print("Telemetry data structure:")
        print(f"  Available keys: {list(tel.keys())}")
        print(f"  Data length: {len(tel.get('time', []))} points")
        
        if 'x' in tel and 'y' in tel and 'z' in tel:
            x = np.array(tel['x'])
            y = np.array(tel['y'])
            z = np.array(tel['z'])
            time = np.array(tel.get('time', list(range(len(x)))))
            
            fig = plt.figure(figsize=(15, 10))
            
            ax1 = fig.add_subplot(221, projection='3d')
            ax1.plot(x, y, z, 'b-', linewidth=1, alpha=0.7, label='Track Path')
            ax1.scatter(x[0], y[0], z[0], color='green', s=100, marker='o', label='Start')
            ax1.scatter(x[-1], y[-1], z[-1], color='red', s=100, marker='s', label='End')
            ax1.set_xlabel('X Position (m)')
            ax1.set_ylabel('Y Position (m)')
            ax1.set_zlabel('Z Position (m)')
            ax1.set_title('3D Track Path')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            ax2 = fig.add_subplot(222)
            ax2.plot(x, y, 'b-', linewidth=1, alpha=0.7)
            ax2.scatter(x[0], y[0], color='green', s=100, marker='o', label='Start')
            ax2.scatter(x[-1], y[-1], color='red', s=100, marker='s', label='End')
            ax2.set_xlabel('X Position (m)')
            ax2.set_ylabel('Y Position (m)')
            ax2.set_title('2D Track Path (Top View)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            ax2.axis('equal')
            
            if 'speed' in tel:
                speed = np.array(tel['speed'])
                ax3 = fig.add_subplot(223)
                ax3.plot(time, speed, 'r-', linewidth=2)
                ax3.set_xlabel('Time (s)')
                ax3.set_ylabel('Speed (km/h)')
                ax3.set_title('Speed over Time')
                ax3.grid(True, alpha=0.3)
            
            if 'throttle' in tel and 'brake' in tel:
                throttle = np.array(tel['throttle'])
                brake = np.array(tel['brake'])
                ax4 = fig.add_subplot(224)
                ax4.plot(time, throttle, 'g-', linewidth=2, label='Throttle (%)')
                ax4.plot(time, brake, 'r-', linewidth=2, label='Brake (%)')
                ax4.set_xlabel('Time (s)')
                ax4.set_ylabel('Percentage (%)')
                ax4.set_title('Throttle and Brake')
                ax4.legend()
                ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
        else:
            print("Warning: No x, y, z coordinates found in telemetry data")
            print("Available data keys:", list(tel.keys()))
    
    def animate_arrow_along_track(
        self,
        location_data: List[Dict[str, Any]],
        driver_number: Optional[int] = None,
        frame_skip: int = 1,
        show_track: bool = True,
        arrow_length: float = 5.0
    ) -> None:
        """
        Animate an arrow moving along the track path with proper rotation.
        
        Shows a simple arrow that moves along the track, rotating to face
        the direction of travel based on the vector between consecutive points.
        
        :param location_data: List of location data points from get_time_and_location
        :param driver_number: Optional driver number for title
        :param frame_skip: Number of frames to skip in animation (1 = show all, 10 = show every 10th)
        :param show_track: If True, display the track path as a line
        :param arrow_length: Length of the arrow in meters
        """
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            from matplotlib.animation import FuncAnimation
            import numpy as np
        except ImportError:
            raise ImportError("matplotlib and numpy are required. Install with: pip install matplotlib numpy")
        
        if not location_data:
            print("No location data to animate")
            return
        
        valid_points = [
            point for point in location_data
            if point.get("x") is not None and point.get("y") is not None and point.get("z") is not None
        ]
        
        if not valid_points:
            print("No valid 3D coordinates found in location data")
            return
        
        x_coords = np.array([point.get("x") for point in valid_points])
        y_coords = np.array([point.get("y") for point in valid_points])
        z_coords = np.array([point.get("z") for point in valid_points])
        
        positions = np.column_stack((x_coords, y_coords, z_coords))
        
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        if show_track:
            ax.plot(x_coords, y_coords, z_coords, 'b-', linewidth=2, alpha=0.5, label='Track Path')
        
        num_points = len(positions)
        current_idx = [0]
        arrow_quiver = [None]
        
        def create_arrow(pos, direction, length):
            """
            Create arrow points for 3D quiver.
            
            :param pos: Position (x, y, z)
            :param direction: Direction vector (normalized)
            :param length: Arrow length
            :returns: Arrow components for quiver
            """
            return pos[0], pos[1], pos[2], direction[0] * length, direction[1] * length, direction[2] * length
        
        def update_arrow(frame):
            """
            Update arrow position and rotation for animation.
            """
            idx = current_idx[0]
            
            if idx >= num_points - 1:
                current_idx[0] = 0
                idx = 0
            
            current_pos = positions[idx]
            next_idx = min(idx + frame_skip, num_points - 1)
            next_pos = positions[next_idx]
            
            direction = next_pos - current_pos
            direction_norm = np.linalg.norm(direction)
            
            if direction_norm < 1e-6:
                direction = np.array([1, 0, 0])
            else:
                direction = direction / direction_norm
            
            if arrow_quiver[0] is not None:
                arrow_quiver[0].remove()
            
            x, y, z, u, v, w = create_arrow(current_pos, direction, arrow_length)
            arrow_quiver[0] = ax.quiver(x, y, z, u, v, w, color='red', arrow_length_ratio=0.3, linewidth=3)
            
            current_idx[0] = next_idx
            return arrow_quiver[0]
        
        ax.set_xlabel('X Position (m)', fontsize=11)
        ax.set_ylabel('Y Position (m)', fontsize=11)
        ax.set_zlabel('Z Position (m)', fontsize=11)
        
        title = "Arrow Animation - Track Path"
        if driver_number is not None:
            title += f" - Driver #{driver_number}"
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        num_frames = (num_points + frame_skip - 1) // frame_skip
        anim = FuncAnimation(fig, update_arrow, frames=num_frames, interval=50, blit=False, repeat=True)
        
        plt.show()
    
    def animate_arrow_from_json(
        self,
        json_file_path: str,
        driver_number: Optional[int] = None,
        frame_skip: int = 1,
        show_track: bool = True,
        speed_multiplier: float = 1.0
    ) -> None:
        """
        Animate a dot moving along the track path from JSON telemetry file at real-time speed.
        
        Loads telemetry data from JSON file and animates a dot following the path.
        Uses time data from JSON to animate at real-time speed.
        
        :param json_file_path: Path to JSON file (e.g., '10_tel.json')
        :param driver_number: Optional driver number for title
        :param frame_skip: Number of frames to skip in animation (1 = show all, 10 = show every 10th)
        :param show_track: If True, display the track path as a line
        :param speed_multiplier: Speed multiplier (1.0 = real-time, 2.0 = 2x speed, 0.5 = half speed)
        """
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            from matplotlib.animation import FuncAnimation
            import numpy as np
        except ImportError:
            raise ImportError("matplotlib and numpy are required. Install with: pip install matplotlib numpy")
        
        json_path = Path(json_file_path)
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'tel' not in data:
            raise ValueError("JSON file does not contain 'tel' key")
        
        tel = data['tel']
        
        if 'x' not in tel or 'y' not in tel or 'z' not in tel:
            raise ValueError("JSON file does not contain x, y, z coordinates in 'tel'")
        
        x_coords = np.array(tel['x'])
        y_coords = np.array(tel['y'])
        z_coords = np.array(tel['z'])
        time_data = np.array(tel.get('time', list(range(len(x_coords)))))
        
        positions = np.column_stack((x_coords, y_coords, z_coords))
        
        if len(time_data) != len(positions):
            time_data = np.linspace(0, len(positions) * 0.05, len(positions))
        
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        if show_track:
            ax.plot(x_coords, y_coords, z_coords, 'b-', linewidth=1, alpha=0.3, label='Track Path')
        
        num_points = len(positions)
        dot_scatter = ax.scatter([], [], [], color='red', s=200, marker='o', label='Car Position', zorder=5)
        
        trail_x = []
        trail_y = []
        trail_z = []
        trail_line, = ax.plot([], [], [], 'r-', linewidth=2, alpha=0.6, label='Trail')
        
        current_idx = [0]
        start_time = [None]
        
        time_diffs = np.diff(time_data)
        if len(time_diffs) == 0:
            time_diffs = np.array([0.05])
        avg_interval = np.mean(time_diffs[time_diffs > 0]) if np.any(time_diffs > 0) else 0.05
        animation_interval = max(1, int(avg_interval * 1000 / speed_multiplier))
        
        def update_dot(frame):
            """
            Update dot position for animation at real-time speed.
            """
            if start_time[0] is None:
                import time
                start_time[0] = time.time()
            
            import time
            elapsed = (time.time() - start_time[0]) * speed_multiplier
            
            idx = current_idx[0]
            
            while idx < num_points - 1 and time_data[idx] <= elapsed:
                idx += 1
            
            if idx >= num_points - 1:
                idx = num_points - 1
                current_idx[0] = 0
                start_time[0] = time.time()
                trail_x.clear()
                trail_y.clear()
                trail_z.clear()
            else:
                current_idx[0] = idx
            
            current_pos = positions[idx]
            
            trail_x.append(current_pos[0])
            trail_y.append(current_pos[1])
            trail_z.append(current_pos[2])
            
            if len(trail_x) > 200:
                trail_x.pop(0)
                trail_y.pop(0)
                trail_z.pop(0)
            
            dot_scatter._offsets3d = ([current_pos[0]], [current_pos[1]], [current_pos[2]])
            if len(trail_x) > 1:
                trail_line.set_data(trail_x, trail_y)
                trail_line.set_3d_properties(trail_z)
            
            return dot_scatter, trail_line
        
        ax.set_xlabel('X Position (m)', fontsize=11)
        ax.set_ylabel('Y Position (m)', fontsize=11)
        ax.set_zlabel('Z Position (m)', fontsize=11)
        
        title = "Real-time Animation - Track Path (from JSON)"
        if driver_number is not None:
            title += f" - Driver #{driver_number}"
        if speed_multiplier != 1.0:
            title += f" ({speed_multiplier}x speed)"
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        anim = FuncAnimation(fig, update_dot, interval=16, blit=False, repeat=True, cache_frame_data=False)
        
        plt.show()
    
    def animate_car_on_track_from_json(
        self,
        json_file_path: str,
        car_stl_path: str,
        track_stl_path: str,
        driver_number: Optional[int] = None,
        car_scale: float = 1.0,
        track_scale: float = 1.0,
        speed_multiplier: float = 1.0,
        forward_axis: str = 'y'
    ) -> None:
        """
        Animate a 3D car model moving along a 3D track from JSON telemetry file.
        
        Loads telemetry data from JSON file and animates a 3D car model following the path
        on a 3D track model at real-time speed.
        
        :param json_file_path: Path to JSON file (e.g., '10_tel.json')
        :param car_stl_path: Path to car STL model file
        :param track_stl_path: Path to track STL model file
        :param driver_number: Optional driver number for title
        :param car_scale: Scale factor for car model
        :param track_scale: Scale factor for track model
        :param speed_multiplier: Speed multiplier (1.0 = real-time, 2.0 = 2x speed)
        :param forward_axis: Car model's forward direction axis ('x', 'y', 'z', '-x', '-y', '-z')
        """
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            from matplotlib.animation import FuncAnimation
            import numpy as np
            import trimesh
        except ImportError:
            raise ImportError("matplotlib, numpy, and trimesh are required. Install with: pip install matplotlib numpy trimesh")
        
        json_path = Path(json_file_path)
        car_path = Path(car_stl_path)
        track_path = Path(track_stl_path)
        
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")
        if not car_path.exists():
            raise FileNotFoundError(f"Car STL file not found: {car_stl_path}")
        if not track_path.exists():
            raise FileNotFoundError(f"Track STL file not found: {track_stl_path}")
        
        print("Loading JSON telemetry data...")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'tel' not in data:
            raise ValueError("JSON file does not contain 'tel' key")
        
        tel = data['tel']
        
        if 'x' not in tel or 'y' not in tel or 'z' not in tel:
            raise ValueError("JSON file does not contain x, y, z coordinates in 'tel'")
        
        x_coords = np.array(tel['x'])
        y_coords = np.array(tel['y'])
        z_coords = np.array(tel['z'])
        time_data = np.array(tel.get('time', list(range(len(x_coords)))))
        
        positions = np.column_stack((x_coords, y_coords, z_coords))
        
        if len(time_data) != len(positions):
            time_data = np.linspace(0, len(positions) * 0.05, len(positions))
        
        print("Loading 3D models...")
        car_mesh = trimesh.load(str(car_path))
        car_mesh.apply_scale(car_scale)
        
        track_mesh = trimesh.load(str(track_path))
        track_mesh.apply_scale(track_scale)
        
        axis_map = {
            'x': np.array([1, 0, 0]),
            'y': np.array([0, 1, 0]),
            'z': np.array([0, 0, 1]),
            '-x': np.array([-1, 0, 0]),
            '-y': np.array([0, -1, 0]),
            '-z': np.array([0, 0, -1])
        }
        model_forward = axis_map.get(forward_axis.lower(), np.array([0, 1, 0]))
        
        def calculate_rotation(current_pos, next_pos):
            """
            Calculate rotation matrix to align car with direction vector.
            
            :param current_pos: Current position (x, y, z)
            :param next_pos: Next position (x, y, z)
            :returns: Rotation matrix (4x4)
            """
            direction = next_pos - current_pos
            direction_norm = np.linalg.norm(direction)
            
            if direction_norm < 1e-6:
                return np.eye(4)
            
            direction = direction / direction_norm
            
            up = np.array([0, 0, 1])
            right = np.cross(direction, up)
            right_norm = np.linalg.norm(right)
            
            if right_norm < 1e-6:
                up = np.array([0, 1, 0])
                right = np.cross(direction, up)
                right_norm = np.linalg.norm(right)
            
            if right_norm > 1e-6:
                right = right / right_norm
                up = np.cross(right, direction)
            else:
                up = np.array([0, 0, 1])
            
            rotation_matrix = np.eye(4)
            rotation_matrix[:3, 0] = right
            rotation_matrix[:3, 1] = -direction
            rotation_matrix[:3, 2] = up
            
            model_forward_world = rotation_matrix[:3, :3] @ model_forward
            if np.dot(model_forward_world, direction) < 0:
                rotation_matrix[:3, 1] = direction
                rotation_matrix[:3, 0] = -right
            
            return rotation_matrix
        
        print("Setting up visualization...")
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        track_vertices = track_mesh.vertices
        track_faces = track_mesh.faces
        
        if len(track_faces) > 10000:
            print("Simplifying track model for better performance...")
            track_simplified = track_mesh.simplify_quadric_decimation(10000)
            track_vertices = track_simplified.vertices
            track_faces = track_simplified.faces
        
        ax.plot_trisurf(
            track_vertices[:, 0], track_vertices[:, 1], track_vertices[:, 2],
            triangles=track_faces, color='gray', alpha=0.5, shade=True, label='Track'
        )
        
        num_points = len(positions)
        car_poly = [None]
        current_idx = [0]
        start_time = [None]
        
        def update_car(frame):
            """
            Update car position and rotation for animation at real-time speed.
            """
            if start_time[0] is None:
                import time
                start_time[0] = time.time()
            
            import time
            elapsed = (time.time() - start_time[0]) * speed_multiplier
            
            idx = current_idx[0]
            
            while idx < num_points - 1 and time_data[idx] <= elapsed:
                idx += 1
            
            if idx >= num_points - 1:
                idx = num_points - 1
                current_idx[0] = 0
                start_time[0] = time.time()
            else:
                current_idx[0] = idx
            
            current_pos = positions[idx]
            next_idx = min(idx + 1, num_points - 1)
            next_pos = positions[next_idx]
            
            rotation = calculate_rotation(current_pos, next_pos)
            
            transformed_car = car_mesh.copy()
            transformed_car.apply_transform(rotation)
            transformed_car.apply_translation(current_pos)
            
            if car_poly[0] is not None:
                car_poly[0].remove()
            
            car_vertices = transformed_car.vertices
            car_faces = transformed_car.faces
            
            if len(car_faces) > 5000:
                car_simplified = transformed_car.simplify_quadric_decimation(5000)
                car_vertices = car_simplified.vertices
                car_faces = car_simplified.faces
            
            car_poly[0] = ax.plot_trisurf(
                car_vertices[:, 0], car_vertices[:, 1], car_vertices[:, 2],
                triangles=car_faces, color='red', alpha=0.9, shade=True
            )
            
            return car_poly[0]
        
        ax.set_xlabel('X Position (m)', fontsize=11)
        ax.set_ylabel('Y Position (m)', fontsize=11)
        ax.set_zlabel('Z Position (m)', fontsize=11)
        
        title = "3D Car on Track Animation"
        if driver_number is not None:
            title += f" - Driver #{driver_number}"
        if speed_multiplier != 1.0:
            title += f" ({speed_multiplier}x speed)"
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        x_range = [x_coords.min(), x_coords.max()]
        y_range = [y_coords.min(), y_coords.max()]
        z_range = [z_coords.min(), z_coords.max()]
        
        ax.set_xlim(x_range)
        ax.set_ylim(y_range)
        ax.set_zlim(z_range)
        
        print("Starting animation...")
        anim = FuncAnimation(fig, update_car, interval=33, blit=False, repeat=True, cache_frame_data=False)
        
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
