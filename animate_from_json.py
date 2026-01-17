"""
Animate arrow from JSON telemetry file (10_tel.json).

First plots debug visualization, then animates the arrow.
"""
from openf1_client import OpenF1Client
from http_client_impl import HttpxClient
import asyncio


async def main():
    """
    Main function to debug plot and animate from JSON file.
    """
    async with HttpxClient() as http_client:
        client = OpenF1Client(http_client)
        
        json_file = "10_tel.json"
        
        print("=" * 60)
        print("Telemetry JSON Visualization")
        print("=" * 60)
        
        print("\n1. Debug plotting telemetry data...")
        print("(Close the plot window to continue to animation)")
        client.debug_plot_telemetry_json(json_file)
        
        print("\n2. Starting arrow animation...")
        print("(Close the window to exit)")
        print("-" * 60)
        
        client.animate_arrow_from_json(
            json_file,
            driver_number=10,
            frame_skip=1,
            show_track=True,
            speed_multiplier=1.0
        )


if __name__ == "__main__":
    asyncio.run(main())
