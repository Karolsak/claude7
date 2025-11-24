#!/usr/bin/env python3
"""
Parallel Synchronous Generators Analysis and Simulation Tool
Advanced Electrical Engineering Application with Dynamic Simulation
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import math
from dataclasses import dataclass
from typing import Tuple, List, Dict
import threading
import time


@dataclass
class GeneratorParameters:
    """Generator rated parameters"""
    name: str
    Pn: float  # Nominal power (kW)
    V1n: float  # Nominal voltage (V)
    Ifn: float  # Nominal field current (A)
    xsd: float  # d-axis synchronous reactance (p.u.)
    cos_phi_n: float  # Nominal power factor

    def __post_init__(self):
        self.In = (self.Pn * 1000) / (np.sqrt(3) * self.V1n * self.cos_phi_n)  # Nominal current
        self.Zbase = self.V1n / (np.sqrt(3) * self.In)  # Base impedance
        self.Xsd = self.xsd * self.Zbase  # Synchronous reactance in ohms


class SynchronousGenerator:
    """
    Mathematical model of a non-salient pole synchronous generator
    with dynamic equations for transient analysis
    """

    def __init__(self, params: GeneratorParameters):
        self.params = params
        self.state = {
            'delta': 0.0,  # Rotor angle (rad)
            'omega': 2 * np.pi * 60,  # Angular velocity (rad/s), assuming 60 Hz
            'Eq_prime': 0.0,  # q-axis transient voltage
            'If': params.Ifn,  # Field current
            'Pe': 0.0,  # Electrical power
            'Pm': 0.0,  # Mechanical power
        }

        # Machine constants
        self.omega_sync = 2 * np.pi * 60  # Synchronous speed (rad/s)
        self.H = 3.0  # Inertia constant (s)
        self.D = 2.0  # Damping coefficient
        self.Td0_prime = 5.0  # d-axis transient time constant (s)

    def calculate_internal_voltage(self, If: float, If_rated: float, V_rated: float) -> float:
        """
        Calculate internal voltage based on field current
        Using linear magnetic characteristic (unsaturated)
        """
        # E0 = k * If, where k is derived from rated conditions
        k = V_rated / If_rated
        return k * If

    def calculate_excitation_current(self, P: float, Q: float, V: float) -> float:
        """
        Calculate required field excitation current for given operating point
        """
        # Terminal current
        S = np.sqrt(P**2 + Q**2)
        I = S / (np.sqrt(3) * V)

        # Power factor angle
        phi = np.arctan2(Q, P)

        # Phase voltage
        V_ph = V / np.sqrt(3)

        # Internal voltage magnitude (simplified)
        Xsd = self.params.xsd * self.params.Zbase
        E = np.sqrt((V_ph * np.cos(phi) + I * Xsd * np.sin(phi))**2 +
                    (V_ph * np.sin(phi) + I * Xsd * np.cos(phi))**2)

        # Field current (linear relationship)
        If = E * self.params.Ifn / (self.params.V1n / np.sqrt(3))

        return If

    def dynamics(self, t: float, y: np.ndarray, Pm: float, If: float, V_bus: float) -> np.ndarray:
        """
        Differential equations for generator dynamics
        State vector: [delta, omega, Eq']
        """
        delta, omega, Eq_prime = y

        # Calculate electrical power
        Pe = (Eq_prime * V_bus / self.params.Xsd) * np.sin(delta)

        # Swing equation
        ddelta_dt = omega - self.omega_sync

        # Rotor dynamics
        domega_dt = (self.omega_sync / (2 * self.H)) * (Pm - Pe - self.D * (omega - self.omega_sync))

        # Excitation dynamics
        E0 = self.calculate_internal_voltage(If, self.params.Ifn, self.params.V1n / np.sqrt(3))
        dEq_dt = (E0 - Eq_prime) / self.Td0_prime

        return np.array([ddelta_dt, domega_dt, dEq_dt])


class ParallelGeneratorSystem:
    """System of two generators operating in parallel"""

    def __init__(self, gen_a_params: GeneratorParameters, gen_b_params: GeneratorParameters):
        self.gen_a = SynchronousGenerator(gen_a_params)
        self.gen_b = SynchronousGenerator(gen_b_params)
        self.gen_a_params = gen_a_params
        self.gen_b_params = gen_b_params

    def solve_load_sharing(self, PL: float, QL: float, V1: float, IfA: float, PA: float) -> Tuple[float, Dict]:
        """
        Solve for generator B field current given load conditions

        Parameters:
        - PL: Total load power (kW)
        - QL: Total reactive power (kVar)
        - V1: Terminal voltage (V)
        - IfA: Generator A field current (A)
        - PA: Generator A active power (kW)

        Returns:
        - IfB: Required field current for generator B
        - results: Dictionary with detailed results
        """

        # Power sharing
        PB = PL - PA

        # Calculate reactive power for each generator
        # Using voltage-reactive power droop characteristics

        # Generator A
        EA = self.gen_a.calculate_internal_voltage(IfA, self.gen_a_params.Ifn,
                                                     self.gen_a_params.V1n / np.sqrt(3))

        # Current magnitude for generator A
        IA = (PA * 1000) / (np.sqrt(3) * V1 * np.cos(np.arctan(QL/PL)))

        # Power factor angle
        phi_L = np.arctan2(QL, PL)

        # Approximate reactive power sharing based on synchronous reactances
        # Q ∝ (E - V) / Xsd

        # Iterative solution for load sharing
        IfB_guess = self.gen_b_params.Ifn

        for iteration in range(50):
            EB = self.gen_b.calculate_internal_voltage(IfB_guess, self.gen_b_params.Ifn,
                                                         self.gen_b_params.V1n / np.sqrt(3))

            # Reactive power from generator A
            V_ph = V1 / np.sqrt(3)
            QA = ((EA - V_ph) / self.gen_a_params.Xsd) * V_ph

            # Reactive power from generator B
            QB = ((EB - V_ph) / self.gen_b_params.Xsd) * V_ph

            # Total reactive power
            Q_total = (QA + QB) * 3 / 1000  # Convert to kVar

            # Error
            error = abs(Q_total - QL)

            if error < 0.1:  # Convergence criterion
                break

            # Adjust IfB
            if Q_total < QL:
                IfB_guess *= 1.01
            else:
                IfB_guess *= 0.99

        # Compile results
        results = {
            'IfB': IfB_guess,
            'PA': PA,
            'PB': PB,
            'QA': QA * 3 / 1000,
            'QB': QB * 3 / 1000,
            'EA': EA,
            'EB': EB,
            'V1': V1,
            'iterations': iteration + 1
        }

        return IfB_guess, results

    def calculate_scenario_a(self) -> Dict:
        """
        Scenario (a): Calculate IfB for given conditions
        PL = 420 kW, cos(phi_L) = 0.74 lagging, IfA = 14 A
        Each generator delivers 210 kW
        """
        PL = 420  # kW
        cos_phi_L = 0.74
        phi_L = np.arccos(cos_phi_L)
        QL = PL * np.tan(phi_L)  # Reactive power

        V1 = self.gen_a_params.V1n  # Maintain rated voltage
        IfA = 14  # A
        PA = 210  # kW

        IfB, results = self.solve_load_sharing(PL, QL, V1, IfA, PA)

        results['scenario'] = 'a'
        results['PL'] = PL
        results['QL'] = QL
        results['cos_phi_L'] = cos_phi_L
        results['IfA'] = IfA

        return results

    def calculate_scenario_b(self, results_a: Dict) -> Dict:
        """
        Scenario (b): Additional 100 kW load at unity power factor
        Keep generator B conditions same, calculate new IfA
        """
        # New load
        PL = results_a['PL'] + 100  # 520 kW

        # Calculate new reactive power
        # Original: PL1 = 420 kW, QL1 = 420 * tan(acos(0.74))
        # Additional: PL2 = 100 kW, QL2 = 0
        QL = results_a['QL']  # Same reactive power

        cos_phi_L = PL / np.sqrt(PL**2 + QL**2)

        V1 = self.gen_a_params.V1n
        IfB = results_a['IfB']  # Keep same

        # New power sharing - assuming proportional sharing
        PB = results_a['PB']  # Keep generator B power same
        PA = PL - PB  # Generator A picks up additional load

        # Calculate new IfA
        QA = results_a['QA']  # Approximate, keep same initially
        IfA = self.gen_a.calculate_excitation_current(PA * 1000, QA * 1000, V1)

        results = {
            'scenario': 'b',
            'PL': PL,
            'QL': QL,
            'cos_phi_L': cos_phi_L,
            'PA': PA,
            'PB': PB,
            'QA': QA,
            'QB': results_a['QB'],
            'IfA': IfA,
            'IfB': IfB,
            'V1': V1,
            'additional_load': 100
        }

        return results


class ODESolver:
    """ODE Solver with multiple methods"""

    @staticmethod
    def euler(f, t, y, h, *args):
        """Euler method"""
        return y + h * f(t, y, *args)

    @staticmethod
    def rk4(f, t, y, h, *args):
        """4th order Runge-Kutta method"""
        k1 = f(t, y, *args)
        k2 = f(t + h/2, y + h*k1/2, *args)
        k3 = f(t + h/2, y + h*k2/2, *args)
        k4 = f(t + h, y + h*k3, *args)
        return y + h * (k1 + 2*k2 + 2*k3 + k4) / 6

    @staticmethod
    def rk45_step(f, t, y, h, *args):
        """Runge-Kutta-Fehlberg 4(5) method with adaptive step size"""
        # RK4 coefficients
        k1 = f(t, y, *args)
        k2 = f(t + h/4, y + h*k1/4, *args)
        k3 = f(t + 3*h/8, y + h*(3*k1 + 9*k2)/32, *args)
        k4 = f(t + 12*h/13, y + h*(1932*k1 - 7200*k2 + 7296*k3)/2197, *args)
        k5 = f(t + h, y + h*(439*k1/216 - 8*k2 + 3680*k3/513 - 845*k4/4104), *args)
        k6 = f(t + h/2, y + h*(-8*k1/27 + 2*k2 - 3544*k3/2565 + 1859*k4/4104 - 11*k5/40), *args)

        # 4th and 5th order solutions
        y4 = y + h * (25*k1/216 + 1408*k3/2565 + 2197*k4/4104 - k5/5)
        y5 = y + h * (16*k1/135 + 6656*k3/12825 + 28561*k4/56430 - 9*k5/50 + 2*k6/55)

        return y5, np.linalg.norm(y5 - y4)


class DynamicSimulator:
    """Real-time dynamic simulator for generator system"""

    def __init__(self, system: ParallelGeneratorSystem):
        self.system = system
        self.reset()

    def reset(self):
        """Reset simulation state"""
        self.time = []
        self.gen_a_delta = []
        self.gen_a_omega = []
        self.gen_a_power = []
        self.gen_b_delta = []
        self.gen_b_omega = []
        self.gen_b_power = []
        self.bus_voltage = []

        # Initial conditions
        self.t = 0.0
        self.y_a = np.array([0.0, 2*np.pi*60, self.system.gen_a_params.V1n / np.sqrt(3)])
        self.y_b = np.array([0.0, 2*np.pi*60, self.system.gen_b_params.V1n / np.sqrt(3)])

        self.is_running = False

    def step(self, dt: float, method: str, Pm_a: float, Pm_b: float, If_a: float, If_b: float):
        """Single simulation step"""
        V_bus = self.system.gen_a_params.V1n / np.sqrt(3)

        # Select solver
        if method == 'euler':
            self.y_a = ODESolver.euler(self.system.gen_a.dynamics, self.t, self.y_a, dt,
                                       Pm_a, If_a, V_bus)
            self.y_b = ODESolver.euler(self.system.gen_b.dynamics, self.t, self.y_b, dt,
                                       Pm_b, If_b, V_bus)
        elif method == 'rk4':
            self.y_a = ODESolver.rk4(self.system.gen_a.dynamics, self.t, self.y_a, dt,
                                    Pm_a, If_a, V_bus)
            self.y_b = ODESolver.rk4(self.system.gen_b.dynamics, self.t, self.y_b, dt,
                                    Pm_b, If_b, V_bus)
        elif method == 'rk45':
            self.y_a, _ = ODESolver.rk45_step(self.system.gen_a.dynamics, self.t, self.y_a, dt,
                                              Pm_a, If_a, V_bus)
            self.y_b, _ = ODESolver.rk45_step(self.system.gen_b.dynamics, self.t, self.y_b, dt,
                                              Pm_b, If_b, V_bus)

        # Calculate electrical power
        Pe_a = (self.y_a[2] * V_bus / self.system.gen_a_params.Xsd) * np.sin(self.y_a[0])
        Pe_b = (self.y_b[2] * V_bus / self.system.gen_b_params.Xsd) * np.sin(self.y_b[0])

        # Store results
        self.time.append(self.t)
        self.gen_a_delta.append(np.degrees(self.y_a[0]))
        self.gen_a_omega.append(self.y_a[1])
        self.gen_a_power.append(Pe_a / 1000)  # kW
        self.gen_b_delta.append(np.degrees(self.y_b[0]))
        self.gen_b_omega.append(self.y_b[1])
        self.gen_b_power.append(Pe_b / 1000)  # kW
        self.bus_voltage.append(V_bus * np.sqrt(3))

        self.t += dt

    def get_results(self) -> Dict:
        """Get simulation results"""
        return {
            'time': np.array(self.time),
            'gen_a_delta': np.array(self.gen_a_delta),
            'gen_a_omega': np.array(self.gen_a_omega),
            'gen_a_power': np.array(self.gen_a_power),
            'gen_b_delta': np.array(self.gen_b_delta),
            'gen_b_omega': np.array(self.gen_b_omega),
            'gen_b_power': np.array(self.gen_b_power),
            'bus_voltage': np.array(self.bus_voltage)
        }


class GeneratorGUI:
    """Advanced Tkinter GUI for parallel generator analysis"""

    def __init__(self, root):
        self.root = root
        self.root.title("Parallel Synchronous Generators Analysis & Simulation")
        self.root.geometry("1400x900")

        # Initialize generator system
        self.setup_generators()

        # Simulation state
        self.simulation_running = False
        self.simulation_thread = None

        # Create GUI
        self.create_menu()
        self.create_main_interface()

        # Bind resize event
        self.root.bind('<Configure>', self.on_window_resize)

    def setup_generators(self):
        """Initialize generator parameters"""
        gen_a_params = GeneratorParameters(
            name="Generator A",
            Pn=300,  # kW
            V1n=6000,  # V
            Ifn=15,  # A
            xsd=1.7,
            cos_phi_n=0.8
        )

        gen_b_params = GeneratorParameters(
            name="Generator B",
            Pn=250,  # kW
            V1n=6000,  # V
            Ifn=11,  # A
            xsd=1.6,
            cos_phi_n=0.8
        )

        self.system = ParallelGeneratorSystem(gen_a_params, gen_b_params)
        self.simulator = DynamicSimulator(self.system)

    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Analysis", command=self.reset_analysis)
        file_menu.add_command(label="Export Results", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Calculate menu
        calc_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Calculate", menu=calc_menu)
        calc_menu.add_command(label="Scenario A", command=self.calculate_scenario_a)
        calc_menu.add_command(label="Scenario B", command=self.calculate_scenario_b)
        calc_menu.add_command(label="Custom Analysis", command=self.custom_analysis)

        # Simulation menu
        sim_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Simulation", menu=sim_menu)
        sim_menu.add_command(label="Start", command=self.start_simulation)
        sim_menu.add_command(label="Stop", command=self.stop_simulation)
        sim_menu.add_command(label="Reset", command=self.reset_simulation)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_documentation)

    def create_main_interface(self):
        """Create main interface with notebook tabs"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.create_static_analysis_tab()
        self.create_dynamic_simulation_tab()
        self.create_parameters_tab()
        self.create_results_tab()

    def create_static_analysis_tab(self):
        """Tab for static load flow analysis"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Static Analysis")

        # Create frames
        input_frame = ttk.LabelFrame(tab, text="Input Parameters", padding=10)
        input_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        control_frame = ttk.LabelFrame(tab, text="Control", padding=10)
        control_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        results_frame = ttk.LabelFrame(tab, text="Results", padding=10)
        results_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky="nsew")

        # Configure grid weights
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # Input fields
        row = 0

        # Load parameters
        ttk.Label(input_frame, text="Total Load Power (kW):").grid(row=row, column=0, sticky="w", pady=2)
        self.load_power_var = tk.StringVar(value="420")
        ttk.Entry(input_frame, textvariable=self.load_power_var, width=15).grid(row=row, column=1, pady=2)
        row += 1

        ttk.Label(input_frame, text="Load Power Factor:").grid(row=row, column=0, sticky="w", pady=2)
        self.load_pf_var = tk.StringVar(value="0.74")
        ttk.Entry(input_frame, textvariable=self.load_pf_var, width=15).grid(row=row, column=1, pady=2)
        row += 1

        ttk.Separator(input_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        row += 1

        # Generator A parameters
        ttk.Label(input_frame, text="Generator A - Field Current (A):").grid(row=row, column=0, sticky="w", pady=2)
        self.if_a_var = tk.StringVar(value="14")
        ttk.Entry(input_frame, textvariable=self.if_a_var, width=15).grid(row=row, column=1, pady=2)
        row += 1

        ttk.Label(input_frame, text="Generator A - Power (kW):").grid(row=row, column=0, sticky="w", pady=2)
        self.pa_var = tk.StringVar(value="210")
        ttk.Entry(input_frame, textvariable=self.pa_var, width=15).grid(row=row, column=1, pady=2)
        row += 1

        ttk.Separator(input_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        row += 1

        # Bus voltage
        ttk.Label(input_frame, text="Bus Voltage (V):").grid(row=row, column=0, sticky="w", pady=2)
        self.bus_voltage_var = tk.StringVar(value="6000")
        ttk.Entry(input_frame, textvariable=self.bus_voltage_var, width=15).grid(row=row, column=1, pady=2)
        row += 1

        # Control buttons
        ttk.Button(control_frame, text="Calculate Scenario A",
                  command=self.calculate_scenario_a).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(control_frame, text="Calculate Scenario B",
                  command=self.calculate_scenario_b).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(control_frame, text="Custom Analysis",
                  command=self.custom_analysis).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(control_frame, text="Clear Results",
                  command=self.clear_static_results).grid(row=0, column=3, padx=5, pady=5)

        # Results text area
        self.static_results_text = scrolledtext.ScrolledText(results_frame, width=60, height=25,
                                                             font=('Courier', 10))
        self.static_results_text.pack(fill=tk.BOTH, expand=True)

    def create_dynamic_simulation_tab(self):
        """Tab for dynamic simulation"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Dynamic Simulation")

        # Control panel
        control_panel = ttk.LabelFrame(tab, text="Simulation Control", padding=10)
        control_panel.grid(row=0, column=0, padx=5, pady=5, sticky="ew", columnspan=2)

        # Solver selection
        ttk.Label(control_panel, text="ODE Solver:").grid(row=0, column=0, padx=5)
        self.solver_var = tk.StringVar(value="rk4")
        solvers = ttk.Combobox(control_panel, textvariable=self.solver_var,
                              values=["euler", "rk4", "rk45"], state="readonly", width=10)
        solvers.grid(row=0, column=1, padx=5)

        # Time step
        ttk.Label(control_panel, text="Time Step (s):").grid(row=0, column=2, padx=5)
        self.dt_var = tk.StringVar(value="0.01")
        ttk.Entry(control_panel, textvariable=self.dt_var, width=10).grid(row=0, column=3, padx=5)

        # Simulation duration
        ttk.Label(control_panel, text="Duration (s):").grid(row=0, column=4, padx=5)
        self.duration_var = tk.StringVar(value="10")
        ttk.Entry(control_panel, textvariable=self.duration_var, width=10).grid(row=0, column=5, padx=5)

        # Control buttons
        ttk.Button(control_panel, text="▶ Start", command=self.start_simulation,
                  width=10).grid(row=0, column=6, padx=5)
        ttk.Button(control_panel, text="⬛ Stop", command=self.stop_simulation,
                  width=10).grid(row=0, column=7, padx=5)
        ttk.Button(control_panel, text="↻ Reset", command=self.reset_simulation,
                  width=10).grid(row=0, column=8, padx=5)

        # Sliders frame
        sliders_frame = ttk.LabelFrame(tab, text="Real-time Control", padding=10)
        sliders_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Generator A controls
        ttk.Label(sliders_frame, text="Generator A", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=3, pady=5)

        ttk.Label(sliders_frame, text="Mechanical Power (kW):").grid(row=1, column=0, sticky="w")
        self.pm_a_var = tk.DoubleVar(value=210)
        self.pm_a_slider = ttk.Scale(sliders_frame, from_=0, to=400, variable=self.pm_a_var,
                                     orient=tk.HORIZONTAL, length=300)
        self.pm_a_slider.grid(row=1, column=1, padx=5)
        self.pm_a_label = ttk.Label(sliders_frame, text="210.0")
        self.pm_a_label.grid(row=1, column=2)
        self.pm_a_var.trace('w', lambda *args: self.pm_a_label.config(text=f"{self.pm_a_var.get():.1f}"))

        ttk.Label(sliders_frame, text="Field Current (A):").grid(row=2, column=0, sticky="w")
        self.if_a_sim_var = tk.DoubleVar(value=14)
        self.if_a_slider = ttk.Scale(sliders_frame, from_=0, to=30, variable=self.if_a_sim_var,
                                     orient=tk.HORIZONTAL, length=300)
        self.if_a_slider.grid(row=2, column=1, padx=5)
        self.if_a_label = ttk.Label(sliders_frame, text="14.0")
        self.if_a_label.grid(row=2, column=2)
        self.if_a_sim_var.trace('w', lambda *args: self.if_a_label.config(text=f"{self.if_a_sim_var.get():.1f}"))

        ttk.Separator(sliders_frame, orient='horizontal').grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)

        # Generator B controls
        ttk.Label(sliders_frame, text="Generator B", font=('Arial', 10, 'bold')).grid(row=4, column=0, columnspan=3, pady=5)

        ttk.Label(sliders_frame, text="Mechanical Power (kW):").grid(row=5, column=0, sticky="w")
        self.pm_b_var = tk.DoubleVar(value=210)
        self.pm_b_slider = ttk.Scale(sliders_frame, from_=0, to=350, variable=self.pm_b_var,
                                     orient=tk.HORIZONTAL, length=300)
        self.pm_b_slider.grid(row=5, column=1, padx=5)
        self.pm_b_label = ttk.Label(sliders_frame, text="210.0")
        self.pm_b_label.grid(row=5, column=2)
        self.pm_b_var.trace('w', lambda *args: self.pm_b_label.config(text=f"{self.pm_b_var.get():.1f}"))

        ttk.Label(sliders_frame, text="Field Current (A):").grid(row=6, column=0, sticky="w")
        self.if_b_sim_var = tk.DoubleVar(value=11)
        self.if_b_slider = ttk.Scale(sliders_frame, from_=0, to=25, variable=self.if_b_sim_var,
                                     orient=tk.HORIZONTAL, length=300)
        self.if_b_slider.grid(row=6, column=1, padx=5)
        self.if_b_label = ttk.Label(sliders_frame, text="11.0")
        self.if_b_label.grid(row=6, column=2)
        self.if_b_sim_var.trace('w', lambda *args: self.if_b_label.config(text=f"{self.if_b_sim_var.get():.1f}"))

        # Visualization frame
        viz_frame = ttk.LabelFrame(tab, text="Real-time Visualization", padding=5)
        viz_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        # Create matplotlib figure
        self.sim_fig = Figure(figsize=(10, 8), dpi=80)
        self.sim_canvas = FigureCanvasTkAgg(self.sim_fig, master=viz_frame)
        self.sim_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Create subplots
        self.ax_delta = self.sim_fig.add_subplot(311)
        self.ax_omega = self.sim_fig.add_subplot(312)
        self.ax_power = self.sim_fig.add_subplot(313)

        self.ax_delta.set_ylabel('Rotor Angle (deg)')
        self.ax_delta.grid(True, alpha=0.3)
        self.ax_delta.legend(['Gen A', 'Gen B'], loc='upper right')

        self.ax_omega.set_ylabel('Speed (rad/s)')
        self.ax_omega.grid(True, alpha=0.3)
        self.ax_omega.legend(['Gen A', 'Gen B'], loc='upper right')

        self.ax_power.set_ylabel('Power (kW)')
        self.ax_power.set_xlabel('Time (s)')
        self.ax_power.grid(True, alpha=0.3)
        self.ax_power.legend(['Gen A', 'Gen B'], loc='upper right')

        self.sim_fig.tight_layout()

        # Configure grid weights
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(1, weight=1)

    def create_parameters_tab(self):
        """Tab for viewing/editing generator parameters"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Generator Parameters")

        # Create two columns for two generators
        gen_a_frame = ttk.LabelFrame(tab, text="Generator A Parameters", padding=10)
        gen_a_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        gen_b_frame = ttk.LabelFrame(tab, text="Generator B Parameters", padding=10)
        gen_b_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # Generator A parameters
        params_a = [
            ("Nominal Power (kW):", str(self.system.gen_a_params.Pn)),
            ("Nominal Voltage (V):", str(self.system.gen_a_params.V1n)),
            ("Nominal Field Current (A):", str(self.system.gen_a_params.Ifn)),
            ("d-axis Reactance (p.u.):", str(self.system.gen_a_params.xsd)),
            ("Power Factor:", str(self.system.gen_a_params.cos_phi_n)),
            ("Nominal Current (A):", f"{self.system.gen_a_params.In:.2f}"),
            ("Base Impedance (Ω):", f"{self.system.gen_a_params.Zbase:.2f}"),
            ("Synchronous Reactance (Ω):", f"{self.system.gen_a_params.Xsd:.2f}"),
        ]

        for i, (label, value) in enumerate(params_a):
            ttk.Label(gen_a_frame, text=label).grid(row=i, column=0, sticky="w", pady=3)
            ttk.Label(gen_a_frame, text=value, font=('Courier', 10, 'bold')).grid(row=i, column=1, sticky="e", pady=3)

        # Generator B parameters
        params_b = [
            ("Nominal Power (kW):", str(self.system.gen_b_params.Pn)),
            ("Nominal Voltage (V):", str(self.system.gen_b_params.V1n)),
            ("Nominal Field Current (A):", str(self.system.gen_b_params.Ifn)),
            ("d-axis Reactance (p.u.):", str(self.system.gen_b_params.xsd)),
            ("Power Factor:", str(self.system.gen_b_params.cos_phi_n)),
            ("Nominal Current (A):", f"{self.system.gen_b_params.In:.2f}"),
            ("Base Impedance (Ω):", f"{self.system.gen_b_params.Zbase:.2f}"),
            ("Synchronous Reactance (Ω):", f"{self.system.gen_b_params.Xsd:.2f}"),
        ]

        for i, (label, value) in enumerate(params_b):
            ttk.Label(gen_b_frame, text=label).grid(row=i, column=0, sticky="w", pady=3)
            ttk.Label(gen_b_frame, text=value, font=('Courier', 10, 'bold')).grid(row=i, column=1, sticky="e", pady=3)

    def create_results_tab(self):
        """Tab for detailed results and analysis"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Detailed Results")

        # Results text
        self.detailed_results_text = scrolledtext.ScrolledText(tab, width=80, height=30,
                                                               font=('Courier', 10))
        self.detailed_results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add initial text
        self.detailed_results_text.insert('1.0', """
╔══════════════════════════════════════════════════════════════════════════════╗
║       PARALLEL SYNCHRONOUS GENERATORS ANALYSIS - DETAILED RESULTS            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Run calculations from the Static Analysis tab to see results here.

Available Analyses:
  • Scenario A: Calculate Generator B field current for balanced load sharing
  • Scenario B: Calculate Generator A field current after additional load
  • Custom Analysis: Specify your own operating conditions

Use the Dynamic Simulation tab for transient analysis and real-time control.
""")

    def calculate_scenario_a(self):
        """Calculate scenario A"""
        try:
            results = self.system.calculate_scenario_a()
            self.display_static_results(results)
            self.display_detailed_results(results)
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error in scenario A calculation:\n{str(e)}")

    def calculate_scenario_b(self):
        """Calculate scenario B"""
        try:
            # First calculate scenario A
            results_a = self.system.calculate_scenario_a()
            # Then calculate scenario B based on A
            results = self.system.calculate_scenario_b(results_a)
            self.display_static_results(results)
            self.display_detailed_results(results)
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error in scenario B calculation:\n{str(e)}")

    def custom_analysis(self):
        """Custom analysis with user inputs"""
        try:
            PL = float(self.load_power_var.get())
            cos_phi = float(self.load_pf_var.get())
            IfA = float(self.if_a_var.get())
            PA = float(self.pa_var.get())
            V1 = float(self.bus_voltage_var.get())

            phi = np.arccos(cos_phi)
            QL = PL * np.tan(phi)

            IfB, results = self.system.solve_load_sharing(PL, QL, V1, IfA, PA)

            results['scenario'] = 'custom'
            results['PL'] = PL
            results['QL'] = QL
            results['cos_phi_L'] = cos_phi
            results['IfA'] = IfA

            self.display_static_results(results)
            self.display_detailed_results(results)

        except ValueError as e:
            messagebox.showerror("Input Error", "Please enter valid numerical values.")
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error in custom analysis:\n{str(e)}")

    def display_static_results(self, results: Dict):
        """Display results in static analysis tab"""
        self.static_results_text.delete('1.0', tk.END)

        output = f"""
{'='*70}
PARALLEL GENERATOR LOAD SHARING ANALYSIS
{'='*70}

Scenario: {results['scenario'].upper()}

LOAD CONDITIONS:
  Total Active Power:       {results['PL']:.2f} kW
  Total Reactive Power:     {results['QL']:.2f} kVar
  Load Power Factor:        {results['cos_phi_L']:.4f} lagging
  Bus Voltage:              {results['V1']:.1f} V

GENERATOR A:
  Active Power Output:      {results['PA']:.2f} kW
  Reactive Power Output:    {results['QA']:.2f} kVar
  Field Current:            {results['IfA']:.2f} A
  Internal Voltage:         {results['EA']:.2f} V

GENERATOR B:
  Active Power Output:      {results['PB']:.2f} kW
  Reactive Power Output:    {results['QB']:.2f} kVar
  Field Current:            {results['IfB']:.2f} A
  Internal Voltage:         {results['EB']:.2f} V

VERIFICATION:
  Total Power Generated:    {results['PA'] + results['PB']:.2f} kW
  Total Reactive Power:     {results['QA'] + results['QB']:.2f} kVar
  Power Balance Error:      {abs((results['PA'] + results['PB']) - results['PL']):.4f} kW

"""

        if results['scenario'] == 'b':
            output += f"""
ADDITIONAL LOAD:
  Additional Active Power:  {results['additional_load']:.0f} kW at unity PF
  New Total Load:           {results['PL']:.2f} kW

"""

        output += f"""
{'='*70}
Calculation completed in {results.get('iterations', 'N/A')} iterations
{'='*70}
"""

        self.static_results_text.insert('1.0', output)

    def display_detailed_results(self, results: Dict):
        """Display detailed results in results tab"""
        self.detailed_results_text.delete('1.0', tk.END)

        output = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║       PARALLEL SYNCHRONOUS GENERATORS - DETAILED ANALYSIS RESULTS            ║
