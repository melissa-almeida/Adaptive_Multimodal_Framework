# Adaptive Confidence-Aware Multimodal Interaction Framework

An experimental framework designed to evaluate dynamic input modality adaptation in Human-Computer Interaction (HCI). This project implements an asynchronous multimodal system combining real-time computer vision and speech recognition, utilizing a custom 2D space shooter game as a hardware-in-the-loop testbed.

Developed for the course *Multimodal Interaction & Evolution of Interfaces*.

---

## Project Overview

Traditional multimodal interfaces rely on rigid, hardcoded rules to combine user inputs. This project introduces a **dynamic adaptation engine** that continuously monitors the mathematical confidence levels of independent input sensors and modifies interaction states accordingly.

Instead of evaluating the application (the game) as the core artifact, the focus is placed on the underlying framework's ability to remain stable, smooth out input degradation, and safely fall back during acute signal loss without breaking user immersion.

### Key Features
* **Vision-Based Kinematic Tracking:** Real-time upper-body postural tilt estimation using MediaPipe Pose.
* **Deep Learning Voice Activity Detection (VAD):** High-accuracy voice boundary processing powered by a Silero VAD neural network model.
* **State Machine Adaptation Engine:** Advanced state transitions using threshold hysteresis and temporal window locks to completely mitigate state chattering caused by noisy sensor boundaries.
* **Asynchronous Multi-Threaded Pipeline:** Decoupled audio callback buffers and heavy API processing loops to guarantee stable rendering frame rates (60 FPS) under concurrent execution.

---

## System Architecture & Modalities

### 1. Vision Module (`src/input_modules/vision_pose.py`)
Tracks the horizontal shoulder line vector to extract user lateral tilt. Movement orientation mimics a physical steering mechanism. Rather than treating raw MediaPipe visibility flags as absolute metrics, the system derives confidence from tracking stability over recent frames.

### 2. Audio Module (`src/input_modules/audio_voice.py`)
Processes acoustic data through a multi-stage pipeline:
* **Silero VAD Callback:** Evaluates sample chunks (512 samples @ 16kHz) to derive speech probability $P(\text{speech}|\text{audio})$ acting as the continuous confidence metric.
* **Temporal Windowing:** Mitigates phonetic clipping by preserving speech onset and offset margins.
* **Asynchronous ASR:** Spawns worker threads to handle Google Speech Recognition tasks for specific actions (`"FIRE or SHOOT"`, `"SHIELD or BARRIER"`), avoiding main game-loop degradation.

### 3. Adaptation Engine (`src/adaptation_engine.py`)
Evaluates tracking and speech confidence metrics frame-by-frame to switch between three discrete operation modes:
1. **FULL_MULTIMODAL:** Ideal tracking conditions. Direct raw posture tracking combined with voice activation triggers.
2. **ASSISTED_SMOOTHING:** Triggered when sensor quality degrades. Implements Exponential Moving Average (EMA) filters to suppress environmental noise, stabilize controls, and smooth sudden kinematic jitters.
3. **SAFE_FALLBACK:** Severe signal loss emergency protocol. Safely delegates control to the mechanical keyboard layout to prevent system failure.

*Note on Stability:* The engine uses distinct activation/deactivation confidence thresholds (hysteresis) alongside a temporal state lock to completely block erratic mode switching (*chattering*) under partial occlusion conditions.

---

## Installation & Setup

### Prerequisites
* Python 3.10.x (Tested on Python 3.10.20)
* Working Web Camera and Microphone

### Environment Configuration

1. Clone this repository to your local directory:
```Bash
   git clone [https://github.com/YOUR_USERNAME/multimodal-spaceship-shooter.git](https://github.com/YOUR_USERNAME/multimodal-spaceship-shooter.git)
   cd multimodal-spaceship-shooter
   ```
2. Create a clean Python virtual environment:
```Bash
python -m venv .venv
```
3. Activate the environment:
```Bash
Windows: .venv\Scripts\activate
macOS/Linux: source .venv/bin/activate
```
4. Install the required external dependencies:
```Bash
pip install -r requirements.txt
```
(Alternatively, if managing via Anaconda Prompt, run conda create -n multimodal-env python=3.10 followed by pip install -r requirements.txt inside the active environment).

---

## Running the System
To start the interface, launch the primary execution script from the repository root:
```Bash
python main.py
```

---

## Execution Flow
1. Audio Calibration: On startup, the audio module runs an initial ambient noise profiling routine to compute background acoustic thresholds.
2. Webcam Initialization: MediaPipe frames compile and launch immediately after calibration.
3. Main Loop: Control the space shooter by tilting your torso left/right to navigate, and speak commands clearly ("FIRE / SHOOT" to attack, "SHIELD / BARRIER" to activate defense barriers).
4. HUD Overlay: An active debugging interface prints real-time confidence scores and system adaptation states directly onto the screen.
