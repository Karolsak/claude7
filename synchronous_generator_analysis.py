#!/usr/bin/env python3
"""
Advanced Synchronous Generator Analysis and Simulation Tool
Solves salient-pole synchronous generator problems with dynamic simulation
"""

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from scipy.integrate import solve_ivp
import threading
import time
from datetime import datetime

class SynchronousGeneratorSolver:
    """Core calculation engine for synchronous generator analysis"""

    def __init__(self):
        # Nominal parameters
        self.Sn = 50e3  # VA
        self.V1Ln = 380  # V (line-to-line)
        self.fn = 60  # Hz
        self.nn = 1800  # rpm
        self.cos_phi_n = 0.82

        # Laboratory test data
        self.Vs = 115  # V (slip test voltage)
        self.fs = 60  # Hz
        self.n_slip = 1768  # rpm
        self.Imax = 22.2  # A
        self.Imin = 11.3  # A
        self.Rf = 0.8  # Ω at reference temperature
        self.If0 = 10.5  # A (no-load field current)
        self.t_ref = 20  # °C (reference temperature)
        self.alpha_cu = 0.00393  # Copper temperature coefficient

        # Calculated values
        self.Xsd = None
        self.Xsq = None
        self.Ifn = None
        self.Vf_nominal = None

    def calculate_synchronous_reactances(self):
        """Calculate Xsd and Xsq using slip test method"""
        # For slip test, voltage per phase
        V_phase = self.Vs / np.sqrt(3)

        # Xsd corresponds to minimum current (d-axis)
        self.Xsd = V_phase / self.Imin

        # Xsq corresponds to maximum current (q-axis)
        self.Xsq = V_phase / self.Imax

        return self.Xsd, self.Xsq

    def calculate_nominal_field_current(self):
        """Calculate nominal field excitation current"""
        # Phase voltage at nominal conditions
        V1n_phase = self.V1Ln / np.sqrt(3)

        # Nominal current
        In = self.Sn / (np.sqrt(3) * self.V1Ln)

        # Power angle (initial estimate using simplified method)
        phi_n = np.arccos(self.cos_phi_n)

        # Iterative solution for power angle delta
        delta = 0
        for iteration in range(20):
            # Current components in d-q frame
            Id = In * np.sin(phi_n + delta)
            Iq = In * np.cos(phi_n + delta)

            # Internal voltage (EMF)
            Ed = V1n_phase * np.sin(delta) - self.Xsq * Iq
            Eq = V1n_phase * np.cos(delta) + self.Xsd * Id

            # Update power angle
            delta_new = np.arctan2(Ed, Eq)

            if abs(delta_new - delta) < 1e-6:
                break
            delta = delta_new

        # Internal EMF magnitude
        En = np.sqrt(Ed**2 + Eq**2)

        # Field current (proportional to EMF, assuming linear magnetization)
        self.Ifn = self.If0 * (En / V1n_phase)

        return self.Ifn, delta, Id, Iq, En

    def calculate_field_voltage(self, temperature=120):
        """Calculate field voltage at specified temperature"""
        # Adjust resistance for temperature
        Rf_temp = self.Rf * (1 + self.alpha_cu * (temperature - self.t_ref))

        # Voltage across field winding
        self.Vf_nominal = self.Ifn * Rf_temp

        return self.Vf_nominal, Rf_temp

    def solve_all(self, temperature=120):
        """Complete solution of the problem"""
        results = {}

        # Part (a): Synchronous reactances
        Xsd, Xsq = self.calculate_synchronous_reactances()
        results['Xsd'] = Xsd
        results['Xsq'] = Xsq

        # Part (b): Nominal field current
        Ifn, delta, Id, Iq, En = self.calculate_nominal_field_current()
        results['Ifn'] = Ifn
        results['delta'] = np.degrees(delta)
        results['Id'] = Id
        results['Iq'] = Iq
        results['En'] = En

        # Part (c): Field voltage at temperature
        Vf, Rf_temp = self.calculate_field_voltage(temperature)
        results['Vf'] = Vf
        results['Rf_temp'] = Rf_temp
        results['temperature'] = temperature

        return results


