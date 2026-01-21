from web3 import Web3
import solcx  # type: ignore
from typing import Any
from web3.types import Wei

# run the line below to install the compiler ->  only once is needed.
solcx.install_solc(version='latest')


def compile(file_name: str) -> Any:
    # set the version
    solcx.set_solc_version('0.8.19')

    # compile
    compiled_sol = solcx.compile_files(
        [file_name], output_values=['abi', 'bin'])

    # retrieve the contract interface
    contract_id, contract_interface = compiled_sol.popitem()
    return contract_interface['bin'], contract_interface['abi']


bytecode, abi = compile("greeter.sol")


# Connect to the blockchain: (Hardhat node should be running at this port)
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# deploy the contract
Greeter = w3.eth.contract(abi=abi, bytecode=bytecode)

# Submit the transaction that deploys the contract. It is deployed by accounts[0] which is the first of the 10 pre-made accounts created by hardhat.
tx_hash = Greeter.constructor("Hello!").transact(
    {'from': w3.eth.accounts[0]})

# Wait for the transaction to be mined, and get the transaction receipt
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

# get a contract instance
print(tx_receipt)
greeter = w3.eth.contract(address=tx_receipt["contractAddress"], abi=abi)

# here we call a view function (that does not require a transaction to the blockchain). This is done via '.call()'
print(greeter.functions.greet().call())

# here we call a function that changes the state and does require a blockchain transaction. This is done via '.transact()'
tx_hash = greeter.functions.setGreeting(
    'Nihao').transact({"from": w3.eth.accounts[1]})  # type: ignore

# wait for a transaction to be mined.
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

# check the greeting again.
print(greeter.functions.greet().call())

tx_hash = w3.eth.send_transaction({
    'to': greeter.address,
    'from': w3.eth.accounts[1],  # type: ignore
    'value': Wei(10**16)
})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print("the contract's balance is:", w3.eth.get_balance(greeter.address))

# now we withdraw:
tx_hash = greeter.functions.withdraw().transact(
    {"from": w3.eth.accounts[2]})  # type: ignore
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print("the contract's balance is:", w3.eth.get_balance(greeter.address))
print("account 2 now has:", w3.eth.get_balance(
    w3.eth.accounts[2]))  # type: ignore
