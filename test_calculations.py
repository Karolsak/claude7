#!/usr/bin/env python3
"""
Test script for parallel generator calculations
Demonstrates analytical solutions for scenarios A and B
"""

import numpy as np
from generator_calculations import GeneratorParameters, ParallelGeneratorSystem


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)


def print_section(text):
    """Print formatted section"""
    print("\n" + "-"*80)
    print(f"  {text}")
    print("-"*80)


def test_scenario_a():
    """Test Scenario A calculations"""
    print_header("SCENARIO A: Calculate Generator B Field Current")

    # Setup generators
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

    system = ParallelGeneratorSystem(gen_a_params, gen_b_params)

    print_section("Given Conditions")
    print(f"  Total Load Power:           420 kW")
    print(f"  Load Power Factor:          0.74 lagging")
    print(f"  Generator A Field Current:  14 A")
    print(f"  Power Sharing:              210 kW each")
    print(f"  Bus Voltage:                6000 V (rated)")

    # Calculate
    results = system.calculate_scenario_a()

    print_section("Results")
    print(f"  Generator B Field Current:  {results['IfB']:.3f} A")
    print(f"\n  Generator A:")
    print(f"    Active Power:             {results['PA']:.2f} kW")
    print(f"    Reactive Power:           {results['QA']:.2f} kVar")
    print(f"    Internal Voltage:         {results['EA']:.2f} V")
    print(f"\n  Generator B:")
    print(f"    Active Power:             {results['PB']:.2f} kW")
    print(f"    Reactive Power:           {results['QB']:.2f} kVar")
    print(f"    Internal Voltage:         {results['EB']:.2f} V")

    print_section("Verification")
    total_p = results['PA'] + results['PB']
    total_q = results['QA'] + results['QB']
    print(f"  Total Active Power:         {total_p:.2f} kW")
    print(f"  Total Reactive Power:       {total_q:.2f} kVar")
    print(f"  Active Power Error:         {abs(total_p - results['PL']):.4f} kW")
    print(f"  Reactive Power Error:       {abs(total_q - results['QL']):.4f} kVar")
    print(f"  Converged in:               {results['iterations']} iterations")

    return results


def test_scenario_b(results_a):
    """Test Scenario B calculations"""
    print_header("SCENARIO B: Calculate Generator A Field Current with Additional Load")

    # Setup generators
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

    system = ParallelGeneratorSystem(gen_a_params, gen_b_params)

    print_section("Given Conditions")
    print(f"  Additional Load:            100 kW at unity PF (lighting)")
    print(f"  Generator B:                Keep same as Scenario A")
    print(f"  Generator B Field Current:  {results_a['IfB']:.3f} A (fixed)")
    print(f"  Generator B Power:          {results_a['PB']:.2f} kW (maintained)")

    # Calculate
    results = system.calculate_scenario_b(results_a)

    print_section("Results")
    print(f"  Generator A Field Current:  {results['IfA']:.3f} A")
    print(f"\n  New Load Conditions:")
    print(f"    Total Load Power:         {results['PL']:.2f} kW")
    print(f"    Total Reactive Power:     {results['QL']:.2f} kVar")
    print(f"    Load Power Factor:        {results['cos_phi_L']:.4f} lagging")
    print(f"\n  Generator A:")
    print(f"    Active Power:             {results['PA']:.2f} kW")
    print(f"    Reactive Power:           {results['QA']:.2f} kVar")
    print(f"    Power Increase:           {results['PA'] - results_a['PA']:.2f} kW")
    print(f"    Field Current Change:     {results['IfA'] - results_a['IfA']:.3f} A")
    print(f"\n  Generator B:")
    print(f"    Active Power:             {results['PB']:.2f} kW (unchanged)")
    print(f"    Reactive Power:           {results['QB']:.2f} kVar (unchanged)")
    print(f"    Field Current:            {results['IfB']:.3f} A (unchanged)")

    print_section("Analysis")
    print(f"  Load Increase:              {results['additional_load']} kW")
    print(f"  Picked up by:               Generator A")
    print(f"  New Gen A Loading:          {results['PA']/gen_a_params.Pn*100:.1f}% of rated")
    print(f"  New Gen B Loading:          {results['PB']/gen_b_params.Pn*100:.1f}% of rated")

    return results


