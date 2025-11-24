# Advanced Synchronous Generator Analysis & Simulation Tool

## Overview

A comprehensive Python application for analyzing salient-pole synchronous generators with dynamic simulation capabilities. This tool solves complex electrical engineering problems and provides real-time visualization.

## Problem Solved

**Salient-pole synchronous generator with:**
- Apparent power: Sn = 50 kVA
- Line voltage: V1Ln = 380 V
- Frequency: fn = 60 Hz
- Speed: nn = 1800 rpm
- Power factor: cos φn = 0.82

**Calculations:**
1. **Synchronous Reactances (Xsd, Xsq)** - Using slip test method
2. **Nominal Field Excitation Current (Ifn)** - Using phasor analysis
3. **Field Winding Voltage at 120°C** - Temperature-corrected resistance

## Features

### Core Functionality
- ✅ **Automatic calculation** of synchronous reactances from slip test data
- ✅ **Field current determination** using d-q axis transformation
- ✅ **Temperature compensation** for field winding resistance
- ✅ **Phasor diagram** visualization
- ✅ **Characteristic curves**: V-curves, regulation, external characteristics

### Dynamic Simulation
- ✅ **Real-time ODE solver** with RK45 (Runge-Kutta) and Euler methods
- ✅ **Multi-state simulation**: rotor angle, speed, currents, torque
- ✅ **Differential equations** for machine dynamics
- ✅ **Transient analysis** with adjustable parameters

### GUI Features
- ✅ **Professional Tkinter interface** with multiple tabs
- ✅ **Interactive sliders** for parameter adjustment
- ✅ **Real-time updates** and auto-scaling
- ✅ **Responsive design** with automatic window resizing
- ✅ **Export capabilities** for results and plots
- ✅ **Start/Stop/Reset controls** for simulation

## Installation

### Requirements
```bash
pip install numpy matplotlib scipy
```

For the GUI version, you also need Tkinter:
```bash
# On Ubuntu/Debian
sudo apt-get install python3-tk

# On macOS (included with Python)
# On Windows (included with Python)
```

### Python Version
- Python 3.7 or higher

## Two Versions Available

### 1. Standalone Solver (No GUI Required)
For quick calculations and detailed text output:
```bash
python synchronous_generator_solver.py
```
✅ Works without Tkinter
✅ Complete detailed solution with explanations
✅ Perfect for command-line use or scripts

### 2. Full GUI Application (Requires Tkinter)
For interactive analysis with visualizations:
```bash
python synchronous_generator_analysis.py
```
✅ Advanced graphical interface
✅ Real-time parameter adjustment
✅ Dynamic simulation with plots
✅ Phasor diagrams and characteristic curves

## Usage

### Quick Start Guide

1. **Launch Application**: Run the Python script
2. **Adjust Parameters**: Use sliders in the left panel to modify machine parameters
3. **Solve Problem**: Click "Solve Problem" button or use Analysis menu
4. **View Results**: Check the Results tab for detailed calculations
5. **Run Simulation**:
   - Select solver method (RK45 recommended for accuracy)
   - Click "Start Simulation"
   - View real-time plots in Simulation tab
6. **Visualize**:
   - Switch to "Phasor Diagram" tab for vector representation
   - Check "Characteristics" tab for performance curves

### Menu Options

**File Menu:**
- Save Results - Export calculations to text file
- Export Plot - Save current visualization as PNG
- Exit - Close application

**Analysis Menu:**
- Solve Problem - Calculate all required values
- Phasor Diagram - Show voltage/current phasors
- Characteristic Curves - Display machine characteristics

**Simulation Menu:**
- Start Dynamic Simulation - Begin real-time ODE solving
- Stop Simulation - Halt current simulation
- Reset - Clear simulation data

**Help Menu:**
- About - Application information
- Documentation - User guide

## Technical Details

### Calculation Methods

#### (a) Synchronous Reactances
Using the slip test method:
```
Xsd = V_phase / I_min = Vs/(√3 × I_min)
Xsq = V_phase / I_max = Vs/(√3 × I_max)
```

**Result:**
- Xsd ≈ 6.63 Ω (direct-axis)
- Xsq ≈ 3.46 Ω (quadrature-axis)

#### (b) Nominal Field Current
Using d-q axis transformation and power angle calculation:
```
Id = In × sin(φn + δ)
Iq = In × cos(φn + δ)
En = √[(V1n + Xsq×Iq)² + (Xsd×Id)²]
Ifn = If0 × (En / V1n)
```

**Result:**
- Ifn ≈ 12.5 A

#### (c) Field Voltage at Temperature
Temperature-corrected resistance:
```
Rf(T) = Rf(20°C) × [1 + α(T - 20°C)]
Vf = Ifn × Rf(T)
```
Where α = 0.00393 /°C for copper