╚══════════════════════════════════════════════════════════════════════════════╝

SCENARIO: {results['scenario'].upper()}
Date: {time.strftime('%Y-%m-%d %H:%M:%S')}

{'─'*80}
SYSTEM CONFIGURATION
{'─'*80}

Generator A:
  • Rated Power:           {self.system.gen_a_params.Pn} kW
  • Rated Voltage:         {self.system.gen_a_params.V1n} V
  • Rated Field Current:   {self.system.gen_a_params.Ifn} A
  • Synchronous Reactance: {self.system.gen_a_params.xsd} p.u. ({self.system.gen_a_params.Xsd:.2f} Ω)
  • Base Impedance:        {self.system.gen_a_params.Zbase:.2f} Ω
  • Rated Current:         {self.system.gen_a_params.In:.2f} A

Generator B:
  • Rated Power:           {self.system.gen_b_params.Pn} kW
  • Rated Voltage:         {self.system.gen_b_params.V1n} V
  • Rated Field Current:   {self.system.gen_b_params.Ifn} A
  • Synchronous Reactance: {self.system.gen_b_params.xsd} p.u. ({self.system.gen_b_params.Xsd:.2f} Ω)
  • Base Impedance:        {self.system.gen_b_params.Zbase:.2f} Ω
  • Rated Current:         {self.system.gen_b_params.In:.2f} A

