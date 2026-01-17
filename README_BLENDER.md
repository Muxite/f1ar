# Blender Race Animation

This script integrates the F1 race animation into Blender for professional 3D rendering.

## Requirements

- Blender 3.0 or later
- Python packages: numpy (usually included with Blender)

## Usage

### Method 1: Run in Blender GUI

1. Open Blender
2. Go to the **Scripting** workspace (top menu)
3. Click **File > Open** and select `blender_race_animation.py`
4. Modify the file paths at the bottom if needed:
   ```python
   json_file = "10_tel.json"
   car_stl = "minipekka.stl"
   track_stl = "track.stl"
   ```
5. Click **Run Script** (or press Alt+P)
6. Press **Space** to play the animation

### Method 2: Run from Command Line

```bash
blender --background --python blender_race_animation.py
```

Or with custom file paths:

```bash
blender --background --python blender_race_animation.py -- 10_tel.json minipekka.stl track.stl
```

### Method 3: Run as Add-on

1. In Blender, go to **Edit > Preferences > Add-ons**
2. Click **Install...** and select `blender_race_animation.py`
3. Enable the add-on
4. Use it from the 3D Viewport

## Features

- **3D Track Model**: Loads and displays your track STL file
- **3D Car Model**: Loads and animates your car STL file
- **Real-time Animation**: Uses time data from JSON for accurate speed
- **Automatic Camera**: Camera follows the car
- **Professional Lighting**: Sun and area lights for realistic rendering
- **Materials**: Car has metallic red material, track has gray asphalt material
- **Keyframe Animation**: Creates proper Blender keyframes for smooth playback

## Customization

You can modify the script to:
- Change car/track scale
- Adjust speed multiplier
- Change materials and colors
- Modify camera angles
- Add more lights
- Export as video or image sequence

## Exporting Animation

After running the script:

1. Go to **Render Properties** (camera icon)
2. Set output format (e.g., FFmpeg video or PNG sequence)
3. Set frame range
4. Click **Render > Render Animation**

## Notes

- The script automatically sets up the scene with proper lighting
- Camera follows the car automatically
- Animation uses Blender's keyframe system for smooth playback
- Large STL files may take time to load
