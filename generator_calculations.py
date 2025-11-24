#!/usr/bin/env python3
"""
Generator calculation module (no GUI dependencies)
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Dict


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
    """

    def __init__(self, params: GeneratorParameters):
        self.params = params

    def calculate_internal_voltage(self, If: float, If_rated: float, V_rated: float) -> float:
        """
        Calculate internal voltage based on field current
        Using linear magnetic characteristic (unsaturated)
        """
        k = V_rated / If_rated
        return k * If

    def calculate_excitation_current(self, P: float, Q: float, V: float) -> float:
        """
        Calculate required field excitation current for given operating point
        """
        S = np.sqrt(P**2 + Q**2)
        I = S / (np.sqrt(3) * V)
        phi = np.arctan2(Q, P)
        V_ph = V / np.sqrt(3)
        Xsd = self.params.xsd * self.params.Zbase
        E = np.sqrt((V_ph * np.cos(phi) + I * Xsd * np.sin(phi))**2 +
                    (V_ph * np.sin(phi) + I * Xsd * np.cos(phi))**2)
        If = E * self.params.Ifn / (self.params.V1n / np.sqrt(3))
        return If


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
        """
        PB = PL - PA

        # Generator A internal voltage
        EA = self.gen_a.calculate_internal_voltage(IfA, self.gen_a_params.Ifn,
                                                     self.gen_a_params.V1n / np.sqrt(3))

        # Iterative solution for load sharing
        IfB_guess = self.gen_b_params.Ifn

        for iteration in range(50):
            EB = self.gen_b.calculate_internal_voltage(IfB_guess, self.gen_b_params.Ifn,
                                                         self.gen_b_params.V1n / np.sqrt(3))

            # Reactive power calculation
            V_ph = V1 / np.sqrt(3)
            QA = ((EA - V_ph) / self.gen_a_params.Xsd) * V_ph
            QB = ((EB - V_ph) / self.gen_b_params.Xsd) * V_ph
            Q_total = (QA + QB) * 3 / 1000  # Convert to kVar

            # Check convergence
            error = abs(Q_total - QL)
            if error < 0.1:
                break

            # Adjust IfB
            if Q_total < QL:
                IfB_guess *= 1.01
            else:
                IfB_guess *= 0.99

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
        """Scenario (a): Calculate IfB for given conditions"""
        PL = 420  # kW
        cos_phi_L = 0.74
        phi_L = np.arccos(cos_phi_L)
        QL = PL * np.tan(phi_L)

        V1 = self.gen_a_params.V1n
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
        """Scenario (b): Additional 100 kW load at unity power factor"""
        PL = results_a['PL'] + 100  # 520 kW
        QL = results_a['QL']
        cos_phi_L = PL / np.sqrt(PL**2 + QL**2)

        V1 = self.gen_a_params.V1n
        IfB = results_a['IfB']

        PB = results_a['PB']
        PA = PL - PB

        QA = results_a['QA']
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