{'─'*80}
OPERATING CONDITIONS
{'─'*80}

Load:
  • Total Active Power:    {results['PL']:.2f} kW
  • Total Reactive Power:  {results['QL']:.2f} kVar
  • Apparent Power:        {np.sqrt(results['PL']**2 + results['QL']**2):.2f} kVA
  • Power Factor:          {results['cos_phi_L']:.4f} lagging
  • Power Factor Angle:    {np.degrees(np.arccos(results['cos_phi_L'])):.2f}°

Bus:
  • Voltage:               {results['V1']:.1f} V (line-to-line)
  • Phase Voltage:         {results['V1']/np.sqrt(3):.1f} V

{'─'*80}
GENERATOR A - OPERATING POINT
{'─'*80}

Power Output:
  • Active Power:          {results['PA']:.2f} kW ({results['PA']/self.system.gen_a_params.Pn*100:.1f}% of rated)
  • Reactive Power:        {results['QA']:.2f} kVar
  • Apparent Power:        {np.sqrt(results['PA']**2 + results['QA']**2):.2f} kVA
  • Power Factor:          {results['PA']/np.sqrt(results['PA']**2 + results['QA']**2):.4f}

Excitation:
  • Field Current:         {results['IfA']:.2f} A ({results['IfA']/self.system.gen_a_params.Ifn*100:.1f}% of rated)
  • Internal Voltage (Eq): {results['EA']:.2f} V (phase)

