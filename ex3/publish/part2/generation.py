from web3 import Web3
import solcx  # type: ignore
from typing import Any
from web3.types import Wei

# run the line below to install the compiler ->  only once is needed.
solcx.install_solc(version='0.8.19')


def compile(file_name: str) -> Any:
    # set the version
    solcx.set_solc_version('0.8.19')

    # compile
    compiled_sol = solcx.compile_files(
        [file_name], output_values=['abi', 'bin'])

    # retrieve the contract interface
    contract_id, contract_interface = compiled_sol.popitem()
    return contract_interface['bin'], contract_interface['abi']


bytecode, abi = compile("RPS.sol")
with open("RPS.abi", "w") as f:
    for line in abi:
        f.write(str(line))
        f.write("\n")

with open("RPS.bin", "w") as f:
    f.write(bytecode)