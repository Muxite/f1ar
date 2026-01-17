"""
Main function for Singapore F1 Grand Prix race animation.

Fetches or loads cached race data and animates an STL car model
driving around the Singapore track.
"""
import asyncio
from pathlib import Path
from openf1_client import OpenF1Client
from http_client_impl import HttpxClient


async def find_singapore_race_data(client: OpenF1Client, year: int = 2024):
    """
    Find Singapore Grand Prix race data for a given year.
    
    :param client: OpenF1Client instance
    :param year: Year to search for (default 2024)
    :returns: Tuple of (date, session_key, meeting_key) or None if not found
    """
    singapore_dates = [
        f"{year}-09-22",
        f"{year}-09-21",
        f"{year}-09-20",
        f"{year}-09-19",
        f"{year}-09-18",
        f"{year}-09-17",
        f"{year}-09-16",
        f"{year}-09-15",
    ]
    
    print(f"Searching for Singapore GP {year}...")
    
    for date in singapore_dates:
        try:
            await asyncio.sleep(0.5)
            sessions = await client.get_sessions(date=date, use_cache=True)
            
            for session in sessions:
                location_name = session.get("location", "").lower()
                if "singapore" in location_name:
                    meeting_key = session.get("meeting_key")
                    session_key = session.get("session_key")
                    session_name = session.get("session_name", "Unknown")
                    
                    print(f"Found Singapore GP session: {session_name} on {date}")
                    print(f"  Meeting Key: {meeting_key}, Session Key: {session_key}")
                    
                    return date, session_key, meeting_key
        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                print(f"Rate limit hit, waiting before retry...")
                await asyncio.sleep(2)
            continue
    
    return None, None, None


async def get_driver_for_animation(client: OpenF1Client, session_key: int, meeting_key: int):
    """
    Get a driver number for animation (prefer race session).
    
    :param client: OpenF1Client instance
    :param session_key: Session key
    :param meeting_key: Meeting key
    :returns: Driver number to use
    """
    drivers = await client.get_drivers(session_key=session_key, meeting_key=meeting_key, use_cache=True)
    
    if drivers:
        driver_number = drivers[0].get("driver_number")
        driver_name = drivers[0].get("full_name", f"Driver #{driver_number}")
        print(f"Using driver: {driver_name} (#{driver_number})")
        return driver_number
    
    print("No drivers found, using default driver #1")
    return 1


async def main(
    year: int = 2024,
    force_refresh: bool = False,
    driver_number: int = None,
    frame_skip: int = 5,
    arrow_length: float = 5.0
):
    """
    Main function to animate arrow driving around Singapore track.
    
    :param year: Year of Singapore GP (default 2024)
    :param force_refresh: If True, force API calls instead of using cache
    :param driver_number: Specific driver number to use (None = auto-select)
    :param frame_skip: Number of frames to skip in animation
    :param arrow_length: Length of the arrow in meters
    """
    print("=" * 60)
    print("Singapore F1 Grand Prix - Race Animation")
    print("=" * 60)
    
    async with HttpxClient() as http_client:
        client = OpenF1Client(http_client, cache_dir=".cache")
        
        date, session_key, meeting_key = await find_singapore_race_data(client, year)
        
        if date is None:
            print(f"\nCould not find Singapore GP data for {year}.")
            print("Trying alternative years...")
            
            for alt_year in [2023, 2022, 2021]:
                await asyncio.sleep(1)
                date, session_key, meeting_key = await find_singapore_race_data(client, alt_year)
                if date is not None:
                    print(f"Using Singapore GP from {alt_year}")
                    break
            
            if date is None:
                print("Could not find Singapore GP data via API search.")
                print("Using known Singapore GP dates as fallback...")
                singapore_fallback_dates = [
                    ("2024-09-22", None, None),
                    ("2023-09-17", None, None),
                    ("2022-10-02", None, None),
                ]
                
                for fallback_date, _, _ in singapore_fallback_dates:
                    print(f"Trying fallback date: {fallback_date}")
                    test_data = await client.get_time_and_location(
                        driver_number=1,
                        date=fallback_date,
                        use_cache=True
                    )
                    if test_data:
                        date = fallback_date
                        session_key = None
                        meeting_key = None
                        print(f"Found data for {fallback_date}, using this date.")
                        break
                
                if date is None:
                    print("No data found. Please check your internet connection and try again later.")
                    return
        
        print(f"\nUsing date: {date}")
        
        if driver_number is None:
            if session_key and meeting_key:
                driver_number = await get_driver_for_animation(client, session_key, meeting_key)
            else:
                driver_number = 1
                print(f"Using default driver: #{driver_number}")
        
        print(f"\nFetching location data for driver #{driver_number}...")
        print("(This will use cache if available, or download from API)")
        
        try:
            location_data = await client.get_time_and_location(
                driver_number=driver_number,
                session_key=session_key,
                meeting_key=meeting_key,
                date=date,
                use_cache=not force_refresh
            )
        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                print("Rate limit hit. Using cached data only...")
                location_data = await client.get_time_and_location(
                    driver_number=driver_number,
                    session_key=session_key,
                    meeting_key=meeting_key,
                    date=date,
                    use_cache=True
                )
            else:
                raise
        
        if not location_data:
            print("No location data available for the specified parameters.")
            print("Trying without session/meeting filters...")
            
            try:
                location_data = await client.get_time_and_location(
                    driver_number=driver_number,
                    date=date,
                    use_cache=not force_refresh
                )
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    print("Rate limit hit. Using cached data only...")
                    location_data = await client.get_time_and_location(
                        driver_number=driver_number,
                        date=date,
                        use_cache=True
                    )
                else:
                    raise
        
        if location_data:
            print(f"Retrieved {len(location_data)} data points")
            print(f"\nStarting animation...")
            print("(Close the window to exit)")
            print("-" * 60)
            
            try:
                client.animate_arrow_along_track(
                    location_data,
                    driver_number=driver_number,
                    frame_skip=frame_skip,
                    show_track=True,
                    arrow_length=arrow_length
                )
            except Exception as e:
                print(f"Error during animation: {e}")
                raise
        else:
            print("No location data available. Cannot create animation.")
            print("\nPossible reasons:")
            print("  - No data available for the specified date/driver")
            print("  - API may not have data for this session")
            print("  - Try a different year or driver number")


if __name__ == "__main__":
    import sys
    
    year = 2024
    force_refresh = False
    frame_skip = 5
    arrow_length = 5.0
    
    if len(sys.argv) > 1:
        year = int(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2].lower() == "refresh":
        force_refresh = True
    if len(sys.argv) > 3:
        frame_skip = int(sys.argv[3])
    if len(sys.argv) > 4:
        arrow_length = float(sys.argv[4])
    
    asyncio.run(main(
        year=year,
        force_refresh=force_refresh,
        frame_skip=frame_skip,
        arrow_length=arrow_length
    ))