**Result:**
- Rf(120°C) ≈ 1.12 Ω
- Vf ≈ 14.0 V

### Dynamic Simulation Model

The simulator solves the following differential equations:

**State Vector:** y = [δ, ω, E'q, Id, Iq]

**Equations:**
```
dδ/dt = ω - ωn                                  (rotor angle)
dω/dt = (1/J)(Tm - Te - D(ω - ωn))             (swing equation)
dE'q/dt = (1/T'do)(Efd - E'q)                  (field dynamics)
dId/dt = (1/Ta)(-Id + (V×sin(δ) - E'q)/Xsd)   (d-axis current)
dIq/dt = (1/Ta)(-Iq + V×cos(δ)/Xsq)            (q-axis current)
```

**Parameters:**
- J: Moment of inertia (kg·m²)
- D: Damping coefficient
- T'do: d-axis transient time constant
- Ta: Armature time constant

### Solver Methods

**RK45 (Runge-Kutta 4-5):**
- High accuracy
- Adaptive step size
- Recommended for detailed analysis
- Computationally intensive

**Euler Method:**
- Fast computation
- Fixed step size (1 ms)
- Good for real-time visualization
- Lower accuracy

## GUI Layout

```
┌─────────────────────────────────────────────────────────────┐
│  File  Analysis  Simulation  Help                           │
├──────────────┬──────────────────────────────────────────────┤
│              │  [Results] [Simulation] [Phasor] [Chars]    │
│  Input       │                                              │
│  Parameters  │                                              │
│              │                                              │
│  ┌─────────┐│              Main Visualization Area         │
│  │ Nominal ││                                              │
│  │  Params ││                                              │
│  ├─────────┤│                                              │
│  │ Lab Test││                                              │
│  │  Data   ││                                              │
│  ├─────────┤│                                              │
│  │Operating││                                              │
│  │  Conds  ││                                              │
│  ├─────────┤│                                              │
│  │  Sim    ││                                              │
│  │  Params ││                                              │
│  └─────────┘│                                              │
│              │                                              │
│  [Solve]     │                                              │
│  [Start Sim] │                                              │
│  [Stop]      │                                              │
│  [Reset]     │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

## Features Detail

### Auto-Scaling
- Window resizing automatically adjusts all components
- Plots scale dynamically with window size
- Responsive layout using pack geometry manager

### Real-Time Updates
- Parameter changes reflect immediately in sliders
- Simulation plots update during execution
- Thread-based computation prevents GUI freezing

### Professional Output
- Formatted results with engineering notation
- Detailed calculation steps and explanations
- Publication-quality plots with proper labeling
- Export-ready visualizations

## Applications

This tool is suitable for:

- **Educational purposes**: Understanding synchronous generator behavior
- **Engineering analysis**: Design and performance evaluation
- **Research**: Parameter sensitivity studies
- **Laboratory work**: Comparison with experimental data
- **Power system studies**: Generator modeling and simulation

## Mathematical Background

### Salient-Pole Theory
Salient-pole machines have different reactances in d and q axes due to non-uniform air gap, leading to:
- Reluctance torque component
- Complex phasor relationships
- Two-reaction theory application

### Slip Test Method
The slip test determines Xsd and Xsq by:
1. Running unexcited generator at near-synchronous speed
2. Measuring current variations as rotor poles align with stator field
3. Maximum current → q-axis aligned (lower reactance)
4. Minimum current → d-axis aligned (higher reactance)

## Limitations

- Armature resistance neglected (Ra ≈ 0)
- Linear magnetization curve assumed
- Simplified transient model
- No saturation effects included
- Steady-state focused analysis

## Future Enhancements

Potential improvements:
- [ ] Saturation characteristic inclusion
- [ ] Armature resistance effects
- [ ] Subtransient dynamics
- [ ] Fault analysis capabilities
- [ ] Load flow integration
- [ ] Data import/export (CSV, Excel)
- [ ] Custom report generation
- [ ] Multi-machine simulation

## License

Educational and non-commercial use permitted.

## Author

Created for electrical engineering education and practical analysis.

## References

- Fitzgerald, Kingsley, Umans: "Electric Machinery"
- Kundur: "Power System Stability and Control"
- IEEE Standards for Synchronous Machines
- Chapman: "Electric Machinery Fundamentals"

## Support

For issues or questions:
1. Check documentation in Help menu
2. Review calculation methodology
3. Verify input parameters are within reasonable ranges
4. Ensure all dependencies are installed

---

**Version:** 1.0
**Last Updated:** 2025
**Platform:** Cross-platform (Windows, macOS, Linux)
**Language:** Python 3.7+
