# Singapore F1 Race Animation

This script animates an STL car model driving around the Singapore F1 track using real race telemetry data.

## Usage

```bash
python singapore_race_animation.py [stl_file] [year] [refresh]
```

### Parameters:
- `stl_file`: Path to STL model file (default: `minipekka.stl`)
- `year`: Year of Singapore GP (default: 2024)
- `refresh`: Set to "refresh" to force API calls instead of using cache

### Examples:

```bash
# Basic usage with default settings
python singapore_race_animation.py

# Specify STL file and year
python singapore_race_animation.py minipekka.stl 2023

# Force refresh (download new data)
python singapore_race_animation.py minipekka.stl 2024 refresh
```

## Features

- **Automatic data fetching**: Searches for Singapore GP data for the specified year
- **Caching**: Automatically caches JSON data to avoid repeated API calls
- **Fallback years**: If data not found for specified year, tries previous years
- **Rate limit handling**: Automatically handles API rate limits
- **STL animation**: Animates your 3D model along the actual race track path

## Data Sources

The script uses the OpenF1 API to fetch real race telemetry data. Data is cached in the `.cache` directory to avoid repeated API calls.

## Requirements

- Python 3.8+
- All dependencies from `requirements.txt`
- An STL model file (e.g., `minipekka.stl`)
