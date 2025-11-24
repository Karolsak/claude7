# Quick Start Guide - Synchronous Generator Analysis

## 🚀 Getting Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install numpy matplotlib scipy
```

### Step 2: Run the Solver
```bash
python3 synchronous_generator_solver.py
```

### Step 3: View Results ✓
Complete solution with detailed explanations will be displayed!

---

## 📊 What You Get

### **Problem Solved:**
A salient-pole synchronous generator analysis with:
- **Sn = 50 kVA** (Apparent power)
- **V1Ln = 380 V** (Line voltage)
- **fn = 60 Hz** (Frequency)
- **nn = 1800 rpm** (Speed)
- **cos φn = 0.82** (Power factor)

### **Solutions Provided:**

#### (a) Synchronous Reactances
```
Xsd = 5.8757 Ω  (direct-axis)
Xsq = 2.9908 Ω  (quadrature-axis)
```
✓ Calculated using slip test method

#### (b) Nominal Field Excitation Current
```
Ifn = 18.5534 A
```
✓ Using d-q axis transformation and phasor analysis

#### (c) Field Voltage at 120°C
```
Vf = 20.6759 V
```
✓ With temperature-corrected resistance

---

## 🎯 Two Versions Available

### Version 1: Standalone Solver (Recommended for Quick Use)
**File:** `synchronous_generator_solver.py`

**Advantages:**
- ✅ No GUI dependencies required
- ✅ Works on any system with Python + NumPy
- ✅ Detailed step-by-step explanations
- ✅ Complete verification checks
- ✅ Professional formatted output
- ✅ Perfect for reports and documentation

**Run:**
```bash
python3 synchronous_generator_solver.py
```

**Output includes:**
- Full problem statement
- Step-by-step solution for each part
- Mathematical derivations
- Performance parameters
- Verification checks
- Assumptions and notes

---

### Version 2: Advanced GUI Application (For Interactive Analysis)
**File:** `synchronous_generator_analysis.py`

**Requires:**
```bash
# Install Tkinter
sudo apt-get install python3-tk  # Ubuntu/Debian
# macOS and Windows: included with Python
```

**Features:**
- 🎨 Professional graphical interface
- 🎛️ Interactive parameter sliders
- 📈 Real-time phasor diagrams
- 📊 Characteristic curves (V-curves, regulation)
- ⚡ Dynamic simulation with ODE solvers
- 🔄 Start/Stop/Reset controls
- 💾 Export results and plots
- 📐 Auto-scaling responsive design

**Run:**
```bash
python3 synchronous_generator_analysis.py
```

**GUI Tabs:**
1. **Results** - Detailed text output
2. **Dynamic Simulation** - Real-time ODE solving with plots
3. **Phasor Diagram** - Vector representation of voltages/currents
4. **Characteristics** - Performance curves

**Simulation Methods:**
- **RK45** (Runge-Kutta 4-5): High accuracy, adaptive step
- **Euler**: Fast, fixed step, good for real-time

---

## 📝 Example Usage

### Basic Calculation
```bash
# Run standalone solver
python3 synchronous_generator_solver.py

# Output shows complete solution with:
# - Part (a): Xsd and Xsq
# - Part (b): Ifn
# - Part (c): Vf at 120°C
```

### Interactive GUI Session
```bash
# Launch GUI
python3 synchronous_generator_analysis.py

# In GUI:
# 1. Adjust parameters with sliders
# 2. Click "Solve Problem"
# 3. View "Phasor Diagram" tab
# 4. Click "Start Simulation"
# 5. Watch dynamic response
# 6. Export results via File menu
```

---

## 🔧 Advanced Features

### Dynamic Simulation
The GUI version includes a complete dynamic simulator based on:

**State Variables:**
- δ (rotor angle)
- ω (angular velocity)
- E'q (transient EMF)
- Id, Iq (d-q axis currents)

**Differential Equations:**
```
dδ/dt = ω - ωn
dω/dt = (1/J)(Tm - Te - D(ω - ωn))
dE'q/dt = (1/T'do)(Efd - E'q)
dId/dt = (1/Ta)(-Id + (V·sin(δ) - E'q)/Xsd)
dIq/dt = (1/Ta)(-Iq + V·cos(δ)/Xsq)
```

### Parameter Adjustment
All parameters can be adjusted via sliders:
- Nominal ratings
- Laboratory test data
- Operating temperature
- Load conditions
- Mechanical torque
- Inertia and damping

---

## 📚 Files Included

```
claude7/
├── synchronous_generator_solver.py      # Standalone solver (no GUI)
├── synchronous_generator_analysis.py    # Full GUI application
├── requirements.txt                     # Python dependencies
├── README.md                           # Complete documentation
├── SOLUTION_SUMMARY.txt                # Quick reference
└── QUICK_START.md                      # This file
```

---

## 🎓 Educational Value

This tool is perfect for:
- **Students**: Understanding synchronous generator theory
- **Engineers**: Quick parameter calculations
- **Researchers**: Sensitivity analysis
- **Educators**: Interactive demonstrations
- **Lab work**: Comparing with experimental results

---

## ⚡ Key Technical Concepts

### 1. Slip Test Method
Determines Xsd and Xsq by driving unexcited generator near synchronous speed and measuring current variations as poles align with stator field.

### 2. d-q Axis Transformation
Converts three-phase quantities to two-axis rotating reference frame for easier analysis of salient-pole machines.

### 3. Two-Reaction Theory
Accounts for different reluctances in direct and quadrature axes, essential for salient-pole analysis.

### 4. Temperature Correction
Adjusts field resistance using copper temperature coefficient (α = 0.00393 /°C).

---

## 🔍 Verification

All calculations are automatically verified:
- ✅ Power balance
- ✅ Apparent power
- ✅ Current magnitude
- ✅ Saliency ratio range
- ✅ Power angle stability

---

## 💡 Tips

1. **For quick calculations**: Use `synchronous_generator_solver.py`
2. **For exploration**: Use GUI with parameter sliders
3. **For reports**: Copy output from standalone solver
4. **For presentations**: Export plots from GUI
5. **For learning**: Compare both versions

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'numpy'"
```bash
pip install numpy scipy matplotlib
```

### "ModuleNotFoundError: No module named 'tkinter'" (GUI only)
```bash
sudo apt-get install python3-tk  # Ubuntu/Debian
```

### GUI won't start
- Use standalone solver instead: `python3 synchronous_generator_solver.py`
- Standalone version works on all systems

---

## 📖 Further Reading

See `README.md` for:
- Complete feature list
- Detailed technical explanation
- Mathematical background
- Assumptions and limitations
- Future enhancements

---

## ✨ Features Summary

### Standalone Solver:
✅ Works without GUI
✅ Detailed explanations
✅ Step-by-step solution
✅ Verification checks
✅ Professional output

### GUI Application:
✅ Interactive parameters
✅ Real-time visualization
✅ Dynamic simulation
✅ Phasor diagrams
✅ Characteristic curves
✅ Export capabilities

---

## 🎉 You're Ready!

Run the solver and explore synchronous generator analysis:
```bash
python3 synchronous_generator_solver.py
```

For interactive experience (if Tkinter available):
```bash
python3 synchronous_generator_analysis.py
```

**Enjoy analyzing synchronous generators!** ⚡🔌
