"""
Advanced Electrical Engineering Simulator with Tkinter GUI
Includes:
1. Transformer Regulation Calculator
2. Dynamic Machine Simulation with ODE Solvers (RK45, Euler)
3. Real-time visualization and controls
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import time
from scipy.integrate import solve_ivp


class ElectricalEngineeringSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Electrical Engineering Simulator")
        self.root.geometry("1200x800")

        # Simulation control flags
        self.simulation_running = False
        self.simulation_thread = None
        self.stop_simulation = False

        # Configure grid weight for responsive design
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Create main notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Create tabs
        self.create_transformer_tab()
        self.create_dynamic_simulation_tab()

        # Bind resize event
        self.root.bind('<Configure>', self.on_window_resize)

    def on_window_resize(self, event):
        """Handle window resize for auto-scaling"""
        if event.widget == self.root:
            # Trigger canvas redraw for all figures
            try:
                if hasattr(self, 'transformer_canvas'):
                    self.transformer_canvas.draw()
                if hasattr(self, 'sim_canvas'):
                    self.sim_canvas.draw()
            except:
                pass

    def create_transformer_tab(self):
        """Create transformer regulation calculator tab"""
        tab1 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text="Transformer Regulation")

        # Configure grid
        tab1.grid_rowconfigure(1, weight=1)
        tab1.grid_columnconfigure(0, weight=1)
        tab1.grid_columnconfigure(1, weight=2)

        # Left panel - Input parameters
        left_frame = ttk.LabelFrame(tab1, text="Input Parameters", padding=10)
        left_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)

        # Transformer parameters
        params = [
            ("Rating (kVA):", "rating", 30),
            ("Primary Voltage (V):", "v1", 6000),
            ("Secondary Voltage (V):", "v2", 230),
            ("Primary Resistance (Ω):", "r1", 10),
            ("Secondary Resistance (Ω):", "r2", 0.016),
            ("Primary Reactance (Ω):", "x1", 23),
            ("Power Factor:", "pf", 0.8)
        ]

        self.transformer_vars = {}
        row = 0

        for label_text, var_name, default_val in params:
            ttk.Label(left_frame, text=label_text).grid(row=row, column=0, sticky="w", pady=5)
            var = tk.DoubleVar(value=default_val)
            entry = ttk.Entry(left_frame, textvariable=var, width=15)
            entry.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
            self.transformer_vars[var_name] = var
            row += 1

        # Power factor type
        ttk.Label(left_frame, text="Power Factor Type:").grid(row=row, column=0, sticky="w", pady=5)
        self.pf_type = tk.StringVar(value="lagging")
        pf_combo = ttk.Combobox(left_frame, textvariable=self.pf_type,
                                values=["lagging", "leading", "unity"],
                                state="readonly", width=13)
        pf_combo.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
        row += 1

        # Calculate button
        calc_btn = ttk.Button(left_frame, text="Calculate Regulation",
                             command=self.calculate_transformer_regulation)
        calc_btn.grid(row=row, column=0, columnspan=2, pady=20)
        row += 1

        # Results display
        results_frame = ttk.LabelFrame(left_frame, text="Results", padding=10)
        results_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)

        self.transformer_results = tk.Text(results_frame, height=15, width=40,
                                          font=("Courier", 9))
        self.transformer_results.grid(row=0, column=0, sticky="ew")

        scrollbar = ttk.Scrollbar(results_frame, command=self.transformer_results.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.transformer_results.config(yscrollcommand=scrollbar.set)

        # Right panel - Visualization
        right_frame = ttk.LabelFrame(tab1, text="Visualization", padding=10)
        right_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # Create matplotlib figure
        self.transformer_fig = Figure(figsize=(8, 6), dpi=100)
        self.transformer_canvas = FigureCanvasTkAgg(self.transformer_fig, right_frame)
        self.transformer_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Initialize with empty plot
        self.update_transformer_plot()

    def calculate_transformer_regulation(self):
        """Calculate transformer regulation and display results"""
        try:
            # Get parameters
            rating = self.transformer_vars['rating'].get() * 1000  # Convert to VA
            v1 = self.transformer_vars['v1'].get()
            v2 = self.transformer_vars['v2'].get()
            r1 = self.transformer_vars['r1'].get()
            r2 = self.transformer_vars['r2'].get()
            x1 = self.transformer_vars['x1'].get()
            pf = self.transformer_vars['pf'].get()

            # Validate inputs
            if v1 <= 0 or v2 <= 0:
                messagebox.showerror("Error", "Voltages must be positive")
                return

            if pf < 0 or pf > 1:
                messagebox.showerror("Error", "Power factor must be between 0 and 1")
                return

            # Calculate turn ratio
            turn_ratio = v1 / v2

            # Convert secondary resistance to primary
            r2_primary = r2 * (turn_ratio ** 2)

            # Total resistance and reactance referred to primary
            r_total = r1 + r2_primary
            x_total = x1

            # Calculate full load current on primary
            i1_fl = rating / v1

            # Calculate angle
            phi = np.arccos(pf)
            sin_phi = np.sin(phi)

            # Adjust for leading power factor
            if self.pf_type.get() == "leading":
                sin_phi = -sin_phi
            elif self.pf_type.get() == "unity":
                sin_phi = 0
                pf = 1.0

            # Calculate voltage regulation
            regulation = (i1_fl * (r_total * pf + x_total * sin_phi) / v1) * 100

            # Calculate equivalent impedance
            z_eq = np.sqrt(r_total**2 + x_total**2)

            # Calculate losses
            copper_loss = i1_fl**2 * r_total

            # Calculate efficiency (assuming core loss = 1% of rating)
            core_loss = 0.01 * rating
            total_loss = copper_loss + core_loss
            output_power = rating * pf
            input_power = output_power + total_loss
            efficiency = (output_power / input_power) * 100

            # Display results
            results_text = f"""
