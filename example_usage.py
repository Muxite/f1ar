"""
Example usage of OpenF1Client.
"""
import asyncio
from openf1_client import OpenF1Client
from http_client_impl import HttpxClient


async def main():
    """
    Example demonstrating OpenF1Client usage with caching.
    """
    async with HttpxClient() as http_client:
        client = OpenF1Client(http_client)
        
        driver_number = 1
        date = "2024-03-02"
        
        print(f"First call - fetching from API (use_cache=True by default)...")
        location_data = await client.get_time_and_location(
            driver_number=driver_number,
            date=date
        )
        print(f"Retrieved {len(location_data)} data points")
        
        print(f"\nSecond call - should load from cache (much faster)...")
        location_data_cached = await client.get_time_and_location(
            driver_number=driver_number,
            date=date
        )
        print(f"Retrieved {len(location_data_cached)} data points from cache")
        
        print(f"\nThird call - forcing API call (use_cache=False)...")
        location_data_fresh = await client.get_time_and_location(
            driver_number=driver_number,
            date=date,
            use_cache=False
        )
        print(f"Retrieved {len(location_data_fresh)} data points from API")
        
        if location_data:
            print("\nFirst few data points:")
            for point in location_data[:5]:
                print(f"  Time: {point['time']}, X: {point['x']}, Y: {point['y']}, Z: {point['z']}")
            
            print("\nPlotting path...")
            client.debug_plot_path(location_data, driver_number=driver_number)
        
        json_output = await client.get_time_and_location_json(
            driver_number=driver_number,
            date=date
        )
        print("\nJSON output (first 500 chars):")
        print(json_output[:500])


if __name__ == "__main__":
    asyncio.run(main())
