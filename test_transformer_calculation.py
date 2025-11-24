"""
Test script to verify transformer regulation calculation
without GUI dependencies
"""

import numpy as np


def calculate_transformer_regulation(rating_kva, v1, v2, r1, r2, x1, pf, pf_type="lagging"):
    """
    Calculate transformer regulation

    Parameters:
    - rating_kva: Transformer rating in kVA
    - v1: Primary voltage in V
    - v2: Secondary voltage in V
    - r1: Primary resistance in Ω
    - r2: Secondary resistance in Ω
    - x1: Primary reactance in Ω
    - pf: Power factor (0 to 1)
    - pf_type: "lagging", "leading", or "unity"

    Returns:
    - Dictionary with all calculated values
    """

    # Convert rating to VA
    rating = rating_kva * 1000

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
    if pf_type == "leading":
        sin_phi = -sin_phi
    elif pf_type == "unity":
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

    # Secondary current
    i2_fl = i1_fl * turn_ratio

    return {
        'regulation': regulation,
        'turn_ratio': turn_ratio,
        'r2_primary': r2_primary,
        'r_total': r_total,
        'x_total': x_total,
        'z_eq': z_eq,
        'i1_fl': i1_fl,
        'i2_fl': i2_fl,
        'copper_loss': copper_loss,
        'core_loss': core_loss,
        'total_loss': total_loss,
        'efficiency': efficiency,
        'output_power': output_power,
        'input_power': input_power
    }


def print_results(results):
    """Print formatted results"""
    print("=" * 70)
    print("TRANSFORMER REGULATION CALCULATION RESULTS")
    print("=" * 70)
    print(f"\nTurn Ratio (a):              {results['turn_ratio']:.3f}")
    print(f"R₂' (referred to primary):   {results['r2_primary']:.3f} Ω")
    print(f"Total Resistance (R₀₁):      {results['r_total']:.3f} Ω")
    print(f"Total Reactance (X₀₁):       {results['x_total']:.3f} Ω")
    print(f"Equivalent Impedance (Z₀₁):  {results['z_eq']:.3f} Ω")
    print(f"\nPrimary Full-Load Current:   {results['i1_fl']:.3f} A")
    print(f"Secondary Full-Load Current: {results['i2_fl']:.3f} A")
    print(f"\nCopper Loss:                 {results['copper_loss']:.2f} W")
    print(f"Core Loss (estimated):       {results['core_loss']:.2f} W")
    print(f"Total Loss:                  {results['total_loss']:.2f} W")
    print(f"\nOutput Power:                {results['output_power']/1000:.2f} kW")
    print(f"Input Power:                 {results['input_power']/1000:.2f} kW")
    print(f"Efficiency:                  {results['efficiency']:.3f} %")
    print("\n" + "=" * 70)
    print(f"║  VOLTAGE REGULATION:  {results['regulation']:6.3f} %                      ║")
    print("=" * 70)


if __name__ == "__main__":
    # Problem parameters
    print("\n" + "=" * 70)
    print("PROBLEM: Transformer Regulation Calculation")
    print("=" * 70)
    print("\nGiven:")
    print("  • Rating: 30 kVA")
    print("  • Primary Voltage: 6000 V")
    print("  • Secondary Voltage: 230 V")
    print("  • Primary Resistance: 10 Ω")
    print("  • Secondary Resistance: 0.016 Ω")
    print("  • Total Reactance (primary): 23 Ω")
    print("  • Power Factor: 0.8 lagging")
    print("  • Load: Full-load current")
    print("\n" + "=" * 70)

    # Calculate
    results = calculate_transformer_regulation(
        rating_kva=30,
        v1=6000,
        v2=230,
        r1=10,
        r2=0.016,
        x1=23,
        pf=0.8,
        pf_type="lagging"
    )

    # Print results
    print_results(results)

    # Additional analysis
    print("\n" + "=" * 70)
    print("ANALYSIS:")
    print("=" * 70)

    if results['regulation'] < 3:
        print("✓ Good regulation - suitable for most applications")
    elif results['regulation'] < 5:
        print("○ Moderate regulation - acceptable for general use")
    else:
        print("✗ High regulation - may need improvement")

    if results['efficiency'] > 95:
        print("✓ Excellent efficiency")
    elif results['efficiency'] > 90:
        print("✓ Good efficiency")
    else:
        print("○ Moderate efficiency")

    print("\n" + "=" * 70)
    print("CALCULATION STEPS:")
    print("=" * 70)
    print("\n1. Turn ratio: a = V₁/V₂ = 6000/230 = 26.087")
    print("\n2. Secondary resistance referred to primary:")
    print("   R₂' = R₂ × a² = 0.016 × (26.087)² = 10.89 Ω")
    print("\n3. Total equivalent resistance:")
    print("   R₀₁ = R₁ + R₂' = 10 + 10.89 = 20.89 Ω")
    print("\n4. Total equivalent reactance:")
    print("   X₀₁ = 23 Ω (given)")
    print("\n5. Primary full-load current:")
    print("   I₁ = S/V₁ = 30000/6000 = 5 A")
    print("\n6. Power factor angle:")
    print("   cos(φ) = 0.8")
    print("   sin(φ) = 0.6")
    print("\n7. Voltage regulation formula:")
    print("   Regulation = [I₁ × (R₀₁×cos(φ) + X₀₁×sin(φ))] / V₁ × 100")
    print(f"              = [5 × (20.89×0.8 + 23×0.6)] / 6000 × 100")
    print(f"              = [5 × (16.712 + 13.8)] / 6000 × 100")
    print(f"              = [5 × 30.512] / 6000 × 100")
    print(f"              = 152.56 / 6000 × 100")
    print(f"              = {results['regulation']:.3f} %")
    print("\n" + "=" * 70)
    print(f"\nFINAL ANSWER: {results['regulation']:.2f}% voltage regulation")
    print("=" * 70 + "\n")

    # Test with different power factors
    print("\n" + "=" * 70)
    print("COMPARISON: Regulation at Different Power Factors")
    print("=" * 70)
    print(f"\n{'PF Type':<15} {'PF Value':<12} {'Regulation (%)':<15}")
    print("-" * 70)

    test_cases = [
        ("Unity", 1.0, "unity"),
        ("0.9 Lagging", 0.9, "lagging"),
        ("0.8 Lagging", 0.8, "lagging"),
        ("0.7 Lagging", 0.7, "lagging"),
        ("0.8 Leading", 0.8, "leading"),
        ("0.9 Leading", 0.9, "leading"),
    ]

    for pf_name, pf_val, pf_type in test_cases:
        res = calculate_transformer_regulation(30, 6000, 230, 10, 0.016, 23, pf_val, pf_type)
        print(f"{pf_name:<15} {pf_val:<12.1f} {res['regulation']:<15.3f}")

    print("=" * 70 + "\n")
