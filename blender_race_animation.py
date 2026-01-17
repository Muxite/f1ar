"""
Blender script to animate 3D car on 3D track from JSON telemetry data.

This script can be run in Blender:
1. Open Blender
2. Go to Scripting workspace
3. Open this file
4. Run the script

Or run from command line:
blender --background --python blender_race_animation.py
"""
import json
import numpy as np
from pathlib import Path

try:
    import bpy
    import bmesh
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("Warning: Blender API not available. This script must be run in Blender.")


def clear_scene():
    """
    Clear all objects from the scene.
    """
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def load_stl(filepath, name, location=(0, 0, 0), scale=(1, 1, 1)):
    """
    Load an STL file into Blender.
    
    :param filepath: Path to STL file
    :param name: Name for the object
    :param location: Location tuple (x, y, z)
    :param scale: Scale tuple (x, y, z)
    :returns: Blender object
    """
    bpy.ops.import_mesh.stl(filepath=str(filepath))
    obj = bpy.context.active_object
    obj.name = name
    obj.location = location
    obj.scale = scale
    return obj


def create_material(name, color, metallic=0.0, roughness=0.5):
    """
    Create a material with specified properties.
    
    :param name: Material name
    :param color: RGB color tuple (0-1)
    :param metallic: Metallic value (0-1)
    :param roughness: Roughness value (0-1)
    :returns: Material
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    
    return mat


def setup_camera_and_lighting(car_obj):
    """
    Set up camera and lighting for the scene.
    
    :param car_obj: Car object to follow
    """
    bpy.ops.object.camera_add(location=(50, -50, 30))
    camera = bpy.context.active_object
    camera.name = "Camera"
    
    bpy.ops.object.light_add(type='SUN', location=(50, 50, 100))
    sun = bpy.context.active_object
    sun.name = "Sun"
    sun.data.energy = 5
    
    bpy.ops.object.light_add(type='AREA', location=(-50, -50, 50))
    area_light = bpy.context.active_object
    area_light.name = "Area Light"
    area_light.data.energy = 100
    area_light.data.size = 20
    
    bpy.context.scene.camera = camera
    
    bpy.ops.object.empty_add(type='ARROWS', location=(0, 0, 0))
    empty = bpy.context.active_object
    empty.name = "Camera Target"
    
    camera.constraints.new(type='TRACK_TO')
    camera.constraints['Track To'].target = empty
    camera.constraints['Track To'].track_axis = 'TRACK_NEGATIVE_Z'
    camera.constraints['Track To'].up_axis = 'UP_Y'
    
    empty.parent = car_obj
    empty.location = (0, 0, 0)


def calculate_rotation_matrix(direction, up_vector=(0, 0, 1)):
    """
    Calculate rotation matrix from direction vector.
    
    :param direction: Direction vector (normalized)
    :param up_vector: Up vector
    :returns: 4x4 rotation matrix
    """
    direction = Vector(direction).normalized()
    up = Vector(up_vector)
    
    right = direction.cross(up).normalized()
    if right.length < 0.01:
        up = Vector((0, 1, 0))
        right = direction.cross(up).normalized()
    
    true_up = right.cross(direction).normalized()
    
    rot_matrix = Matrix([
        [right.x, true_up.x, -direction.x, 0],
        [right.y, true_up.y, -direction.y, 0],
        [right.z, true_up.z, -direction.z, 0],
        [0, 0, 0, 1]
    ])
    
    return rot_matrix.to_3x3().to_4x4()


def animate_car_on_track(
    json_file_path: str,
    car_stl_path: str,
    track_stl_path: str,
    driver_number: int = 10,
    car_scale: float = 1.0,
    track_scale: float = 1.0,
    speed_multiplier: float = 1.0,
    forward_axis: str = 'y'
):
    """
    Animate car on track in Blender from JSON telemetry data.
    
    :param json_file_path: Path to JSON file (e.g., '10_tel.json')
    :param car_stl_path: Path to car STL model file
    :param track_stl_path: Path to track STL model file
    :param driver_number: Driver number for naming
    :param car_scale: Scale factor for car model
    :param track_scale: Scale factor for track model
    :param speed_multiplier: Speed multiplier (1.0 = real-time)
    :param forward_axis: Car model's forward direction axis
    """
    if not BLENDER_AVAILABLE:
        raise RuntimeError("This script must be run in Blender")
    
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
    
    print("Clearing scene...")
    clear_scene()
    
    print("Loading track model...")
    track_obj = load_stl(track_path, "Track", scale=(track_scale, track_scale, track_scale))
    track_mat = create_material("TrackMaterial", (0.3, 0.3, 0.3), metallic=0.1, roughness=0.8)
    track_obj.data.materials.append(track_mat)
    
    print("Loading car model...")
    car_obj = load_stl(car_path, "Car", scale=(car_scale, car_scale, car_scale))
    car_mat = create_material("CarMaterial", (0.8, 0.1, 0.1), metallic=0.9, roughness=0.2)
    car_obj.data.materials.append(car_mat)
    
    print("Setting up camera and lighting...")
    setup_camera_and_lighting(car_obj)
    
    print("Creating animation keyframes...")
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = int(time_data[-1] * 24 / speed_multiplier)
    scene.frame_set(1)
    
    axis_map = {
        'x': Vector((1, 0, 0)),
        'y': Vector((0, 1, 0)),
        'z': Vector((0, 0, 1)),
        '-x': Vector((-1, 0, 0)),
        '-y': Vector((0, -1, 0)),
        '-z': Vector((0, 0, -1))
    }
    model_forward = axis_map.get(forward_axis.lower(), Vector((0, 1, 0)))
    
    frame_step = max(1, int(24 / speed_multiplier / 10))
    
    for i in range(0, len(positions) - 1, frame_step):
        current_pos = positions[i]
        next_pos = positions[min(i + 1, len(positions) - 1)]
        
        direction = next_pos - current_pos
        direction_norm = np.linalg.norm(direction)
        
        if direction_norm < 1e-6:
            direction = np.array([0, 1, 0])
        else:
            direction = direction / direction_norm
        
        frame = int(time_data[i] * 24 / speed_multiplier) + 1
        
        car_obj.location = Vector(current_pos)
        
        rot_matrix = calculate_rotation_matrix(direction)
        car_obj.rotation_euler = rot_matrix.to_euler('XYZ')
        
        car_obj.keyframe_insert(data_path="location", frame=frame)
        car_obj.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        if i % 100 == 0:
            print(f"  Keyframe {i}/{len(positions)} (frame {frame})")
    
    print(f"Animation created: {scene.frame_start} to {scene.frame_end} frames")
    print("Press Space to play animation in Blender")
    
    bpy.context.view_layer.update()


if __name__ == "__main__":
    import sys
    
    json_file = "10_tel.json"
    car_stl = "minipekka.stl"
    track_stl = "track.stl"
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    if len(sys.argv) > 2:
        car_stl = sys.argv[2]
    if len(sys.argv) > 3:
        track_stl = sys.argv[3]
    
    try:
        animate_car_on_track(
            json_file,
            car_stl,
            track_stl,
            driver_number=10,
            car_scale=1.0,
            track_scale=1.0,
            speed_multiplier=1.0,
            forward_axis='y'
        )
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