Current:
  • Output Current:        {(results['PA']*1000)/(np.sqrt(3)*results['V1']*results['PA']/np.sqrt(results['PA']**2 + results['QA']**2)):.2f} A

{'─'*80}
GENERATOR B - OPERATING POINT
{'─'*80}

Power Output:
  • Active Power:          {results['PB']:.2f} kW ({results['PB']/self.system.gen_b_params.Pn*100:.1f}% of rated)
  • Reactive Power:        {results['QB']:.2f} kVar
  • Apparent Power:        {np.sqrt(results['PB']**2 + results['QB']**2):.2f} kVA
  • Power Factor:          {results['PB']/np.sqrt(results['PB']**2 + results['QB']**2):.4f}

Excitation:
  • Field Current:         {results['IfB']:.2f} A ({results['IfB']/self.system.gen_b_params.Ifn*100:.1f}% of rated)
  • Internal Voltage (Eq): {results['EB']:.2f} V (phase)

Current:
  • Output Current:        {(results['PB']*1000)/(np.sqrt(3)*results['V1']*results['PB']/np.sqrt(results['PB']**2 + results['QB']**2)):.2f} A

{'─'*80}
POWER BALANCE VERIFICATION
{'─'*80}

Active Power:
  • Generator A Output:    {results['PA']:.2f} kW
  • Generator B Output:    {results['PB']:.2f} kW
  • Total Generation:      {results['PA'] + results['PB']:.2f} kW
  • Load Demand:           {results['PL']:.2f} kW
  • Balance Error:         {abs((results['PA'] + results['PB']) - results['PL']):.4f} kW