╔════════════════════════════════════════╗
║   TRANSFORMER REGULATION ANALYSIS      ║
╚════════════════════════════════════════╝

INPUT PARAMETERS:
  Rating:              {rating/1000:.1f} kVA
  Primary Voltage:     {v1:.0f} V
  Secondary Voltage:   {v2:.0f} V
  Primary Resistance:  {r1:.3f} Ω
  Secondary Resistance:{r2:.4f} Ω
  Primary Reactance:   {x1:.3f} Ω
  Power Factor:        {pf:.2f} {self.pf_type.get()}

CALCULATED VALUES:
  Turn Ratio (a):      {turn_ratio:.3f}
  R₂' (referred):      {r2_primary:.3f} Ω
  Total Resistance:    {r_total:.3f} Ω
  Total Reactance:     {x_total:.3f} Ω
  Equiv. Impedance:    {z_eq:.3f} Ω

CURRENT:
  Primary FL Current:  {i1_fl:.3f} A
  Secondary FL Current:{i1_fl * turn_ratio:.3f} A

LOSSES:
  Copper Loss:         {copper_loss:.2f} W
  Core Loss (est.):    {core_loss:.2f} W
  Total Loss:          {total_loss:.2f} W

PERFORMANCE:
  ╔════════════════════════════════════╗
  ║ VOLTAGE REGULATION: {regulation:6.3f} %    ║
  ║ EFFICIENCY:         {efficiency:6.3f} %    ║
  ╚════════════════════════════════════╝

NOTES:
  • {'Good' if regulation < 3 else 'Moderate' if regulation < 5 else 'High'} regulation for this transformer
  • {'Excellent' if efficiency > 95 else 'Good' if efficiency > 90 else 'Moderate'} efficiency at full load