class SynchronousGeneratorDynamics:
    """Dynamic simulation of synchronous generator"""

    def __init__(self, params):
        self.params = params

        # Machine parameters
        self.Xsd = params.get('Xsd', 6.63)
        self.Xsq = params.get('Xsq', 3.46)
        self.Ra = params.get('Ra', 0.1)  # Small armature resistance
        self.J = params.get('J', 0.5)  # Moment of inertia (kg·m²)
        self.D = params.get('D', 0.01)  # Damping coefficient
        self.p = params.get('p', 2)  # Number of pole pairs

        # Nominal values
        self.Vn = params.get('Vn', 380/np.sqrt(3))
        self.wn = 2 * np.pi * params.get('fn', 60)
        self.If = params.get('If', 10.5)

        # Load parameters
        self.P_load = params.get('P_load', 40e3)
        self.cos_phi = params.get('cos_phi', 0.82)

    def generator_ode(self, t, y, Tm, Vf):
        """
        Differential equations for synchronous generator
        State vector: y = [delta, omega, Eq_prime, Id, Iq]
        delta: rotor angle (rad)
        omega: rotor speed (rad/s)
        Eq_prime: q-axis transient voltage
        Id, Iq: d-q axis currents
        """
        delta, omega, Eq_prime, Id, Iq = y

        # Electrical torque
        Te = Eq_prime * Iq + (self.Xsd - self.Xsq) * Id * Iq

        # Mechanical equation
        ddelta_dt = omega - self.wn
        domega_dt = (1/self.J) * (Tm - Te - self.D * (omega - self.wn))

        # Simplified electrical transients (first-order model)
        Tdo_prime = 1.0  # d-axis transient time constant (s)
        Ta = 0.01  # Armature time constant (s)

        # Field voltage effect on Eq'
        Efd = Vf * 0.1  # Field voltage to Efd conversion
        dEq_prime_dt = (1/Tdo_prime) * (Efd - Eq_prime)

        # Current dynamics (simplified)
        V_terminal = self.Vn
        dId_dt = (1/Ta) * (-Id + (V_terminal * np.sin(delta) - Eq_prime) / self.Xsd)
        dIq_dt = (1/Ta) * (-Iq + (V_terminal * np.cos(delta)) / self.Xsq)

        return [ddelta_dt, domega_dt, dEq_prime_dt, dId_dt, dIq_dt]

    def simulate(self, t_span, y0, Tm, Vf, method='RK45'):
        """
        Run dynamic simulation
        t_span: (t_start, t_end)
        y0: initial conditions
        Tm: mechanical torque (constant or callable)
        Vf: field voltage (constant or callable)
        method: 'RK45' or 'Euler'
        """
        if method.upper() == 'RK45':
            # Use scipy's RK45 solver
            sol = solve_ivp(
                lambda t, y: self.generator_ode(t, y, Tm, Vf),
                t_span,
                y0,
                method='RK45',
                dense_output=True,
                max_step=0.01
            )
            return sol
        else:
            # Euler method
            t_start, t_end = t_span
            dt = 0.001  # Time step
            t_eval = np.arange(t_start, t_end, dt)
            y = np.zeros((len(y0), len(t_eval)))
            y[:, 0] = y0

            for i in range(1, len(t_eval)):
                dydt = self.generator_ode(t_eval[i-1], y[:, i-1], Tm, Vf)
                y[:, i] = y[:, i-1] + np.array(dydt) * dt

            return {'t': t_eval, 'y': y}


