# Parallel Synchronous Generators Analysis Tool

## Overview

This is an advanced electrical engineering application for analyzing two non-salient pole rotor synchronous generators operating in parallel. The tool provides both **static load flow analysis** and **dynamic transient simulation** with real-time visualization.

## Problem Statement

### Given Parameters

**Generator A:**
- Nominal Power: 300 kW
- Nominal Voltage: 6000 V (line-to-line)
- Nominal Field Current: 15 A
- d-axis Synchronous Reactance: 1.7 p.u.
- Nominal Power Factor: 0.8 lagging

**Generator B:**
- Nominal Power: 250 kW
- Nominal Voltage: 6000 V (line-to-line)
- Nominal Field Current: 11 A
- d-axis Synchronous Reactance: 1.6 p.u.
- Nominal Power Factor: 0.8 lagging

### Scenarios

#### Scenario A
Calculate the field excitation current of Generator B (IfB) for:
- Total Load: 420 kW at 0.74 power factor lagging
- Generator A Field Current: 14 A
- Each generator delivers 210 kW
- Maintain bus voltage at rated value (6000 V)

#### Scenario B
With additional 100 kW resistive load (unity power factor):
- Keep Generator B operating conditions same as Scenario A
- Calculate new field excitation current for Generator A (IfA)

## Features

### 1. Static Analysis
- **Load Flow Calculations**: Solve for generator field currents and power sharing
- **Per-Unit System**: Automatic conversion and calculations
- **Power Balance**: Verification of active and reactive power
- **Detailed Results**: Comprehensive analysis reports

### 2. Dynamic Simulation
- **Multiple ODE Solvers**:
  - Euler method (simple, fast)
  - RK4 (Runge-Kutta 4th order)
  - RK45 (Runge-Kutta-Fehlberg with adaptive stepping)

- **Real-time Visualization**:
  - Rotor angle dynamics
  - Angular velocity variations
  - Power output changes

- **Interactive Control**:
  - Adjustable mechanical power (sliders)
  - Variable field excitation (sliders)
  - Start/Stop/Reset functionality

### 3. Mathematical Models

#### Generator Model
The synchronous generator is modeled using:

**Swing Equation:**
```
d²δ/dt² = (ω_sync / 2H) * (Pm - Pe - D(ω - ω_sync))
```

**Excitation Dynamics:**
```
dEq'/dt = (E0 - Eq') / Td0'
```

**Electrical Power:**
```
Pe = (Eq' * V / Xd) * sin(δ)
```

Where:
- δ = rotor angle
- ω = angular velocity
- Eq' = transient internal voltage
- H = inertia constant
- D = damping coefficient
- Td0' = d-axis transient time constant

#### Load Sharing
Reactive power sharing based on voltage-droop characteristics:
```
Q ∝ (E - V) / Xsd
```

## Installation

