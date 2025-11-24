# Advanced Electrical Engineering Simulator

A comprehensive Python application with Tkinter GUI for electrical engineering calculations and dynamic machine simulations.

## Features

### 1. Transformer Regulation Calculator
- Calculate voltage regulation for transformers
- Visualize regulation vs power factor
- Phasor diagrams
- Impedance triangles
- Regulation vs load curves
- Detailed results with efficiency calculations

### 2. Dynamic Machine Simulation
- **DC Motor** - Current and speed dynamics
- **Synchronous Generator** - Rotor angle and power
- **Induction Motor** - Torque-speed characteristics
- **RL Circuit** - Basic transient analysis

### 3. ODE Solvers
- **RK45** - 4th/5th order Runge-Kutta (high accuracy)
- **Euler** - Forward Euler method (educational)
- Real-time visualization
- Adjustable time steps and simulation duration

### 4. Advanced Features
- Responsive design with auto-scaling
- Real-time plotting during simulation
- Start/Stop/Reset controls
- Multiple machine models
- Professional GUI with tabs

## Installation

### Prerequisites
- Python 3.7 or higher
- tkinter (usually included with Python)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### For Ubuntu/Debian (if tkinter is missing):
```bash
sudo apt-get install python3-tk
```

### For macOS:
```bash
brew install python-tk
```

## Usage

### Run the Application
```bash
python3 electrical_engineering_simulator.py
```

### Transformer Regulation Tab
1. Enter transformer parameters (rating, voltages, resistances, reactances)
2. Set power factor and type (lagging/leading/unity)
3. Click "Calculate Regulation"
4. View detailed results and visualizations

### Dynamic Simulation Tab
1. Select machine type (DC Motor, Sync Gen, Induction Motor, RL Circuit)
2. Configure machine parameters using input fields
3. Choose ODE solver (RK45 or Euler)
4. Set simulation time and time step
5. Click "Start" to run simulation
6. Watch real-time plots update
7. Use "Stop" to pause or "Reset" to clear

## Transformer Problem Solution

**Problem:** A 30 kVA, 6000/230 V transformer has:
- Primary resistance: 10 Ω
- Secondary resistance: 0.016 Ω
- Total primary reactance: 23 Ω
- Power factor: 0.8 lagging

**Solution:**
```
Turn ratio (a) = 6000/230 = 26.087
R₂' = 0.016 × (26.087)² = 10.89 Ω
Total R = 10 + 10.89 = 20.89 Ω
Total X = 23 Ω
Primary current = 30000/6000 = 5 A

Regulation = (I₁ × (R × cos(φ) + X × sin(φ))) / V₁ × 100
           = (5 × (20.89 × 0.8 + 23 × 0.6)) / 6000 × 100
           = (5 × 30.512) / 6000 × 100
           = 2.543%
```

**Answer: 2.54% regulation**

## Technical Details

### Differential Equations Implemented

#### DC Motor
```
di/dt = (V - R·i - Ke·ω) / L
dω/dt = (Kt·i - B·ω - TL) / J
```

#### Synchronous Generator
```
dδ/dt = Δω
dΔω/dt = (Tm - Pe - D·Δω) / J
```

#### Induction Motor
```
di/dt = (V - Rs·i - M·ω·s) / Ls
dω/dt = (Te - TL) / J
```

#### RL Circuit
```
di/dt = (V - R·i) / L
```

## Window Features

- **Auto-scaling:** Window resizes automatically adjust plots
- **Responsive layout:** Grid-based responsive design
- **Real-time updates:** Plots update during simulation (50 fps)
- **Thread-safe:** Simulations run in separate threads
- **Professional styling:** Modern UI with organized controls

## Code Structure

```
electrical_engineering_simulator.py
├── ElectricalEngineeringSimulator (Main Class)
│   ├── Transformer Tab
│   │   ├── calculate_transformer_regulation()
│   │   └── update_transformer_plot()
│   ├── Dynamic Simulation Tab
│   │   ├── dc_motor_dynamics()
│   │   ├── synchronous_generator_dynamics()
│   │   ├── induction_motor_dynamics()
│   │   ├── rl_circuit_dynamics()
│   │   ├── euler_solve()
│   │   └── run_simulation()
│   └── GUI Management
│       ├── on_window_resize()
│       ├── start_simulation()
│       ├── stop_simulation_func()
│       └── reset_simulation()
```

## Tips for Use

1. **Transformer Calculator:**
   - Start with default values to see example
   - Experiment with different power factors
   - Compare lagging vs leading behavior

2. **Dynamic Simulation:**
   - Use RK45 for accurate results
   - Use Euler for educational/comparison
   - Try different time steps to see effect
   - Smaller time steps = more accurate but slower

3. **Performance:**
   - Reduce simulation time for faster results
   - Increase time step for quicker preview
   - Use smaller window for faster rendering

## Troubleshooting

**Issue:** Tkinter not found
- **Solution:** Install python3-tk package for your OS

**Issue:** Slow simulation
- **Solution:** Increase time step or reduce simulation time

**Issue:** Plot not updating
- **Solution:** Ensure simulation is running (check status)

**Issue:** Values seem incorrect
- **Solution:** Check parameter units (V, Ω, H, kg·m², etc.)

## Educational Value

This simulator is designed for:
- Electrical engineering students
- Power systems analysis
- Control systems study
- Understanding ODE solvers
- Practical machine behavior visualization

## Future Enhancements

- Export results to CSV/PDF
- Load/save parameter presets
- More machine types
- 3-phase systems
- Harmonic analysis
- Frequency response plots

## Author

Created for electrical engineering education and practical analysis.

## License

Free to use for educational purposes.
