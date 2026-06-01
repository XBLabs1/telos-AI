# Project Telos — Architecture & Technical Overview

**Organization:** XB Labs
**Repo:** github.com/XBLabs/telos
**Status:** Active Development

---

## 1. Project Overview

Telos is an open source platform for training robot AI policies using only webcam footage. It eliminates the need for expensive teleoperation hardware or physical rigs by using hand tracking and synthetic dataset generation. The platform is built on top of HuggingFace LeRobot and extends it with a webcam-first data collection pipeline.

The long-term vision is a community marketplace (Telos Hub) where anyone can upload trained robot skills and URDF profiles, similar to HuggingFace but scoped to physical AI and robotics. The platform is intentionally local-first: all training and inference runs on the user's own machine with no cloud dependency required.

---

## 2. System Architecture

The system is composed of three core modules that form a sequential pipeline from raw webcam input to deployable robot policy.

### Module 1 — Hand Tracking & Data Logging ✅ Complete

Captures webcam footage and extracts hand landmark data in real time using MediaPipe. This module produces the raw demonstration dataset.

**Key details:**
- MediaPipe Hands extracts 21 3D landmark coordinates (X, Y, Z) per frame at approximately 30fps
- Pinch gesture between Thumb Tip (landmark 4) and Index Tip (landmark 8) maps to gripper open/close signal as a normalized float 0.0 to 1.0
- All landmark data and gripper state logged per frame to JSON or CSV
- Output: raw human demonstration dataset ready for IK processing

### Module 2 — Robotic Mapping via Inverse Kinematics 🔧 In Progress

Converts MediaPipe hand landmark coordinates into motor joint angles for the physical robot arm using inverse kinematics. This module bridges human hand motion to robot-compatible commands.

**Key details:**
- IK library: ikpy or TinyIK (lightweight, local, no GPU required)
- Robot described via URDF file — a text-based XML specification of joint types, segment lengths, and motor ranges
- URDF fed into IK solver to compute per-joint angles from end-effector target positions
- Motor commands sent over USB serial to Arduino or Raspberry Pi Pico on the physical arm
- Reference hardware: SO-101 arm by TheRobotStudio (6-DOF, Feetech STS3215 servos, Waveshare control board)
- URDF files for SO-101 available in the TheRobotStudio GitHub repo under /Simulation

### Module 3 — Phantom Dataset Generation 🔧 In Progress

The core differentiator of the platform. Instead of using heavy AI video inpainting to remove the human arm from footage, a lightweight 3D render of the robot arm is overlaid onto the webcam frames using the robot STL files. This produces clean synthetic training data without requiring a GPU.

**Key details:**
- Robot STL files loaded via PyVista (primary) or Trimesh (supporting geometry math)
- 3D robot arm mesh rendered frame-by-frame over the webcam footage, positioned using the IK joint angles from Module 2
- Output is a synthetic video of the robot arm performing the demonstrated task — no human visible
- This synthetic video paired with the motor angle log forms the complete training dataset
- Intentionally lightweight: runs on CPU, no GPU needed, works on standard laptop
- The clean synthetic appearance is an advantage for policy training — it reduces visual noise versus real video

---

## 3. Training Data Format

Each recorded session produces paired observation-action data logged per frame. This is the format consumed by the ACT (Action Chunking with Transformers) policy model.

**Per-frame data structure:**
- `observation` — phantom dataset frame (synthetic robot arm image)
- `joint_angles` — array of per-joint motor angles for all 6 DOF
- `gripper` — float 0.0 to 1.0 representing open/close state
- `end_effector_xyz` — [X, Y, Z] position of the arm tip in 3D space

**Critical design decision — normalized actions:**

Joint angles are stored as relative delta movements between frames, not absolute motor positions. Example: motor 1 moved +2.3 degrees from previous frame. This prevents hardcoding to any specific robot. When a skill is downloaded from the marketplace and run on a different robot, the local URDF remapper converts these normalized deltas into that robot's specific motor commands.

---

## 4. Tech Stack

| Layer | Library / Tool | Purpose |
|---|---|---|
| Hand Tracking | MediaPipe Hands | 21-landmark 3D hand detection from webcam |
| IK Solver | ikpy / TinyIK | Convert hand position to robot joint angles |
| 3D Rendering | PyVista | Load STL files, render phantom overlay per frame |
| Geometry | Trimesh | STL loading, mesh manipulation, supporting math |
| Robot Format | URDF (XML) | Robot arm description: joints, segments, ranges |
| Policy Model | ACT (LeRobot) | Action Chunking Transformers for imitation learning |
| Inference Runtime | ONNX / TensorRT / CoreML | Local policy execution, no cloud required |
| Hardware Comms | USB Serial | Send motor commands to Arduino or Pi Pico |
| Data Format | JSON / CSV | Frame-by-frame observation-action logging |
| Base Framework | HuggingFace LeRobot | Imitation learning pipeline foundation |

---

## 5. Module Status

| Module | Status |
|---|---|
| Module 1 — Hand Tracking & Logging | ✅ Complete |
| Module 2 — IK Robotic Mapping | 🔧 In Progress |
| Module 3 — Phantom Dataset Generation | 🔧 In Progress |
| Local GUI (Desktop App) | 📋 Planned |
| Telos Hub (Web Marketplace) | 📋 Planned |

