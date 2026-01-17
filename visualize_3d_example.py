"""
Simple example showing 3D track visualization with animation.
"""
import asyncio
from openf1_client import OpenF1Client
from http_client_impl import HttpxClient


async def main():
    """
    Example demonstrating 3D track visualization.
    """
    async with HttpxClient() as http_client:
        client = OpenF1Client(http_client)
        
        driver_number = 1
        date = "2024-03-02"
        
        print(f"Fetching location data for driver #{driver_number} on {date}...")
        location_data = await client.get_time_and_location(
            driver_number=driver_number,
            date=date
        )
        
        if location_data:
            print(f"Retrieved {len(location_data)} data points")
            print("\nDisplaying 3D animated track visualization...")
            print("(Close the window to continue)")
            
            client.plot_3d_track(
                location_data, 
                driver_number=driver_number, 
                animate=True,
                frame_skip=5
            )
        else:
            print("No location data available")


if __name__ == "__main__":
    asyncio.run(main())