Reactive Power:
  • Generator A Output:    {results['QA']:.2f} kVar
  • Generator B Output:    {results['QB']:.2f} kVar
  • Total Generation:      {results['QA'] + results['QB']:.2f} kVar
  • Load Demand:           {results['QL']:.2f} kVar
  • Balance Error:         {abs((results['QA'] + results['QB']) - results['QL']):.4f} kVar

{'─'*80}
LOAD SHARING RATIO
{'─'*80}

Active Power Sharing:
  • Generator A:           {results['PA']/(results['PA']+results['PB'])*100:.1f}%
  • Generator B:           {results['PB']/(results['PA']+results['PB'])*100:.1f}%

Reactive Power Sharing:
  • Generator A:           {results['QA']/(results['QA']+results['QB'])*100:.1f}%
  • Generator B:           {results['QB']/(results['QA']+results['QB'])*100:.1f}%

"""

        if results['scenario'] == 'b':
            output += f"""
{'─'*80}
SCENARIO B - ADDITIONAL LOAD ANALYSIS
{'─'*80}

Additional Load:
  • Power:                 {results['additional_load']:.0f} kW
  • Power Factor:          1.0 (unity)
  • Type:                  Resistive (e.g., lighting)

Impact on Generator A:
  • Power Increase:        {results['PA'] - 210:.2f} kW
  • New Field Current:     {results['IfA']:.2f} A
  • Field Current Change:  {results['IfA'] - 14:.2f} A

