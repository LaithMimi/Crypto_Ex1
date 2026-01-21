#!/usr/bin/env python3
"""
Compile RPS.sol and generate RPS.abi and RPS.bin files
"""

from solcx import compile_source, install_solc
import json

def compile_rps():
    # Install the specific Solidity version if not already installed
    print("Installing Solidity compiler version 0.8.19...")
    install_solc('0.8.19')
    
    # Read the Solidity source file
    print("Reading RPS.sol...")
    with open('RPS.sol', 'r') as file:
        contract_source = file.read()
    
    # Compile the contract
    print("Compiling RPS.sol...")
    compiled_sol = compile_source(
        contract_source,
        output_values=['abi', 'bin'],
        solc_version='0.8.19'
    )
    
    # Extract contract interface
    contract_id, contract_interface = compiled_sol.popitem()
    
    # Write ABI to file
    abi = contract_interface['abi']
    with open('RPS.abi', 'w') as f:
        json.dump(abi, f, indent=2)
    print("✓ Generated RPS.abi")
    
    # Write bytecode to file
    bytecode = contract_interface['bin']
    with open('RPS.bin', 'w') as f:
        f.write(bytecode)
    print("✓ Generated RPS.bin")
    
    print("\n✅ Compilation successful!")
    print(f"   ABI size: {len(json.dumps(abi))} bytes")
    print(f"   Bytecode size: {len(bytecode)} bytes")

if __name__ == '__main__':
    compile_rps()