"""

            self.transformer_results.delete(1.0, tk.END)
            self.transformer_results.insert(1.0, results_text)

            # Update visualization
            self.update_transformer_plot(regulation, pf, r_total, x_total, v1, i1_fl)

        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error: {str(e)}")

    def update_transformer_plot(self, regulation=None, pf=None, r_total=None,
                                x_total=None, v1=None, i1=None):
        """Update transformer visualization plots"""
        self.transformer_fig.clear()

        if regulation is not None:
            # Create subplots
            gs = self.transformer_fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

            # Plot 1: Voltage Regulation vs Power Factor
            ax1 = self.transformer_fig.add_subplot(gs[0, 0])
            pf_range = np.linspace(0.5, 1.0, 50)
            phi_range = np.arccos(pf_range)

            # Lagging
            reg_lagging = (i1 * (r_total * pf_range + x_total * np.sin(phi_range)) / v1) * 100
            ax1.plot(pf_range, reg_lagging, 'b-', linewidth=2, label='Lagging')

            # Leading
            reg_leading = (i1 * (r_total * pf_range - x_total * np.sin(phi_range)) / v1) * 100
            ax1.plot(pf_range, reg_leading, 'r--', linewidth=2, label='Leading')

            # Current point
            if pf is not None:
                ax1.plot(pf, regulation, 'go', markersize=10, label='Operating Point')

            ax1.set_xlabel('Power Factor', fontsize=9)
            ax1.set_ylabel('Regulation (%)', fontsize=9)
            ax1.set_title('Regulation vs Power Factor', fontsize=10, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.legend(fontsize=8)

            # Plot 2: Phasor Diagram
            ax2 = self.transformer_fig.add_subplot(gs[0, 1])
            phi = np.arccos(pf)

            # Current phasor (reference)
            i_vec = np.array([i1, 0])

            # Voltage drops
            vr = i1 * r_total
            vx = i1 * x_total

            # No-load voltage
            v_nl = v1 + vr * pf + vx * np.sin(phi)

            # Draw phasors
            ax2.arrow(0, 0, v1*np.cos(0), v1*np.sin(0), head_width=v1*0.05,
                     head_length=v1*0.03, fc='blue', ec='blue', linewidth=2, label='V₁')
            ax2.arrow(0, 0, i1*100*pf, i1*100*np.sin(phi), head_width=i1*5,
                     head_length=i1*3, fc='green', ec='green', linewidth=2, label='I₁')
            ax2.arrow(v1, 0, vr*pf, vr*np.sin(phi), head_width=vr*0.1,
                     head_length=vr*0.05, fc='red', ec='red', linewidth=1.5, label='I·R')
            ax2.arrow(v1+vr*pf, vr*np.sin(phi), -vx*np.sin(phi), vx*pf,
                     head_width=vx*0.1, head_length=vx*0.05, fc='orange',
                     ec='orange', linewidth=1.5, label='I·X')

            ax2.set_xlabel('Real', fontsize=9)
            ax2.set_ylabel('Imaginary', fontsize=9)
            ax2.set_title('Phasor Diagram', fontsize=10, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.legend(fontsize=8)
            ax2.axis('equal')

            # Plot 3: Regulation vs Load
            ax3 = self.transformer_fig.add_subplot(gs[1, 0])
            load_range = np.linspace(0, 1.5, 50)
            reg_vs_load = load_range * regulation

            ax3.plot(load_range * 100, reg_vs_load, 'b-', linewidth=2)
            ax3.axvline(100, color='r', linestyle='--', label='Full Load')
            ax3.axhline(regulation, color='g', linestyle='--', alpha=0.5)
            ax3.fill_between(load_range * 100, 0, reg_vs_load, alpha=0.3)

            ax3.set_xlabel('Load (%)', fontsize=9)
            ax3.set_ylabel('Regulation (%)', fontsize=9)
            ax3.set_title('Regulation vs Load', fontsize=10, fontweight='bold')
            ax3.grid(True, alpha=0.3)
            ax3.legend(fontsize=8)

            # Plot 4: Impedance Triangle
            ax4 = self.transformer_fig.add_subplot(gs[1, 1])
            z_eq = np.sqrt(r_total**2 + x_total**2)

            # Draw impedance triangle
            triangle = plt.Polygon([(0, 0), (r_total, 0), (r_total, x_total)],
                                  fill=True, alpha=0.3, color='cyan', edgecolor='black', linewidth=2)
            ax4.add_patch(triangle)

            # Labels
            ax4.text(r_total/2, -x_total*0.1, f'R = {r_total:.2f} Ω',
                    ha='center', fontsize=9, fontweight='bold')
            ax4.text(r_total+x_total*0.15, x_total/2, f'X = {x_total:.2f} Ω',
                    ha='left', fontsize=9, fontweight='bold')
            ax4.text(r_total/2-2, x_total/2+1, f'Z = {z_eq:.2f} Ω',
                    ha='center', fontsize=9, fontweight='bold', color='red')

            # Angle
            angle = np.arctan(x_total/r_total) * 180/np.pi
            ax4.text(r_total*0.3, x_total*0.1, f'θ = {angle:.1f}°',
                    fontsize=8)

            ax4.set_xlabel('Resistance (Ω)', fontsize=9)
            ax4.set_ylabel('Reactance (Ω)', fontsize=9)
            ax4.set_title('Equivalent Impedance Triangle', fontsize=10, fontweight='bold')
            ax4.grid(True, alpha=0.3)
            ax4.set_xlim(-2, r_total*1.3)
            ax4.set_ylim(-x_total*0.3, x_total*1.3)
            ax4.set_aspect('equal')
        else:
            # Initial empty plot
            ax = self.transformer_fig.add_subplot(111)
            ax.text(0.5, 0.5, 'Enter parameters and click\n"Calculate Regulation"',
                   ha='center', va='center', fontsize=14, transform=ax.transAxes)
            ax.axis('off')

        self.transformer_canvas.draw()

    def create_dynamic_simulation_tab(self):
        """Create dynamic machine simulation tab with ODE solvers"""
        tab2 = ttk.Frame(self.notebook)
        self.notebook.add(tab2, text="Dynamic Machine Simulation")

        # Configure grid
        tab2.grid_rowconfigure(1, weight=1)
        tab2.grid_columnconfigure(0, weight=1)
        tab2.grid_columnconfigure(1, weight=2)

        # Left panel - Controls
        control_frame = ttk.LabelFrame(tab2, text="Simulation Controls", padding=10)
        control_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)

        # Machine type selection
        ttk.Label(control_frame, text="Machine Type:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=5)

        self.machine_type = tk.StringVar(value="DC Motor")
        machines = ["DC Motor", "Synchronous Generator", "Induction Motor", "RL Circuit"]
        for i, machine in enumerate(machines):
            ttk.Radiobutton(control_frame, text=machine, variable=self.machine_type,
                          value=machine, command=self.update_machine_parameters).grid(
                row=i+1, column=0, columnspan=2, sticky="w", padx=20)

        # Separator
        ttk.Separator(control_frame, orient='horizontal').grid(
            row=len(machines)+1, column=0, columnspan=2, sticky="ew", pady=10)

        # Machine parameters frame
        self.params_frame = ttk.LabelFrame(control_frame, text="Machine Parameters", padding=10)
        self.params_frame.grid(row=len(machines)+2, column=0, columnspan=2, sticky="ew", pady=5)

        # ODE Solver selection
        ttk.Label(control_frame, text="ODE Solver:", font=('Arial', 10, 'bold')).grid(
            row=len(machines)+3, column=0, columnspan=2, sticky="w", pady=(10, 5))

        self.solver_type = tk.StringVar(value="RK45")
        ttk.Radiobutton(control_frame, text="RK45 (Runge-Kutta 4-5)",
                       variable=self.solver_type, value="RK45").grid(
            row=len(machines)+4, column=0, columnspan=2, sticky="w", padx=20)
        ttk.Radiobutton(control_frame, text="Euler (Forward Euler)",
                       variable=self.solver_type, value="Euler").grid(
            row=len(machines)+5, column=0, columnspan=2, sticky="w", padx=20)

        # Simulation settings
        ttk.Separator(control_frame, orient='horizontal').grid(
            row=len(machines)+6, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(control_frame, text="Simulation Time (s):", font=('Arial', 9)).grid(
            row=len(machines)+7, column=0, sticky="w", pady=5)
        self.sim_time = tk.DoubleVar(value=5.0)
        ttk.Entry(control_frame, textvariable=self.sim_time, width=10).grid(
            row=len(machines)+7, column=1, sticky="ew", padx=5)

        ttk.Label(control_frame, text="Time Step (s):", font=('Arial', 9)).grid(
            row=len(machines)+8, column=0, sticky="w", pady=5)
        self.time_step = tk.DoubleVar(value=0.01)
        ttk.Entry(control_frame, textvariable=self.time_step, width=10).grid(
            row=len(machines)+8, column=1, sticky="ew", padx=5)

        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=len(machines)+9, column=0, columnspan=2, pady=20)

        self.start_btn = ttk.Button(button_frame, text="▶ Start",
                                    command=self.start_simulation, width=10)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = ttk.Button(button_frame, text="⬛ Stop",
                                   command=self.stop_simulation_func,
                                   width=10, state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=5)

        self.reset_btn = ttk.Button(button_frame, text="↺ Reset",
                                    command=self.reset_simulation, width=10)
        self.reset_btn.grid(row=0, column=2, padx=5)

        # Status display
        self.status_label = ttk.Label(control_frame, text="Status: Ready",
                                     font=('Arial', 9, 'bold'), foreground='green')
        self.status_label.grid(row=len(machines)+10, column=0, columnspan=2, pady=10)

        # Right panel - Visualization
        viz_frame = ttk.LabelFrame(tab2, text="Real-Time Visualization", padding=10)
        viz_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        viz_frame.grid_rowconfigure(0, weight=1)
        viz_frame.grid_columnconfigure(0, weight=1)

        # Create matplotlib figure for simulation
        self.sim_fig = Figure(figsize=(10, 7), dpi=100)
        self.sim_canvas = FigureCanvasTkAgg(self.sim_fig, viz_frame)
        self.sim_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Initialize parameters
        self.sim_params = {}
        self.sim_data = {'t': [], 'y1': [], 'y2': [], 'y3': []}
        self.update_machine_parameters()

        # Initialize plot
        self.reset_simulation_plot()

    def update_machine_parameters(self):
        """Update parameter inputs based on selected machine"""
        # Clear existing parameters
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        self.sim_params = {}
        machine = self.machine_type.get()

        if machine == "DC Motor":
            params = [
                ("Voltage (V):", "V", 220),
                ("Resistance (Ω):", "R", 2.0),
                ("Inductance (H):", "L", 0.5),
                ("Back EMF Const (V·s/rad):", "Ke", 0.5),
                ("Torque Const (N·m/A):", "Kt", 0.5),
                ("Inertia (kg·m²):", "J", 0.01),
                ("Friction (N·m·s/rad):", "B", 0.1),
                ("Load Torque (N·m):", "TL", 5.0)
            ]
        elif machine == "Synchronous Generator":
            params = [
                ("Terminal Voltage (V):", "Vt", 400),
                ("Field Current (A):", "If", 10),
                ("Sync. Reactance (Ω):", "Xs", 5.0),
                ("Armature Resistance (Ω):", "Ra", 0.5),
                ("Inertia (kg·m²):", "J", 50),
                ("Damping (N·m·s/rad):", "D", 2.0),
                ("Mech. Torque (N·m):", "Tm", 100)
            ]
        elif machine == "Induction Motor":
            params = [
                ("Voltage (V):", "V", 400),
                ("Stator Resistance (Ω):", "Rs", 1.0),
                ("Rotor Resistance (Ω):", "Rr", 0.8),
                ("Stator Inductance (H):", "Ls", 0.1),
                ("Rotor Inductance (H):", "Lr", 0.1),
                ("Mutual Inductance (H):", "M", 0.09),
                ("Inertia (kg·m²):", "J", 0.1),
                ("Load Torque (N·m):", "TL", 20)
            ]
        else:  # RL Circuit
            params = [
                ("Voltage (V):", "V", 100),
                ("Resistance (Ω):", "R", 10),
                ("Inductance (H):", "L", 0.5)
            ]

        for i, (label_text, var_name, default_val) in enumerate(params):
            ttk.Label(self.params_frame, text=label_text, font=('Arial', 8)).grid(
                row=i, column=0, sticky="w", pady=2)
            var = tk.DoubleVar(value=default_val)
            entry = ttk.Entry(self.params_frame, textvariable=var, width=12)
            entry.grid(row=i, column=1, sticky="ew", pady=2, padx=5)
            self.sim_params[var_name] = var

    def dc_motor_dynamics(self, t, y, params):
        """DC Motor differential equations"""
        i, omega = y
        V = params['V']
        R = params['R']
        L = params['L']
        Ke = params['Ke']
        Kt = params['Kt']
        J = params['J']
        B = params['B']
        TL = params['TL']

        # di/dt = (V - R*i - Ke*omega) / L
        di_dt = (V - R * i - Ke * omega) / L

        # domega/dt = (Kt*i - B*omega - TL) / J
        domega_dt = (Kt * i - B * omega - TL) / J

        return [di_dt, domega_dt]

    def rl_circuit_dynamics(self, t, y, params):
        """RL Circuit differential equation"""
        i = y[0]
        V = params['V']
        R = params['R']
        L = params['L']

        # di/dt = (V - R*i) / L
        di_dt = (V - R * i) / L

        return [di_dt, 0]  # Second state unused

    def synchronous_generator_dynamics(self, t, y, params):
        """Synchronous generator simplified dynamics"""
        delta, omega_dev = y  # Rotor angle and speed deviation
        Vt = params['Vt']
        If_val = params['If']
        Xs = params['Xs']
        Ra = params['Ra']
        J = params['J']
        D = params['D']
        Tm = params['Tm']

        # Simplified model
        Ef = If_val * 10  # Simplified field voltage
        Pe = (Ef * Vt * np.sin(delta)) / Xs  # Electrical power

        # d(delta)/dt = omega_dev
        ddelta_dt = omega_dev

        # d(omega_dev)/dt = (Tm - Pe - D*omega_dev) / J
        domega_dev_dt = (Tm - Pe - D * omega_dev) / J

        return [ddelta_dt, domega_dev_dt]

    def induction_motor_dynamics(self, t, y, params):
        """Induction motor simplified dynamics"""
        i, omega = y
        V = params['V']
        Rs = params['Rs']
        Rr = params['Rr']
        Ls = params['Ls']
        M = params['M']
        J = params['J']
        TL = params['TL']

        # Simplified single-phase equivalent
        omega_s = 2 * np.pi * 50  # Synchronous speed (50 Hz)
        slip = (omega_s - omega) / omega_s if omega_s != 0 else 1

        # di/dt = (V - Rs*i - M*omega) / Ls
        di_dt = (V - Rs * i - M * omega * slip) / Ls

        # Torque = k * i^2 * slip
        Te = 0.1 * i * i * slip

        # domega/dt = (Te - TL) / J
        domega_dt = (Te - TL) / J

        return [di_dt, domega_dt]

    def euler_solve(self, func, y0, t_span, t_eval, params):
        """Euler method ODE solver"""
        t_start, t_end = t_span
        t = np.array(t_eval)
        dt = t[1] - t[0]
        n = len(t)
        y = np.zeros((n, len(y0)))
        y[0] = y0

        for i in range(n - 1):
            dydt = func(t[i], y[i], params)
            y[i + 1] = y[i] + np.array(dydt) * dt

        return t, y

    def start_simulation(self):
        """Start the dynamic simulation"""
        if self.simulation_running:
            messagebox.showwarning("Warning", "Simulation already running")
            return

        self.simulation_running = True
        self.stop_simulation = False
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_label.config(text="Status: Running...", foreground='blue')

        # Reset data
        self.sim_data = {'t': [], 'y1': [], 'y2': [], 'y3': []}

        # Start simulation in separate thread
        self.simulation_thread = threading.Thread(target=self.run_simulation)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()

    def run_simulation(self):
        """Run the simulation with selected ODE solver"""
        try:
            # Get parameters
            sim_time = self.sim_time.get()
            dt = self.time_step.get()
            machine = self.machine_type.get()
            solver = self.solver_type.get()

            # Get machine parameters
            params = {}
            for key, var in self.sim_params.items():
                params[key] = var.get()

            # Select dynamics function and initial conditions
            if machine == "DC Motor":
                func = self.dc_motor_dynamics
                y0 = [0.0, 0.0]  # [current, angular velocity]
                labels = ['Current (A)', 'Speed (rad/s)', 'Torque (N·m)']
            elif machine == "RL Circuit":
                func = self.rl_circuit_dynamics
                y0 = [0.0, 0.0]
                labels = ['Current (A)', 'Voltage Drop (V)', 'Power (W)']
            elif machine == "Synchronous Generator":
                func = self.synchronous_generator_dynamics
                y0 = [0.1, 0.0]  # [rotor angle, speed deviation]
                labels = ['Rotor Angle (rad)', 'Speed Dev (rad/s)', 'Power (W)']
            else:  # Induction Motor
                func = self.induction_motor_dynamics
                y0 = [0.0, 0.0]  # [current, angular velocity]
                labels = ['Current (A)', 'Speed (rad/s)', 'Slip']

            # Time points
            t_eval = np.arange(0, sim_time, dt)

            # Solve based on selected solver
            if solver == "RK45":
                # Use scipy's RK45
                sol = solve_ivp(func, [0, sim_time], y0, method='RK45',
                              t_eval=t_eval, args=(params,), dense_output=True)
                t_solution = sol.t
                y_solution = sol.y.T
            else:
                # Use custom Euler method
                t_solution, y_solution = self.euler_solve(func, y0, [0, sim_time],
                                                         t_eval, params)

            # Update plot in real-time
            chunk_size = max(1, len(t_solution) // 50)  # Update 50 times

            for i in range(0, len(t_solution), chunk_size):
                if self.stop_simulation:
                    break

                end_idx = min(i + chunk_size, len(t_solution))

                # Append data
                self.sim_data['t'] = t_solution[:end_idx].tolist()
                self.sim_data['y1'] = y_solution[:end_idx, 0].tolist()
                self.sim_data['y2'] = y_solution[:end_idx, 1].tolist()

                # Calculate third parameter
                if machine == "DC Motor":
                    # Torque = Kt * i
                    Kt = params['Kt']
                    self.sim_data['y3'] = [Kt * i for i in self.sim_data['y1']]
                elif machine == "RL Circuit":
                    # Power = V * i
                    V = params['V']
                    self.sim_data['y3'] = [V * i for i in self.sim_data['y1']]
                elif machine == "Synchronous Generator":
                    # Power calculation
                    Vt = params['Vt']
                    If_val = params['If']
                    Xs = params['Xs']
                    Ef = If_val * 10
                    self.sim_data['y3'] = [Ef * Vt * np.sin(delta) / Xs
                                          for delta in self.sim_data['y1']]
                else:  # Induction Motor
                    # Slip calculation
                    omega_s = 2 * np.pi * 50
                    self.sim_data['y3'] = [(omega_s - omega) / omega_s
                                          for omega in self.sim_data['y2']]

                # Update plot
                self.root.after(0, self.update_simulation_plot, labels)
                time.sleep(0.02)  # Small delay for visualization

            # Simulation complete
            self.root.after(0, self.simulation_complete)

        except Exception as e:
            self.root.after(0, self.simulation_error, str(e))

    def update_simulation_plot(self, labels):
        """Update simulation plots in real-time"""
        if not self.sim_data['t']:
            return

        self.sim_fig.clear()
        gs = self.sim_fig.add_gridspec(3, 1, hspace=0.4)

        t = self.sim_data['t']

        # Plot 1
        ax1 = self.sim_fig.add_subplot(gs[0, 0])
        ax1.plot(t, self.sim_data['y1'], 'b-', linewidth=2)
        ax1.set_ylabel(labels[0], fontsize=9, fontweight='bold')
        ax1.set_title(f'{self.machine_type.get()} - Dynamic Response ({self.solver_type.get()} Solver)',
                     fontsize=11, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(0, self.sim_time.get())

        # Plot 2
        ax2 = self.sim_fig.add_subplot(gs[1, 0])
        ax2.plot(t, self.sim_data['y2'], 'r-', linewidth=2)
        ax2.set_ylabel(labels[1], fontsize=9, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0, self.sim_time.get())

        # Plot 3
        ax3 = self.sim_fig.add_subplot(gs[2, 0])
        ax3.plot(t, self.sim_data['y3'], 'g-', linewidth=2)
        ax3.set_xlabel('Time (s)', fontsize=9, fontweight='bold')
        ax3.set_ylabel(labels[2], fontsize=9, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.set_xlim(0, self.sim_time.get())

        self.sim_canvas.draw()

    def stop_simulation_func(self):
        """Stop the running simulation"""
        self.stop_simulation = True
        self.status_label.config(text="Status: Stopped", foreground='orange')
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.simulation_running = False

    def reset_simulation(self):
        """Reset simulation to initial state"""
        if self.simulation_running:
            self.stop_simulation_func()

        self.sim_data = {'t': [], 'y1': [], 'y2': [], 'y3': []}
        self.reset_simulation_plot()
        self.status_label.config(text="Status: Ready", foreground='green')

    def reset_simulation_plot(self):
        """Reset simulation plot to empty state"""
        self.sim_fig.clear()
        ax = self.sim_fig.add_subplot(111)
        ax.text(0.5, 0.5, f'Configure parameters and\nclick "Start" to begin simulation',
               ha='center', va='center', fontsize=14, transform=ax.transAxes)
        ax.axis('off')
        self.sim_canvas.draw()

    def simulation_complete(self):
        """Handle simulation completion"""
        self.status_label.config(text="Status: Completed", foreground='green')
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.simulation_running = False
        messagebox.showinfo("Simulation Complete",
                          f"Simulation completed successfully using {self.solver_type.get()} solver!")

    def simulation_error(self, error_msg):
        """Handle simulation error"""
        self.status_label.config(text="Status: Error", foreground='red')
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.simulation_running = False
        messagebox.showerror("Simulation Error", f"Error during simulation:\n{error_msg}")


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = ElectricalEngineeringSimulator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