### Requirements
- Python 3.7 or higher
- NumPy
- Matplotlib
- Tkinter (usually included with Python)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install numpy matplotlib
```

## Usage

### Running the Application

```bash
python3 parallel_generators_gui.py
```

### GUI Navigation

The application has 4 main tabs:

#### 1. Static Analysis Tab
- **Input Parameters**: Enter load conditions and generator settings
- **Control Buttons**:
  - "Calculate Scenario A" - Solves for Generator B field current
  - "Calculate Scenario B" - Solves for Generator A field current with additional load
  - "Custom Analysis" - Use your own parameters
  - "Clear Results" - Reset the results display

#### 2. Dynamic Simulation Tab
- **Simulation Control**:
  - Select ODE solver (Euler, RK4, or RK45)
  - Set time step and simulation duration
  - Start/Stop/Reset buttons

- **Real-time Control Sliders**:
  - Generator A: Mechanical Power (0-400 kW) and Field Current (0-30 A)
  - Generator B: Mechanical Power (0-350 kW) and Field Current (0-25 A)

- **Visualization**:
  - Real-time plots of rotor angles, speeds, and power outputs
  - Automatic scaling and updates

#### 3. Generator Parameters Tab
- View detailed generator specifications
- Base values and calculated impedances
- Nominal current and reactances

#### 4. Detailed Results Tab
- Comprehensive analysis reports
- Power balance verification
- Load sharing ratios
- Computational details

### Menu Options

**File Menu:**
- New Analysis - Reset all parameters
- Export Results - Save results to file
- Exit - Close application

**Calculate Menu:**
- Quick access to Scenario A, B, and Custom Analysis

**Simulation Menu:**
- Start/Stop/Reset simulation controls

**Help Menu:**
- About - Application information
- Documentation - Usage guide

## Example Workflow

### Solving Scenario A

1. Launch the application
2. Go to "Static Analysis" tab
3. Click "Calculate Scenario A" button
4. Results appear showing:
   - Generator B field current ≈ 11.2 A
   - Power sharing: 210 kW each
   - Reactive power distribution

### Solving Scenario B

1. Click "Calculate Scenario B" button
2. Results show:
   - New Generator A field current ≈ 16.8 A
   - Generator A picks up additional 100 kW
   - Total load: 520 kW

### Running Dynamic Simulation

1. Go to "Dynamic Simulation" tab
2. Select ODE solver (recommended: RK4 or RK45)
3. Set time step (e.g., 0.01 s) and duration (e.g., 10 s)
4. Click "▶ Start" button
5. Adjust sliders to change mechanical power or field current
6. Observe real-time response in plots
7. Click "⬛ Stop" when done

## Technical Details

### Mathematical Background

#### Per-Unit System
Base values calculated from nominal parameters:
```
I_base = P_n / (√3 * V_n * cos φ_n)
Z_base = V_n / (√3 * I_base)
X_sd = x_sd(p.u.) * Z_base
```

#### Internal Voltage
For unsaturated magnetic circuit (linear):
```
E = k * If
where k = V_rated / If_rated
```

#### Load Flow Solution
Iterative method:
1. Assume initial field currents
2. Calculate internal voltages
3. Compute reactive power from each generator
4. Check power balance
5. Adjust field currents until convergence

### ODE Solvers

**Euler Method:**
- Simplest, fastest
- First-order accuracy
- Use for quick preliminary analysis

**RK4 (4th Order Runge-Kutta):**
- Good balance of speed and accuracy
- Fourth-order accuracy
- Recommended for most simulations

**RK45 (Runge-Kutta-Fehlberg):**
- Adaptive step size
- Fifth-order accuracy with error estimation
- Best for high-precision requirements

## Automatic Scaling and Resizing

The GUI automatically adjusts to window size changes:
- Grid layout with weight configuration
- Matplotlib figures resize automatically
- Responsive text areas and input fields
- Maintains aspect ratios for plots

## Practical Applications

This tool is useful for:
- **Educational purposes**: Understanding generator parallel operation
- **System planning**: Analyzing load sharing strategies
- **Stability studies**: Observing transient behavior
- **Control design**: Testing excitation control algorithms
- **Operator training**: Simulating power system scenarios

## Troubleshooting

### Common Issues

**Import Error:**
```
ModuleNotFoundError: No module named 'numpy'
```
Solution: Install dependencies with `pip install -r requirements.txt`

**Display Issues:**
- Ensure X11 forwarding is enabled if running remotely
- For headless systems, consider using a virtual display

**Simulation not updating:**
- Check that time step is not too large
- Verify simulation duration is sufficient
- Ensure Start button was clicked

## Theory References

### Synchronous Generator Equations

**Voltage Equation:**
```
V_t = E - j*Ia*Xsd
```

**Power Equations:**
```
P = (E*V / Xsd) * sin(δ)
Q = (E*V / Xsd) * cos(δ) - V²/Xsd
```

**Swing Equation (Classical Model):**
```
M * d²δ/dt² + D * dδ/dt = Pm - Pe
```

Where M = 2H/ω_sync is the inertia coefficient

## Advanced Features

### Real-time Parameter Adjustment
- Modify generator parameters during simulation
- Observe immediate system response
- Study effect of excitation and mechanical power changes

### Multi-plot Visualization
- Synchronized time axes
- Independent scaling for each variable
- Grid lines for easy reading
- Legend for generator identification

### Comprehensive Reporting
- Detailed calculation steps
- Power balance verification
- Load sharing analysis
- Per-unit and absolute values

## License

Educational and research use.

## Author

Created for electrical engineering analysis and education.

## Version History

**v1.0** - Initial release
- Static load flow analysis
- Dynamic simulation with multiple ODE solvers
- Real-time control and visualization
- Comprehensive GUI interface

## Contact

For questions or improvements, please refer to the documentation or contact support.

---

**Note**: This tool assumes:
- Unsaturated magnetic circuits (linear E-If relationship)
- Non-salient pole rotors (Xd = Xq)
- Steady-state for static analysis
- Balanced three-phase system
- Wye-connected stator windings