class AdvancedGeneratorGUI:
    """Advanced Tkinter GUI for synchronous generator analysis"""

    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Synchronous Generator Analysis & Simulation")
        self.root.geometry("1400x900")

        # Solver and dynamics objects
        self.solver = SynchronousGeneratorSolver()
        self.dynamics = None

        # Simulation control
        self.simulation_running = False
        self.simulation_thread = None
        self.sim_data = None

        # Setup GUI
        self.setup_styles()
        self.create_menu()
        self.create_main_layout()

        # Bind resize event
        self.root.bind('<Configure>', self.on_window_resize)

    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Custom styles
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'), foreground='#2c3e50')
        style.configure('Subtitle.TLabel', font=('Arial', 10, 'bold'), foreground='#34495e')
        style.configure('Header.TLabel', font=('Arial', 11, 'bold'), background='#3498db',
                       foreground='white', padding=5)
        style.configure('Result.TLabel', font=('Courier', 9), background='#ecf0f1')

    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Results", command=self.save_results)
        file_menu.add_command(label="Export Plot", command=self.export_plot)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Solve Problem", command=self.solve_problem)
        analysis_menu.add_command(label="Phasor Diagram", command=self.show_phasor_diagram)
        analysis_menu.add_command(label="Characteristic Curves", command=self.show_characteristics)

        # Simulation menu
        sim_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Simulation", menu=sim_menu)
        sim_menu.add_command(label="Start Dynamic Simulation", command=self.start_simulation)
        sim_menu.add_command(label="Stop Simulation", command=self.stop_simulation)
        sim_menu.add_command(label="Reset", command=self.reset_simulation)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_documentation)

    def create_main_layout(self):
        """Create main application layout"""
        # Main container with paned window for resizable sections
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel: Input parameters and controls
        left_panel = ttk.Frame(self.paned_window, relief=tk.RAISED, borderwidth=2)
        self.paned_window.add(left_panel, weight=1)

        # Right panel: Visualization and results
        right_panel = ttk.Frame(self.paned_window, relief=tk.RAISED, borderwidth=2)
        self.paned_window.add(right_panel, weight=3)

        # Setup left panel
        self.create_input_panel(left_panel)

        # Setup right panel
        self.create_visualization_panel(right_panel)

    def create_input_panel(self, parent):
        """Create input parameters panel"""
        # Scrollable frame
        canvas = tk.Canvas(parent, bg='white')
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.input_frame = ttk.Frame(canvas)

        self.input_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.input_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Title
        ttk.Label(self.input_frame, text="Input Parameters", style='Title.TLabel').pack(pady=10)

        # Nominal Parameters Section
        self.create_parameter_section("Nominal Parameters", [
            ("Apparent Power (kVA)", 'Sn', 50, 1, 1000),
            ("Line Voltage (V)", 'V1Ln', 380, 100, 1000),
            ("Frequency (Hz)", 'fn', 60, 50, 400),
            ("Speed (rpm)", 'nn', 1800, 100, 3600),
            ("Power Factor", 'cos_phi_n', 0.82, 0.5, 1.0),
        ])

        # Laboratory Test Parameters
        self.create_parameter_section("Laboratory Test Data", [
            ("Test Voltage Vs (V)", 'Vs', 115, 50, 500),
            ("Test Frequency (Hz)", 'fs', 60, 50, 400),
            ("Test Speed (rpm)", 'n_slip', 1768, 100, 3600),
            ("Max Current (A)", 'Imax', 22.2, 1, 100),
            ("Min Current (A)", 'Imin', 11.3, 1, 100),
            ("Field Resistance (Ω)", 'Rf', 0.8, 0.1, 10),
            ("No-load Field Current (A)", 'If0', 10.5, 1, 50),
        ])

        # Operating Conditions
        self.create_parameter_section("Operating Conditions", [
            ("Temperature (°C)", 'temperature', 120, 20, 200),
            ("Load Power (kW)", 'P_load', 40, 0, 100),
            ("Mechanical Torque (Nm)", 'Tm', 250, 0, 500),
        ])

        # Dynamic Simulation Parameters
        self.create_parameter_section("Simulation Parameters", [
            ("Inertia J (kg·m²)", 'J', 0.5, 0.1, 5.0),
            ("Damping D", 'D', 0.01, 0.001, 0.1),
            ("Simulation Time (s)", 't_sim', 5.0, 0.1, 20.0),
        ])

        # Control Buttons
        button_frame = ttk.LabelFrame(self.input_frame, text="Controls", padding=10)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Solve Problem",
                  command=self.solve_problem, style='Accent.TButton').pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Start Simulation",
                  command=self.start_simulation).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Stop Simulation",
                  command=self.stop_simulation).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Reset",
                  command=self.reset_simulation).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Clear Results",
                  command=self.clear_results).pack(fill=tk.X, pady=2)

        # Simulation method selection
        method_frame = ttk.Frame(button_frame)
        method_frame.pack(fill=tk.X, pady=5)
        ttk.Label(method_frame, text="Method:").pack(side=tk.LEFT)
        self.sim_method = tk.StringVar(value="RK45")
        ttk.Radiobutton(method_frame, text="RK45", variable=self.sim_method,
                       value="RK45").pack(side=tk.LEFT)
        ttk.Radiobutton(method_frame, text="Euler", variable=self.sim_method,
                       value="Euler").pack(side=tk.LEFT)

    def create_parameter_section(self, title, parameters):
        """Create a section of parameters with sliders"""
        frame = ttk.LabelFrame(self.input_frame, text=title, padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

        if not hasattr(self, 'params'):
            self.params = {}
        if not hasattr(self, 'sliders'):
            self.sliders = {}

        for label, key, default, min_val, max_val in parameters:
            param_frame = ttk.Frame(frame)
            param_frame.pack(fill=tk.X, pady=3)

            # Label
            ttk.Label(param_frame, text=label, width=25, anchor='w').pack(side=tk.LEFT)

            # Value display
            self.params[key] = tk.DoubleVar(value=default)
            value_label = ttk.Label(param_frame, textvariable=self.params[key],
                                   width=8, anchor='e', relief=tk.SUNKEN)
            value_label.pack(side=tk.RIGHT, padx=2)

            # Slider
            slider = ttk.Scale(param_frame, from_=min_val, to=max_val,
                             variable=self.params[key], orient=tk.HORIZONTAL)
            slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)
            self.sliders[key] = slider

            # Format value display
            self.params[key].trace('w', lambda *args, k=key:
                                  self.params[k].set(round(self.params[k].get(), 3)))

    def create_visualization_panel(self, parent):
        """Create visualization panel with plots and results"""
        # Notebook for multiple tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Results
        self.results_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.results_tab, text="Results")
        self.create_results_display(self.results_tab)

        # Tab 2: Dynamic Simulation
        self.sim_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.sim_tab, text="Dynamic Simulation")
        self.create_simulation_display(self.sim_tab)

        # Tab 3: Phasor Diagram
        self.phasor_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.phasor_tab, text="Phasor Diagram")
        self.create_phasor_display(self.phasor_tab)

        # Tab 4: Characteristics
        self.char_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.char_tab, text="Characteristics")
        self.create_characteristics_display(self.char_tab)

    def create_results_display(self, parent):
        """Create results display area"""
        # Results text area
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(text_frame, text="Calculation Results",
                 style='Header.TLabel').pack(fill=tk.X)

        self.results_text = scrolledtext.ScrolledText(
            text_frame,
            font=('Courier', 10),
            bg='#f8f9fa',
            fg='#2c3e50',
            wrap=tk.WORD
        )
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=5)

    def create_simulation_display(self, parent):
        """Create dynamic simulation display"""
        # Matplotlib figure
        self.sim_fig = Figure(figsize=(10, 8), dpi=100)
        self.sim_canvas = FigureCanvasTkAgg(self.sim_fig, parent)
        self.sim_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Toolbar
        toolbar = NavigationToolbar2Tk(self.sim_canvas, parent)
        toolbar.update()

        # Create subplots
        self.ax_delta = self.sim_fig.add_subplot(3, 2, 1)
        self.ax_omega = self.sim_fig.add_subplot(3, 2, 2)
        self.ax_Eq = self.sim_fig.add_subplot(3, 2, 3)
        self.ax_Id = self.sim_fig.add_subplot(3, 2, 4)
        self.ax_Iq = self.sim_fig.add_subplot(3, 2, 5)
        self.ax_Te = self.sim_fig.add_subplot(3, 2, 6)

        self.sim_fig.tight_layout()

    def create_phasor_display(self, parent):
        """Create phasor diagram display"""
        self.phasor_fig = Figure(figsize=(8, 8), dpi=100)
        self.phasor_canvas = FigureCanvasTkAgg(self.phasor_fig, parent)
        self.phasor_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.ax_phasor = self.phasor_fig.add_subplot(111)
        self.ax_phasor.set_aspect('equal')
        self.ax_phasor.grid(True, alpha=0.3)

    def create_characteristics_display(self, parent):
        """Create characteristic curves display"""
        self.char_fig = Figure(figsize=(10, 8), dpi=100)
        self.char_canvas = FigureCanvasTkAgg(self.char_fig, parent)
        self.char_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.ax_char1 = self.char_fig.add_subplot(2, 2, 1)
        self.ax_char2 = self.char_fig.add_subplot(2, 2, 2)
        self.ax_char3 = self.char_fig.add_subplot(2, 2, 3)
        self.ax_char4 = self.char_fig.add_subplot(2, 2, 4)

    def solve_problem(self):
        """Solve the synchronous generator problem"""
        try:
            # Update solver parameters from GUI
            self.update_solver_params()

            # Solve
            temperature = self.params['temperature'].get()
            results = self.solver.solve_all(temperature)

            # Display results
            self.display_results(results)

            # Update phasor diagram
            self.update_phasor_diagram(results)

            # Update characteristics
            self.update_characteristics()

        except Exception as e:
            messagebox.showerror("Error", f"Calculation error: {str(e)}")

    def update_solver_params(self):
        """Update solver parameters from GUI inputs"""
        self.solver.Sn = self.params['Sn'].get() * 1e3
        self.solver.V1Ln = self.params['V1Ln'].get()
        self.solver.fn = self.params['fn'].get()
        self.solver.nn = self.params['nn'].get()
        self.solver.cos_phi_n = self.params['cos_phi_n'].get()
        self.solver.Vs = self.params['Vs'].get()
        self.solver.fs = self.params['fs'].get()
        self.solver.n_slip = self.params['n_slip'].get()
        self.solver.Imax = self.params['Imax'].get()
        self.solver.Imin = self.params['Imin'].get()
        self.solver.Rf = self.params['Rf'].get()
        self.solver.If0 = self.params['If0'].get()

    def display_results(self, results):
        """Display calculation results"""
        self.results_text.delete(1.0, tk.END)

        output = f"""
{'='*70}
SYNCHRONOUS GENERATOR ANALYSIS RESULTS
{'='*70}
Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PROBLEM STATEMENT:
Salient-pole synchronous generator with nominal parameters:
  - Apparent Power:     Sn = {self.solver.Sn/1e3:.1f} kVA
  - Line Voltage:       V1Ln = {self.solver.V1Ln:.1f} V
  - Frequency:          fn = {self.solver.fn:.1f} Hz
  - Speed:              nn = {self.solver.nn:.0f} rpm
  - Power Factor:       cos(φn) = {self.solver.cos_phi_n:.3f}

LABORATORY TEST DATA:
  - Test Voltage:       Vs = {self.solver.Vs:.1f} V
  - Test Speed:         n = {self.solver.n_slip:.0f} rpm
  - Maximum Current:    Imax = {self.solver.Imax:.2f} A
  - Minimum Current:    Imin = {self.solver.Imin:.2f} A
  - Field Resistance:   Rf = {self.solver.Rf:.2f} Ω (at {self.solver.t_ref}°C)
  - No-load Field I:    If0 = {self.solver.If0:.2f} A

{'='*70}
SOLUTIONS:
{'='*70}

(a) SYNCHRONOUS REACTANCES (Slip Test Method):

    Using the slip test, the extremum currents correspond to:
    - Minimum current occurs when d-axis aligned → Xsd
    - Maximum current occurs when q-axis aligned → Xsq

    Phase voltage: V_phase = Vs/√3 = {self.solver.Vs/np.sqrt(3):.3f} V

    ➤ Xsd = V_phase / Imin = {results['Xsd']:.4f} Ω
    ➤ Xsq = V_phase / Imax = {results['Xsq']:.4f} Ω

    Saliency ratio: Xsd/Xsq = {results['Xsd']/results['Xsq']:.3f}

{'='*70}

(b) NOMINAL FIELD EXCITATION CURRENT:

    Nominal phase voltage: V1n = {self.solver.V1Ln/np.sqrt(3):.2f} V
    Nominal current: In = {self.solver.Sn/(np.sqrt(3)*self.solver.V1Ln):.3f} A
    Power factor angle: φn = {np.degrees(np.arccos(self.solver.cos_phi_n)):.2f}°

    Current components (d-q frame):
    - Id (direct axis):      {results['Id']:.4f} A
    - Iq (quadrature axis):  {results['Iq']:.4f} A

    Power angle: δ = {results['delta']:.3f}°
    Internal EMF: En = {results['En']:.3f} V

    Using linear magnetization:
    Ifn = If0 × (En / V1n)

    ➤ Ifn = {results['Ifn']:.4f} A

{'='*70}

(c) FIELD WINDING VOLTAGE AT ELEVATED TEMPERATURE:

    Operating temperature: T = {results['temperature']:.0f}°C
    Temperature coefficient (Copper): α = {self.solver.alpha_cu:.6f} /°C

    Resistance at {results['temperature']:.0f}°C:
    Rf(T) = Rf(20°C) × [1 + α(T - 20°C)]
    Rf({results['temperature']:.0f}°C) = {results['Rf_temp']:.4f} Ω

    Field voltage:
    Vf = Ifn × Rf(T)

    ➤ Vf = {results['Vf']:.4f} V

{'='*70}

PERFORMANCE PARAMETERS:
{'='*70}
Nominal Power Output:    P = {self.solver.Sn * self.solver.cos_phi_n / 1e3:.2f} kW
Nominal Reactive Power:  Q = {self.solver.Sn * np.sin(np.arccos(self.solver.cos_phi_n)) / 1e3:.2f} kVAR
Synchronous Speed:       ns = {120 * self.solver.fn / 2:.0f} rpm (assuming p=2)
Field Power Loss:        Pf = {results['Ifn']**2 * results['Rf_temp']:.2f} W

{'='*70}
NOTES:
- Armature resistance Ra is neglected in calculations
- Linear magnetization curve assumed
- Calculations valid for steady-state operation
{'='*70}
"""

        self.results_text.insert(1.0, output)
        self.results_text.see(1.0)

    def update_phasor_diagram(self, results):
        """Draw phasor diagram"""
        self.ax_phasor.clear()

        # Get values
        V_phase = self.solver.V1Ln / np.sqrt(3)
        In = self.solver.Sn / (np.sqrt(3) * self.solver.V1Ln)
        phi = np.arccos(self.solver.cos_phi_n)
        delta = np.radians(results['delta'])

        # Phasors (using V as reference at 0°)
        V = V_phase
        I = In * np.exp(-1j * phi)
        jXsq_Iq = 1j * results['Xsq'] * results['Iq']
        jXsd_Id = 1j * results['Xsd'] * results['Id']
        E = results['En'] * np.exp(1j * delta)

        # Plot phasors
        self.ax_phasor.quiver(0, 0, V.real, V.imag, angles='xy', scale_units='xy',
                             scale=1, color='blue', width=0.006, label='V (Terminal Voltage)')
        self.ax_phasor.quiver(0, 0, I.real, I.imag, angles='xy', scale_units='xy',
                             scale=1, color='red', width=0.006, label='I (Armature Current)')
        self.ax_phasor.quiver(V.real, V.imag, jXsq_Iq.real, jXsq_Iq.imag,
                             angles='xy', scale_units='xy', scale=1,
                             color='green', width=0.005, label='jXsq·Iq')
        self.ax_phasor.quiver(0, 0, E.real, E.imag, angles='xy', scale_units='xy',
                             scale=1, color='purple', width=0.006, label='E (Internal EMF)')

        # Annotations
        self.ax_phasor.annotate(f'V = {V_phase:.1f}V', xy=(V.real, V.imag),
                               xytext=(10, 10), textcoords='offset points')
        self.ax_phasor.annotate(f'I = {In:.2f}A', xy=(I.real, I.imag),
                               xytext=(10, -20), textcoords='offset points')
        self.ax_phasor.annotate(f'E = {results["En"]:.1f}V', xy=(E.real, E.imag),
                               xytext=(10, 10), textcoords='offset points')

        # Angle annotations
        self.ax_phasor.plot([0, V.real*1.3], [0, 0], 'k--', alpha=0.3, linewidth=0.5)

        self.ax_phasor.set_xlabel('Real Part', fontsize=10)
        self.ax_phasor.set_ylabel('Imaginary Part', fontsize=10)
        self.ax_phasor.set_title('Phasor Diagram - Synchronous Generator', fontsize=12, fontweight='bold')
        self.ax_phasor.legend(loc='upper right', fontsize=8)
        self.ax_phasor.grid(True, alpha=0.3)
        self.ax_phasor.set_aspect('equal')

        # Set limits
        max_val = max(abs(V), abs(E)) * 1.3
        self.ax_phasor.set_xlim(-max_val*0.3, max_val)
        self.ax_phasor.set_ylim(-max_val*0.5, max_val*0.8)

        self.phasor_canvas.draw()

    def update_characteristics(self):
        """Plot characteristic curves"""
        # Clear axes
        for ax in [self.ax_char1, self.ax_char2, self.ax_char3, self.ax_char4]:
            ax.clear()

        # Calculate characteristics
        V_phase = self.solver.V1Ln / np.sqrt(3)

        # 1. V-curve (Ia vs If at constant power)
        If_range = np.linspace(5, 20, 50)
        Ia_values = []
        pf_values = []

        for If in If_range:
            # Simplified model: assume linear relation
            E = V_phase * (If / self.solver.If0)
            # For constant power, approximate current
            Ia = self.solver.Sn / (np.sqrt(3) * self.solver.V1Ln)
            pf = min(1.0, self.solver.cos_phi_n * (self.solver.If0 / If)**0.3)
            Ia_values.append(Ia * (1 + 0.2 * abs(If - self.solver.Ifn) / self.solver.Ifn))
            pf_values.append(pf)

        self.ax_char1.plot(If_range, Ia_values, 'b-', linewidth=2)
        self.ax_char1.axvline(self.solver.Ifn, color='r', linestyle='--',
                             label=f'Nominal If = {self.solver.Ifn:.2f}A')
        self.ax_char1.set_xlabel('Field Current If (A)')
        self.ax_char1.set_ylabel('Armature Current Ia (A)')
        self.ax_char1.set_title('V-Curve (Constant Power)')
        self.ax_char1.grid(True, alpha=0.3)
        self.ax_char1.legend()

        # 2. Power factor vs If
        self.ax_char2.plot(If_range, pf_values, 'g-', linewidth=2)
        self.ax_char2.axvline(self.solver.Ifn, color='r', linestyle='--')
        self.ax_char2.set_xlabel('Field Current If (A)')
        self.ax_char2.set_ylabel('Power Factor')
        self.ax_char2.set_title('Power Factor Characteristic')
        self.ax_char2.grid(True, alpha=0.3)
        self.ax_char2.set_ylim([0, 1.1])

        # 3. External characteristic (V vs Ia)
        Ia_range = np.linspace(0, 1.5 * self.solver.Sn / (np.sqrt(3) * self.solver.V1Ln), 50)
        V_values = []

        for Ia in Ia_range:
            # Voltage drop due to reactance
            if self.solver.Xsd:
                V_drop = Ia * (self.solver.Xsd + self.solver.Xsq) / 2
                V_terminal = max(0, V_phase - V_drop)
            else:
                V_terminal = V_phase * (1 - 0.2 * Ia / (self.solver.Sn / (np.sqrt(3) * self.solver.V1Ln)))
            V_values.append(V_terminal)

        self.ax_char3.plot(Ia_range, V_values, 'm-', linewidth=2)
        self.ax_char3.axhline(V_phase, color='b', linestyle='--', label='No-load Voltage')
        self.ax_char3.set_xlabel('Armature Current Ia (A)')
        self.ax_char3.set_ylabel('Terminal Voltage (V)')
        self.ax_char3.set_title('External Characteristic')
        self.ax_char3.grid(True, alpha=0.3)
        self.ax_char3.legend()

        # 4. Regulation curve
        load_percent = np.linspace(0, 150, 50)
        regulation = []

        for load in load_percent:
            # Voltage regulation percentage
            if load == 0:
                reg = 0
            else:
                reg = (5 + load * 0.15)  # Approximate model
            regulation.append(reg)

        self.ax_char4.plot(load_percent, regulation, 'r-', linewidth=2)
        self.ax_char4.axvline(100, color='g', linestyle='--', label='Full Load')
        self.ax_char4.set_xlabel('Load (%)')
        self.ax_char4.set_ylabel('Voltage Regulation (%)')
        self.ax_char4.set_title('Voltage Regulation')
        self.ax_char4.grid(True, alpha=0.3)
        self.ax_char4.legend()

        self.char_fig.tight_layout()
        self.char_canvas.draw()

    def start_simulation(self):
        """Start dynamic simulation"""
        if self.simulation_running:
            messagebox.showinfo("Info", "Simulation already running")
            return

        try:
            # Update solver parameters
            self.update_solver_params()

            # Calculate reactances if not done
            if self.solver.Xsd is None:
                self.solver.calculate_synchronous_reactances()
                self.solver.calculate_nominal_field_current()

            # Setup dynamics
            params = {
                'Xsd': self.solver.Xsd,
                'Xsq': self.solver.Xsq,
                'Ra': 0.1,
                'J': self.params['J'].get(),
                'D': self.params['D'].get(),
                'p': 2,
                'Vn': self.solver.V1Ln / np.sqrt(3),
                'fn': self.solver.fn,
                'If': self.solver.Ifn,
                'P_load': self.params['P_load'].get() * 1e3,
                'cos_phi': self.solver.cos_phi_n
            }

            self.dynamics = SynchronousGeneratorDynamics(params)

            # Initial conditions [delta, omega, Eq_prime, Id, Iq]
            y0 = [0.3, 2*np.pi*self.solver.fn, params['Vn'], 0, 0]

            # Mechanical torque and field voltage
            Tm = self.params['Tm'].get()
            Vf = self.solver.Vf_nominal if self.solver.Vf_nominal else 10.0

            # Time span
            t_span = (0, self.params['t_sim'].get())

            # Run simulation in thread
            self.simulation_running = True
            self.simulation_thread = threading.Thread(
                target=self.run_simulation,
                args=(t_span, y0, Tm, Vf, self.sim_method.get())
            )
            self.simulation_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Simulation error: {str(e)}")
            self.simulation_running = False

    def run_simulation(self, t_span, y0, Tm, Vf, method):
        """Run simulation (called in thread)"""
        try:
            # Solve ODE
            sol = self.dynamics.simulate(t_span, y0, Tm, Vf, method)

            # Store results
            if method.upper() == 'RK45':
                t_plot = np.linspace(t_span[0], t_span[1], 500)
                self.sim_data = {
                    't': t_plot,
                    'y': sol.sol(t_plot)
                }
            else:
                self.sim_data = sol

            # Update plot
            self.root.after(0, self.update_simulation_plot)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error",
                                                             f"Simulation failed: {str(e)}"))
        finally:
            self.simulation_running = False

    def update_simulation_plot(self):
        """Update simulation plots"""
        if self.sim_data is None:
            return

        t = self.sim_data['t']
        y = self.sim_data['y']

        # Extract states
        delta = y[0, :]
        omega = y[1, :]
        Eq_prime = y[2, :]
        Id = y[3, :]
        Iq = y[4, :]

        # Calculate torque
        Te = Eq_prime * Iq + (self.dynamics.Xsd - self.dynamics.Xsq) * Id * Iq

        # Plot
        self.ax_delta.clear()
        self.ax_delta.plot(t, np.degrees(delta), 'b-', linewidth=2)
        self.ax_delta.set_ylabel('δ (deg)')
        self.ax_delta.set_title('Rotor Angle')
        self.ax_delta.grid(True, alpha=0.3)

        self.ax_omega.clear()
        self.ax_omega.plot(t, omega/(2*np.pi), 'r-', linewidth=2)
        self.ax_omega.axhline(self.solver.fn, color='k', linestyle='--', alpha=0.5)
        self.ax_omega.set_ylabel('f (Hz)')
        self.ax_omega.set_title('Frequency')
        self.ax_omega.grid(True, alpha=0.3)

        self.ax_Eq.clear()
        self.ax_Eq.plot(t, Eq_prime, 'g-', linewidth=2)
        self.ax_Eq.set_ylabel("E'q (V)")
        self.ax_Eq.set_title('Transient EMF')
        self.ax_Eq.grid(True, alpha=0.3)

        self.ax_Id.clear()
        self.ax_Id.plot(t, Id, 'm-', linewidth=2)
        self.ax_Id.set_ylabel('Id (A)')
        self.ax_Id.set_title('d-axis Current')
        self.ax_Id.grid(True, alpha=0.3)

        self.ax_Iq.clear()
        self.ax_Iq.plot(t, Iq, 'c-', linewidth=2)
        self.ax_Iq.set_xlabel('Time (s)')
        self.ax_Iq.set_ylabel('Iq (A)')
        self.ax_Iq.set_title('q-axis Current')
        self.ax_Iq.grid(True, alpha=0.3)

        self.ax_Te.clear()
        self.ax_Te.plot(t, Te, 'k-', linewidth=2)
        self.ax_Te.set_xlabel('Time (s)')
        self.ax_Te.set_ylabel('Te (Nm)')
        self.ax_Te.set_title('Electrical Torque')
        self.ax_Te.grid(True, alpha=0.3)

        self.sim_fig.tight_layout()
        self.sim_canvas.draw()

    def stop_simulation(self):
        """Stop running simulation"""
        self.simulation_running = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=1.0)

    def reset_simulation(self):
        """Reset simulation"""
        self.stop_simulation()
        self.sim_data = None

        # Clear plots
        for ax in [self.ax_delta, self.ax_omega, self.ax_Eq,
                   self.ax_Id, self.ax_Iq, self.ax_Te]:
            ax.clear()
            ax.grid(True, alpha=0.3)

        self.sim_canvas.draw()

    def clear_results(self):
        """Clear results display"""
        self.results_text.delete(1.0, tk.END)

    def show_phasor_diagram(self):
        """Switch to phasor diagram tab"""
        self.notebook.select(self.phasor_tab)

    def show_characteristics(self):
        """Switch to characteristics tab"""
        self.notebook.select(self.char_tab)

    def save_results(self):
        """Save results to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'generator_results_{timestamp}.txt'

            with open(filename, 'w') as f:
                f.write(self.results_text.get(1.0, tk.END))

            messagebox.showinfo("Success", f"Results saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")

    def export_plot(self):
        """Export current plot"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            current_tab = self.notebook.select()

            if self.sim_tab == self.notebook.nametowidget(current_tab):
                filename = f'simulation_plot_{timestamp}.png'
                self.sim_fig.savefig(filename, dpi=300, bbox_inches='tight')
            elif self.phasor_tab == self.notebook.nametowidget(current_tab):
                filename = f'phasor_diagram_{timestamp}.png'
                self.phasor_fig.savefig(filename, dpi=300, bbox_inches='tight')
            elif self.char_tab == self.notebook.nametowidget(current_tab):
                filename = f'characteristics_{timestamp}.png'
                self.char_fig.savefig(filename, dpi=300, bbox_inches='tight')
            else:
                messagebox.showinfo("Info", "No plot to export in current tab")
                return

            messagebox.showinfo("Success", f"Plot exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def show_about(self):
        """Show about dialog"""
        about_text = """
Advanced Synchronous Generator Analysis Tool
Version 1.0

Features:
• Salient-pole synchronous generator analysis
• Synchronous reactance calculation (slip test method)
• Field excitation current determination
• Temperature-dependent field voltage calculation
• Dynamic simulation with RK45 and Euler methods
• Real-time phasor diagrams
• Characteristic curves visualization
• Professional electrical engineering tool

Developed for educational and engineering purposes.
        """
        messagebox.showinfo("About", about_text)

    def show_documentation(self):
        """Show documentation"""
        doc_text = """
DOCUMENTATION

1. Input Parameters:
   - Adjust sliders to set machine parameters
   - All values update in real-time

2. Problem Solution:
   - Click "Solve Problem" to calculate reactances,
     field current, and voltages
   - Results appear in Results tab

3. Dynamic Simulation:
   - Select RK45 (accurate) or Euler (fast) method
   - Click "Start Simulation" to run
   - View real-time responses in Simulation tab

4. Visualization:
   - Phasor Diagram: shows voltage/current phasors
   - Characteristics: V-curves, regulation, etc.

5. Export:
   - Save results to text file
   - Export plots as PNG images

For more information, consult electrical machines textbooks.
        """

        doc_window = tk.Toplevel(self.root)
        doc_window.title("Documentation")
        doc_window.geometry("600x400")

        text = scrolledtext.ScrolledText(doc_window, font=('Arial', 10), wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(1.0, doc_text)
        text.config(state=tk.DISABLED)

    def on_window_resize(self, event):
        """Handle window resize for auto-scaling"""
        # This is called on any configure event
        # Matplotlib figures will auto-scale due to pack(fill=BOTH, expand=True)
        pass


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = AdvancedGeneratorGUI(root)

    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()


if __name__ == "__main__":
    main()
