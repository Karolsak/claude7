#!/usr/bin/env python3
"""
Comprehensive test suite for synchronous generator analysis tools
Verifies syntax, calculations, and code quality
"""

import sys
import subprocess

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(text)
    print("="*80 + "\n")

def test_syntax():
    """Test Python syntax"""
    print_header("TEST 1: SYNTAX CHECK")
    
    files = [
        'synchronous_generator_solver.py',
        'synchronous_generator_analysis.py'
    ]
    
    all_passed = True
    for file in files:
        try:
            result = subprocess.run(
                ['python3', '-m', 'py_compile', file],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"✓ {file:45s} - Syntax OK")
            else:
                print(f"✗ {file:45s} - Syntax ERROR")
                print(result.stderr)
                all_passed = False
        except Exception as e:
            print(f"✗ {file:45s} - Error: {e}")
            all_passed = False
    
    return all_passed

def test_imports():
    """Test module imports"""
    print_header("TEST 2: MODULE IMPORTS")
    
    required = ['numpy', 'scipy', 'matplotlib']
    all_passed = True
    
    for module in required:
        try:
            __import__(module)
            print(f"✓ {module:20s} - Available")
        except ImportError:
            print(f"✗ {module:20s} - MISSING")
            all_passed = False
    
    return all_passed

def test_calculations():
    """Test calculation accuracy"""
    print_header("TEST 3: CALCULATION VERIFICATION")
    
    try:
        from synchronous_generator_solver import SynchronousGeneratorSolver
        import numpy as np
        
        solver = SynchronousGeneratorSolver()
        results = solver.solve_all(temperature=120)
        
        # Expected values (with tolerance)
        tests = [
            ('Xsd', results['Xsd'], 5.8757, 0.001, 'Ω'),
            ('Xsq', results['Xsq'], 2.9908, 0.001, 'Ω'),
            ('Ifn', results['Ifn'], 18.5534, 0.01, 'A'),
            ('Vf', results['Vf'], 20.6759, 0.01, 'V'),
            ('Rf_temp', results['Rf_temp'], 1.1144, 0.001, 'Ω'),
        ]
        
        all_passed = True
        for name, calculated, expected, tolerance, unit in tests:
            error = abs(calculated - expected)
            if error < tolerance:
                print(f"✓ {name:15s} = {calculated:10.4f} {unit:3s} (expected: {expected:.4f})")
            else:
                print(f"✗ {name:15s} = {calculated:10.4f} {unit:3s} (expected: {expected:.4f}, error: {error:.6f})")
                all_passed = False
        
        # Additional checks
        saliency_ratio = results['Xsd'] / results['Xsq']
        if 1.5 <= saliency_ratio <= 2.5:
            print(f"✓ Saliency ratio  = {saliency_ratio:10.4f}     (within valid range)")
        else:
            print(f"✗ Saliency ratio  = {saliency_ratio:10.4f}     (outside valid range)")
            all_passed = False
        
        if abs(results['delta']) < 180:
            print(f"✓ Power angle    = {results['delta']:10.4f} °   (reasonable value)")
        else:
            print(f"✗ Power angle    = {results['delta']:10.4f} °   (unusual value)")
            all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_solver_class():
    """Test solver class structure"""
    print_header("TEST 4: CLASS STRUCTURE")
    
    try:
        from synchronous_generator_solver import SynchronousGeneratorSolver
        
        solver = SynchronousGeneratorSolver()
        
        methods = [
            'calculate_synchronous_reactances',
            'calculate_nominal_field_current',
            'calculate_field_voltage',
            'solve_all',
            'print_detailed_results'
        ]
        
        all_passed = True
        for method in methods:
            if hasattr(solver, method):
                print(f"✓ Method: {method:40s} - Present")
            else:
                print(f"✗ Method: {method:40s} - MISSING")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Class structure test failed: {e}")
        return False

def test_gui_class():
    """Test GUI class structure (if Tkinter available)"""
    print_header("TEST 5: GUI CLASS STRUCTURE (Optional)")
    
    try:
        # Try to import without actually instantiating
        # (to avoid display issues)
        import sys
        import os
        
        # Read the file and check for class definitions
        with open('synchronous_generator_analysis.py', 'r') as f:
            content = f.read()
        
        classes = [
            'SynchronousGeneratorSolver',
            'SynchronousGeneratorDynamics',
            'AdvancedGeneratorGUI'
        ]
        
        all_passed = True
        for cls in classes:
            if f'class {cls}' in content:
                print(f"✓ Class: {cls:40s} - Defined")
            else:
                print(f"✗ Class: {cls:40s} - MISSING")
                all_passed = False
        
        print("\nNote: GUI functionality not fully tested (requires display)")
        return all_passed
        
    except Exception as e:
        print(f"✗ GUI class test failed: {e}")
        return False

def test_documentation():
    """Test documentation completeness"""
    print_header("TEST 6: DOCUMENTATION")
    
    files = [
        'README.md',
        'SOLUTION_SUMMARY.txt',
        'QUICK_START.md',
        'requirements.txt'
    ]
    
    all_passed = True
    for file in files:
        import os
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✓ {file:30s} - Present ({size} bytes)")
        else:
            print(f"✗ {file:30s} - MISSING")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print(" "*20 + "SYNCHRONOUS GENERATOR ANALYSIS")
    print(" "*25 + "TEST SUITE")
    print("="*80)
    
    tests = [
        ("Syntax Check", test_syntax),
        ("Module Imports", test_imports),
        ("Calculations", test_calculations),
        ("Solver Class", test_solver_class),
        ("GUI Class", test_gui_class),
        ("Documentation", test_documentation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print_header("TEST SUMMARY")
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status:15s} - {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print(" "*25 + "ALL TESTS PASSED ✓")
        print("="*80 + "\n")
        print("✓ No syntax errors found")
        print("✓ All calculations verified")
        print("✓ Code structure validated")
        print("✓ Documentation complete")
        print("\nReady for use!")
        return 0
    else:
        print(" "*25 + "SOME TESTS FAILED ✗")
        print("="*80 + "\n")
        print("Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
