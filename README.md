# shaurya7vs
for NWHacks2026
# F1 Augmented Reality Live Race Viewer

## Overview

This project is an **F1 Augmented Reality (AR) visualization platform** that converts real Formula 1 race data into a **live, manipulatable 3D race model**. The system currently targets **web browsers** (desktop/laptop) for proof-of-concept and will later be extended to **Apple Vision Pro** using Apple’s spatial computing stack.

The core idea is similar in spirit to products like *Lapz*, but focused on an **interactive 3D race reconstruction**, where cars are represented as moving entities (e.g., dots or meshes) following real telemetry on a fully modeled F1 circuit.

---

## Key Features

* **3D Track Visualization**

  * High-fidelity 3D models of F1 circuits (e.g., Singapore, Abu Dhabi)
  * Full-track view with pan, zoom, and rotate controls

* **Live / Replay Race Mapping**

  * Maps real F1 telemetry and timing data to a 3D track
  * Animates car positions in real time or during race replays
  * Supports single-car or multi-car visualization

* **Telemetry-Driven Animation**

  * Speed, distance, lap time, and positional data
  * Cars move based on actual race telemetry (not pre-baked animation)

* **Browser-Based Rendering (Phase 1)**

  * Runs in modern browsers using WebGL/WebGPU
  * Mouse and keyboard interaction

* **AR / Spatial Computing Ready (Phase 2)**

  * Architecture designed for future deployment on **Apple Vision Pro**
  * Planned support for spatial anchors, gestures, and volumetric rendering

---

## Tech Stack

### Current (Browser-Based)

* **Rendering:** Three.js or Babylon.js
* **Data Processing:** JavaScript / TypeScript
* **3D Assets:** glTF / GLB (converted from FBX, OBJ, or STL)
* **Telemetry Input:** CSV / JSON race data
* **Animation:** Spline-based path following + time interpolation

### Planned (Apple Vision Pro)

* **Frameworks:** visionOS, RealityKit, ARKit
* **Language:** Swift / SwiftUI
* **Rendering:** RealityKit + Metal (if required)
* **Interaction:** Hand tracking, gaze, spatial gestures

---

## Data Pipeline

```text
F1 Telemetry & Timing Data
        ↓
 Data Parsing & Normalization
        ↓
 Distance / Time Mapping
        ↓
 Track Spline Projection
        ↓
 3D Animation Engine
        ↓
 Browser / AR Visualization
```

### Telemetry Sources

* Publicly available F1 telemetry archives
* Community datasets (CSV / JSON)
* Single-car or multi-car race sessions

> **Note:** This project does not scrape live F1 broadcasts and relies on legally accessible data sources.

---

## How It Works

1. **Track Loading**

   * A 3D model of an F1 circuit is loaded and scaled to real-world dimensions.
   * A centerline spline is generated or manually defined along the racing line.

2. **Telemetry Ingestion**

   * Telemetry data (time, distance, speed, lap) is loaded per car.
   * Data is normalized to match track length and coordinate space.

3. **Car Mapping**

   * Each car is represented as a dot or low-poly mesh.
   * Position along the spline is updated based on telemetry timestamps.

4. **Rendering & Interaction**

   * Users can rotate, pan, and zoom the entire circuit.
   * Camera modes: free cam, follow car, top-down tactical view.

---

## Project Structure

```text
/src
 ├── data/          # Telemetry and timing data
 ├── tracks/        # 3D track models (glTF/GLB)
 ├── core/          # Telemetry parsing & math
 ├── rendering/     # 3D scene, camera, lighting
 ├── animation/     # Spline and motion logic
 └── ui/            # Browser UI controls

/public
 └── index.html

README.md
```

---

## Current Limitations

* Browser-only (no true AR yet)
* Limited elevation accuracy depending on track model
* Telemetry precision depends on available data granularity
* No official F1 live data feed integration (yet)

---

## Roadmap

### Phase 1 – Proof of Concept (Current)

* Single-car race visualization
* Browser-based 3D interaction
* Accurate spline-based motion

### Phase 2 – Enhanced Visualization

* Multi-car support
* Overtakes, gaps, sector highlighting
* Speed-based color gradients

### Phase 3 – Apple Vision Pro

* Port rendering to RealityKit
* Tabletop-scale AR race view
* Gesture-based controls
* Real-time spatial overlays

---

## Inspiration

* Lapz (F1 AR visualization)
* Formula 1 data engineering
* Sports analytics + spatial computing

---

## Disclaimer

This project is for **educational, research, and proof-of-concept purposes only** and is **not affiliated with Formula 1, FIA, or any official broadcasters**.

---

## Author

Built by an F1 and engineering enthusiast exploring the future of **sports visualization, AR, and spatial computing**.

---

## License

MIT License (or to be defined)
