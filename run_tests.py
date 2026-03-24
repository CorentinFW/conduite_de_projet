#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Emotion-Reaction Dialogue Engine
Script de Test pour le Moteur de Dialogue Émotion-Réaction

This script runs automated tests to verify the functionality.
Ce script exécute des tests automatisés pour vérifier les fonctionnalités.
"""

import subprocess
import json
import sys

def run_test(name, input_file, expected_states=None):
    """
    Run a test with the given input file.
    Exécute un test avec le fichier d'entrée donné.
    """
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    
    try:
        # Run the command using PowerShell
        # Exécuter la commande avec PowerShell
        cmd = f"Get-Content {input_file} | python EmotionDamage.py"
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"Input file: {input_file}")
        print(f"\nOutput:")
        print(result.stdout)
        
        # Parse and validate states if expected
        # Parser et valider les états si attendus
        if expected_states:
            lines = result.stdout.strip().split('\n')
            actual_states = []
            
            for line in lines:
                if line.strip():
                    try:
                        data = json.loads(line)
                        actual_states.append(data.get('next_state'))
                    except:
                        pass
            
            print(f"\nExpected states: {expected_states}")
            print(f"Actual states:   {actual_states}")
            
            if actual_states == expected_states:
                print("✅ PASSED - States match!")
                return True
            else:
                print("❌ FAILED - States don't match!")
                return False
        else:
            print("✅ PASSED - No state validation required")
            return True
            
    except subprocess.TimeoutExpired:
        print("❌ FAILED - Test timed out!")
        return False
    except Exception as e:
        print(f"❌ FAILED - Error: {e}")
        return False

def main():
    """
    Main test runner.
    Exécuteur principal des tests.
    """
    print("="*70)
    print("EMOTION-REACTION DIALOGUE ENGINE - AUTOMATED TESTS")
    print("MOTEUR DE DIALOGUE ÉMOTION-RÉACTION - TESTS AUTOMATISÉS")
    print("="*70)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Basic STDIN functionality
    # Test 1: Fonctionnalité STDIN basique
    if run_test(
        "Basic STDIN Functionality",
        "test_stdin.jsonl",
        ["SUPPORT", "SUPPORT", "SUPPORT", "DEESCALATE"]
    ):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 2: State transitions
    # Test 2: Transitions d'état
    if run_test(
        "State Transitions",
        "test_states.jsonl",
        ["SUPPORT", "SUPPORT", "DEESCALATE", "DEESCALATE", "DEESCALATE"]
    ):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Summary
    # Résumé
    print("\n" + "="*70)
    print("TEST SUMMARY / RÉSUMÉ DES TESTS")
    print("="*70)
    print(f"Tests passed: {tests_passed} ✅")
    print(f"Tests failed: {tests_failed} {'❌' if tests_failed > 0 else ''}")
    print(f"Total tests:  {tests_passed + tests_failed}")
    print("="*70)
    
    # Exit code
    # Code de sortie
    sys.exit(0 if tests_failed == 0 else 1)

if __name__ == "__main__":
    main()