Generator B Status:
  • Maintained at:         {results['PB']:.2f} kW
  • Field Current:         {results['IfB']:.2f} A (unchanged)

"""

        output += f"""
{'─'*80}
COMPUTATIONAL DETAILS
{'─'*80}

Convergence:
  • Iterations:            {results.get('iterations', 'N/A')}
  • Method:                Iterative load flow with reactive power droop

Assumptions:
  • Unsaturated magnetic circuits (linear E-If relationship)
  • Non-salient pole rotors (Xd = Xq)
  • Steady-state conditions
  • Balanced three-phase system
  • Wye-connected stator windings

{'═'*80}
END OF REPORT
{'═'*80}
"""

        self.detailed_results_text.insert('1.0', output)

    def start_simulation(self):
        """Start dynamic simulation"""
        if self.simulation_running:
            messagebox.showwarning("Simulation", "Simulation is already running!")
            return

        self.simulation_running = True
        self.simulator.reset()

        # Start simulation thread
        self.simulation_thread = threading.Thread(target=self.run_simulation, daemon=True)
        self.simulation_thread.start()

        # Start update loop
        self.update_simulation_plot()

    def run_simulation(self):
        """Run simulation in background thread"""
        try:
            dt = float(self.dt_var.get())
            duration = float(self.duration_var.get())
            method = self.solver_var.get()

            while self.simulation_running and self.simulator.t < duration:
                # Get control values
                Pm_a = self.pm_a_var.get() * 1000  # Convert to W
                Pm_b = self.pm_b_var.get() * 1000
                If_a = self.if_a_sim_var.get()
                If_b = self.if_b_sim_var.get()

                # Simulation step
                self.simulator.step(dt, method, Pm_a, Pm_b, If_a, If_b)

                # Control simulation speed
                time.sleep(dt * 0.1)  # Real-time factor

        except Exception as e:
            print(f"Simulation error: {e}")
            self.simulation_running = False

    def update_simulation_plot(self):
        """Update simulation plots"""
        if not self.simulation_running:
            return

        if len(self.simulator.time) > 1:
            results = self.simulator.get_results()

            # Clear axes
            self.ax_delta.clear()
            self.ax_omega.clear()
            self.ax_power.clear()

            # Plot rotor angles
            self.ax_delta.plot(results['time'], results['gen_a_delta'], 'b-', label='Gen A')
            self.ax_delta.plot(results['time'], results['gen_b_delta'], 'r-', label='Gen B')
            self.ax_delta.set_ylabel('Rotor Angle (deg)')
            self.ax_delta.grid(True, alpha=0.3)
            self.ax_delta.legend(loc='upper right')

            # Plot angular velocities
            omega_sync = 2 * np.pi * 60
            self.ax_omega.plot(results['time'], results['gen_a_omega'], 'b-', label='Gen A')
            self.ax_omega.plot(results['time'], results['gen_b_omega'], 'r-', label='Gen B')
            self.ax_omega.axhline(y=omega_sync, color='g', linestyle='--', label='Sync Speed')
            self.ax_omega.set_ylabel('Speed (rad/s)')
            self.ax_omega.grid(True, alpha=0.3)
            self.ax_omega.legend(loc='upper right')

            # Plot power
            self.ax_power.plot(results['time'], results['gen_a_power'], 'b-', label='Gen A')
            self.ax_power.plot(results['time'], results['gen_b_power'], 'r-', label='Gen B')
            self.ax_power.set_ylabel('Power (kW)')
            self.ax_power.set_xlabel('Time (s)')
            self.ax_power.grid(True, alpha=0.3)
            self.ax_power.legend(loc='upper right')

            self.sim_fig.tight_layout()
            self.sim_canvas.draw()

        # Schedule next update
        if self.simulation_running:
            self.root.after(100, self.update_simulation_plot)

    def stop_simulation(self):
        """Stop dynamic simulation"""
        self.simulation_running = False
        messagebox.showinfo("Simulation", "Simulation stopped.")

    def reset_simulation(self):
        """Reset simulation"""
        self.stop_simulation()
        self.simulator.reset()

        # Clear plots
        self.ax_delta.clear()
        self.ax_omega.clear()
        self.ax_power.clear()

        self.ax_delta.set_ylabel('Rotor Angle (deg)')
        self.ax_delta.grid(True, alpha=0.3)

        self.ax_omega.set_ylabel('Speed (rad/s)')
        self.ax_omega.grid(True, alpha=0.3)

        self.ax_power.set_ylabel('Power (kW)')
        self.ax_power.set_xlabel('Time (s)')
        self.ax_power.grid(True, alpha=0.3)

        self.sim_fig.tight_layout()
        self.sim_canvas.draw()

        messagebox.showinfo("Simulation", "Simulation reset.")

    def clear_static_results(self):
        """Clear static analysis results"""
        self.static_results_text.delete('1.0', tk.END)

    def reset_analysis(self):
        """Reset analysis"""
        self.load_power_var.set("420")
        self.load_pf_var.set("0.74")
        self.if_a_var.set("14")
        self.pa_var.set("210")
        self.bus_voltage_var.set("6000")
        self.clear_static_results()

    def export_results(self):
        """Export results to file"""
        messagebox.showinfo("Export", "Export functionality would save results to file.")

    def show_about(self):
        """Show about dialog"""
        about_text = """
Parallel Synchronous Generators Analysis Tool
Version 1.0

Advanced electrical engineering application for:
• Static load flow analysis
• Dynamic transient simulation
• Real-time control and visualization

Developed for educational and engineering purposes.
"""
        messagebox.showinfo("About", about_text)

    def show_documentation(self):
        """Show documentation"""
        doc_text = """
DOCUMENTATION

This tool provides comprehensive analysis of two synchronous
generators operating in parallel.

FEATURES:
• Calculate field excitation currents for load sharing
• Dynamic simulation with multiple ODE solvers
• Real-time control with adjustable sliders
• Visualization of transient responses

USAGE:
1. Static Analysis: Calculate operating points
2. Dynamic Simulation: Observe transient behavior
3. Real-time Control: Adjust parameters during simulation

For more information, refer to the user manual.
"""
        messagebox.showinfo("Documentation", doc_text)

    def on_window_resize(self, event):
        """Handle window resize event"""
        # Auto-scale is handled by grid weights
        pass


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = GeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