def test_custom_conditions():
    """Test custom operating conditions"""
    print_header("CUSTOM ANALYSIS: User-Defined Conditions")

    # Setup generators
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

    system = ParallelGeneratorSystem(gen_a_params, gen_b_params)

    # Custom conditions
    PL = 500  # kW
    cos_phi = 0.85
    IfA = 15  # A
    PA = 300  # kW
    V1 = 6000  # V

    print_section("Custom Conditions")
    print(f"  Total Load Power:           {PL} kW")
    print(f"  Load Power Factor:          {cos_phi} lagging")
    print(f"  Generator A Field Current:  {IfA} A")
    print(f"  Generator A Power:          {PA} kW")
    print(f"  Bus Voltage:                {V1} V")

    # Calculate reactive power
    phi = np.arccos(cos_phi)
    QL = PL * np.tan(phi)

    # Solve
    IfB, results = system.solve_load_sharing(PL, QL, V1, IfA, PA)

    print_section("Results")
    print(f"  Generator B Field Current:  {IfB:.3f} A")
    print(f"\n  Generator A:")
    print(f"    Active Power:             {results['PA']:.2f} kW ({results['PA']/gen_a_params.Pn*100:.1f}% rated)")
    print(f"    Reactive Power:           {results['QA']:.2f} kVar")
    print(f"\n  Generator B:")
    print(f"    Active Power:             {results['PB']:.2f} kW ({results['PB']/gen_b_params.Pn*100:.1f}% rated)")
    print(f"    Reactive Power:           {results['QB']:.2f} kVar")
    print(f"\n  Power Sharing:")
    print(f"    Generator A:              {results['PA']/(results['PA']+results['PB'])*100:.1f}%")
    print(f"    Generator B:              {results['PB']/(results['PA']+results['PB'])*100:.1f}%")


def display_generator_parameters():
    """Display generator parameters and base values"""
    print_header("GENERATOR PARAMETERS AND BASE VALUES")

    gen_a = GeneratorParameters(
        name="Generator A",
        Pn=300,  # kW
        V1n=6000,  # V
        Ifn=15,  # A
        xsd=1.7,
        cos_phi_n=0.8
    )

    gen_b = GeneratorParameters(
        name="Generator B",
        Pn=250,  # kW
        V1n=6000,  # V
        Ifn=11,  # A
        xsd=1.6,
        cos_phi_n=0.8
    )

    print_section("Generator A")
    print(f"  Nominal Power:              {gen_a.Pn} kW")
    print(f"  Nominal Voltage (L-L):      {gen_a.V1n} V")
    print(f"  Nominal Voltage (phase):    {gen_a.V1n/np.sqrt(3):.2f} V")
    print(f"  Nominal Field Current:      {gen_a.Ifn} A")
    print(f"  Nominal Power Factor:       {gen_a.cos_phi_n}")
    print(f"  d-axis Reactance (p.u.):    {gen_a.xsd}")
    print(f"\n  Calculated Base Values:")
    print(f"  Nominal Current:            {gen_a.In:.2f} A")
    print(f"  Base Impedance:             {gen_a.Zbase:.2f} Ω")
    print(f"  Synchronous Reactance:      {gen_a.Xsd:.2f} Ω")

    print_section("Generator B")
    print(f"  Nominal Power:              {gen_b.Pn} kW")
    print(f"  Nominal Voltage (L-L):      {gen_b.V1n} V")
    print(f"  Nominal Voltage (phase):    {gen_b.V1n/np.sqrt(3):.2f} V")
    print(f"  Nominal Field Current:      {gen_b.Ifn} A")
    print(f"  Nominal Power Factor:       {gen_b.cos_phi_n}")
    print(f"  d-axis Reactance (p.u.):    {gen_b.xsd}")
    print(f"\n  Calculated Base Values:")
    print(f"  Nominal Current:            {gen_b.In:.2f} A")
    print(f"  Base Impedance:             {gen_b.Zbase:.2f} Ω")
    print(f"  Synchronous Reactance:      {gen_b.Xsd:.2f} Ω")


def main():
    """Main test function"""
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + " "*10 + "PARALLEL SYNCHRONOUS GENERATORS - CALCULATION TEST" + " "*17 + "║")
    print("╚" + "═"*78 + "╝")

    # Display parameters
    display_generator_parameters()

    # Test Scenario A
    results_a = test_scenario_a()

    # Test Scenario B
    results_b = test_scenario_b(results_a)

    # Test custom conditions
    test_custom_conditions()

    print("\n" + "="*80)
    print("  TESTING COMPLETE")
    print("="*80)
    print("\nTo run the GUI application, execute:")
    print("  python3 parallel_generators_gui.py")
    print("\n")


if __name__ == "__main__":
    main()
