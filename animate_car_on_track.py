"""
Animate 3D car model on 3D track from JSON telemetry file.

This script provides two options:
1. Use matplotlib (slower but no Blender required)
2. Use Blender (better quality, requires Blender installation)

For Blender animation, use blender_race_animation.py instead.
"""
from openf1_client import OpenF1Client
from http_client_impl import HttpxClient
import asyncio
import sys


async def main():
    """
    Main function to animate car on track from JSON file.
    """
    use_blender = '--blender' in sys.argv or '-b' in sys.argv
    
    if use_blender:
        print("=" * 60)
        print("Blender Animation Mode")
        print("=" * 60)
        print("\nTo use Blender animation, run:")
        print("  blender --background --python blender_race_animation.py")
        print("\nOr open Blender and run blender_race_animation.py from the Scripting workspace.")
        return
    
    async with HttpxClient() as http_client:
        client = OpenF1Client(http_client)
        
        json_file = "10_tel.json"
        car_stl = "minipekka.stl"
        track_stl = "track.stl"
        
        print("=" * 60)
        print("3D Car on Track Animation (Matplotlib)")
        print("=" * 60)
        print(f"\nJSON file: {json_file}")
        print(f"Car model: {car_stl}")
        print(f"Track model: {track_stl}")
        print("\nNote: For better quality, use Blender animation:")
        print("  python blender_race_animation.py")
        print("\nStarting matplotlib animation...")
        print("(Close the window to exit)")
        print("-" * 60)
        
        try:
            client.animate_car_on_track_from_json(
                json_file,
                car_stl,
                track_stl,
                driver_number=10,
                car_scale=1.0,
                track_scale=1.0,
                speed_multiplier=1.0,
                forward_axis='y'
            )
        except FileNotFoundError as e:
            print(f"Error: {e}")
            print("\nPlease make sure both STL files exist:")
            print(f"  - Car: {car_stl}")
            print(f"  - Track: {track_stl}")


if __name__ == "__main__":
    asyncio.run(main())