---

## 6. Reference Hardware

### SO-101 Robot Arm (TheRobotStudio)
- 6 degrees of freedom
- Servos: Feetech STS3215 (30kg/cm torque)
- Controller: Waveshare servo control board
- Connection: USB-C to host machine
- CAD source: OnShape public document by TheRobotStudio
- STL files: github.com/TheRobotStudio/SO-ARM100 — use SO-101 files specifically
- URDF: available in /Simulation folder of the same repo

### Webcam Setup
- Standard laptop webcam supported for basic use
- Overhead mount STL available in /Optional folder of SO-ARM100 repo
- Consistent camera position is important for MediaPipe tracking accuracy
- No depth camera required

---

## 7. URDF Library Strategy

One of the platform's core UX challenges is URDF onboarding. Every robot arm has a different physical configuration and requires a URDF file for the IK solver to function. The strategy is tiered:

**Tier 1 — Pre-built profiles (ship with app):**
- SO-101 (reference hardware, ships first)
- SO-100 (deprecated but still widely used)
- Koch arm
- Additional popular hobby arms added over time

**Tier 2 — Community URDF library:**
- Users submit URDF profiles for their robots via GitHub pull request
- Reviewed and merged into the platform robot library
- Users select their robot from a dropdown — no manual URDF required

**Tier 3 — URDF generator (future):**
- Guided form: user enters joint count, segment lengths, motor types
- Platform generates URDF automatically
- This tier is a significant gap in the current LeRobot ecosystem and a platform differentiator

---

## 8. Product Roadmap

### Phase 1 — Local App (Current)
Goal: working end-to-end pipeline on a single machine. Hobbyist-focused. All processing local, no cloud dependency.

- Complete Module 2 (IK mapping) and Module 3 (Phantom Dataset)
- Test full pipeline on SO-101 reference arm
- Push working Python scripts to github.com/XBLabs/telos
- Build simple local desktop GUI (Gradio or Tkinter)
- Package app as installable binary via PyInstaller (.exe for Windows, .dmg for Mac)
- Release via GitHub Releases

### Phase 2 — Telos Hub Marketplace
Goal: community platform for sharing trained skills and URDF profiles. Free to use, no commission on uploads or downloads.

- Web application — separate repo: github.com/XBLabs/telos-hub
- Users upload trained policy files (.pt or .onnx) as robot skills
- Skills tagged by robot type, task category, and required URDF
- URDF library browser — community submitted profiles
- GitHub Actions sync between contributor PRs and the hub library
- Skill download auto-remaps normalized actions to the user's robot URDF

### Phase 3 — Cloud & Enterprise
Goal: premium tier for power users and industrial clients. This is the primary monetization layer.

- Cloud-based Phantom Dataset generation using AI video inpainting (higher quality, GPU-backed)
- Fleet analytics dashboard: inference drift detection, anomaly flagging, training data audit trails
- Safety layer: live webcam monitoring for human-robot coexistence, out-of-bounds command interception
- Industrial protocol bridging: Modbus, EtherCAT, OPC-UA output for factory PLC integration
- Enterprise URDF support for industrial arms (UR series, KUKA, Fanuc)

---

## 9. Next Development Tasks

### 1. Complete Module 2 — IK Mapping
- Install and configure ikpy
- Load SO-101 URDF into the IK solver
- Write coordinate transform: MediaPipe landmark space to robot workspace
- Output: per-frame joint angle array logged alongside Module 1 data
- Test: move hand in front of webcam, verify corresponding joint angles are computed correctly

### 2. Complete Module 3 — Phantom Dataset
- Load SO-101 STL files using PyVista
- For each recorded frame: position the 3D mesh using computed joint angles from Module 2
- Render the mesh overlay onto the webcam frame
- Output: synthetic video file + matched joint angle log = complete training dataset
- Validate dataset format against LeRobot ACT expected input schema

### 3. End-to-End Test Case
- Record a simple pick-and-place task using webcam
- Run full pipeline: hand tracking → IK → phantom overlay → dataset
- Train ACT policy on the generated dataset using LeRobot
- Run trained policy on physical SO-101 arm
- Document results and push to GitHub

### 4. Desktop GUI
- After pipeline is verified working, wrap in simple GUI
- Framework: Gradio (faster) or Tkinter (more control)
- Required screens: robot selector dropdown, record session, view dataset, run policy
- Package with PyInstaller for distribution via GitHub Releases

---

## 10. Repository Structure

```
XBLabs/telos/
├── hardware/
│   ├── STL/          ← 3D print files for SO-101
│   ├── STEP/         ← CAD files for Fusion 360 / OnShape
│   └── URDF/         ← Robot description files
├── software/
│   ├── module1/      ← Hand tracking & data logging
│   ├── module2/      ← IK mapping
│   ├── module3/      ← Phantom dataset generation
│   └── gui/          ← Desktop application (coming)
├── datasets/         ← Example recorded sessions
├── docs/
│   └── ARCHITECTURE.md  ← this document
├── .gitignore        ← Python template
├── LICENSE           ← MIT
└── README.md
```

---

*Document maintained by XB Labs. Update module status when each module is completed. This document is for technical context only.*
