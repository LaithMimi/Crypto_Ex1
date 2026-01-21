import pytest
from typing import Generator
from client.node import Node
from client.lightning_node import LightningNode
from client.network import Network
from client.utils import IPAddress, Contract, CompiledContract, compile
from testing_utils import ONE_ETH, EthTools, logger
import subprocess
import os
import signal
import time
import eth_account
from web3 import Web3
from web3.types import RPCEndpoint, TxParams, Wei, RPCResponse
import sys


@pytest.fixture(scope="session", autouse=True)
def start_hardhat() -> Generator[None, None, None]:
    """Start Hardhat network as a subprocess"""
    logger.info("Starting Hardhat node")

    # the command to start the hardhat node. This checks first if hardhat is installed (e.g. as is on CS machines)
    # and if not, it uses npx to run the hardhat node
    # note that you need to use `module load hardhat/18` to have hardhat on cs machines.
    cmd = "command -v hardhat >/dev/null 2>&1 && hardhat node || npx hardhat node"
    
    # On Windows, 'command -v' might not work. simpler command:
    # Also npx might ask for confirmation, so we use -y
    if sys.platform == "win32":
        cmd = "npx -y hardhat node"
    
    logger.info(f"Running the command {cmd}")
    
    kwargs = {}
    if sys.platform != "win32":
        kwargs['preexec_fn'] = os.setsid
    else:
        # On Windows, we can use creationflags to create a new process group if needed, 
        # but defaulting to standard behavior usually works for killing logic if simple terminate is used.
        # However, hardhat node might ignore SIGTERM on windows if not careful.
        # usually creating a new console window or just shell=True is enough for Popen defaults.
        pass

    # Redirect to file
    with open("hardhat.log", "w") as f:
        process = subprocess.Popen(
            cmd, shell=True, stdout=f, stderr=f, **kwargs)

        # Give the node some time to start up

        logger.info("Waiting for the Hardhat node to start")
        time.sleep(10) # Wait 10s

        try:
            # Provide the fixture value (here the control returns to the test execution)
            yield
        finally:
            logger.info("Terminating the Hardhat node")
            # Ensure that the process group is terminated
            if sys.platform != "win32":
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:
                # Windows equivalent to kill process tree
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(process.pid)])
            
            process.wait()


@pytest.fixture(scope="function", autouse=True)
def revert_snapshot(eth_tools: EthTools) -> Generator[str, None, None]:
    """Snapshot the blockchain at start so we can revert after every test"""
    logger.info("Creating a snapshot")
    response: RPCResponse = eth_tools.w3.provider.make_request(
        RPCEndpoint("evm_snapshot"), [])
    assert response['result'], "Snapshot creation failed!"

    snapshot_id = response['result']
    logger.info(f"Snapshot created with id {snapshot_id}")

    yield snapshot_id

    logger.info(f"Reverting to the snapshot {snapshot_id}")
    result = eth_tools.w3.provider.make_request(RPCEndpoint(
        "evm_revert"), [snapshot_id])
    assert result['result'], "Revert Blockchain state failed!"


@ pytest.fixture(scope="session")
def eth_tools(start_hardhat: None) -> EthTools:
    """Instance to interact with the blockchain during tests"""
    logger.info("Creating a Web3 instance")
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    assert w3.is_connected(), "Web3 is not connected to the Hardhat node."

    logger.info("Setting the base gas price on the node to 0")
    w3.provider.make_request(RPCEndpoint(
        "hardhat_setNextBlockBaseFeePerGas"), [0])

    logger.info("Setting the default gas price to 0 for the duration of tests")

    def pay_no_gas(web3: Web3, transaction_params: TxParams) -> Wei:
        return Web3.to_wei(0, "gwei")

    w3.eth.set_gas_price_strategy(pay_no_gas)
    return EthTools(w3)


def get_contract_file(filename: str) -> str:
    """Get the full path to contracts"""
    logger.info(f"Getting the full path to {filename}")
    current_dir = os.path.dirname(__file__)
    contracts_dir = os.path.join(current_dir, '..', 'contracts')
    contracts_dir = os.path.abspath(contracts_dir)

    # Check if the directory exists
    assert os.path.exists(contracts_dir)

    contracts_file = os.path.join(contracts_dir, filename)
    assert os.path.exists(contracts_file)
    return contracts_file


@ pytest.fixture(scope="session")
def compiled_contract() -> CompiledContract:
    """Compile the contract Channel.sol and return the ABI and bytecode"""
    contract_file = get_contract_file("Channel.sol")
    interface_file = get_contract_file("ChannelInterface.sol")
    logger.info("Compiling the contract")
    result = compile([contract_file, interface_file], "Channel")
    assert result.abi and result.bin
    return result


@ pytest.fixture
def network() -> Network:
    """Create a network object"""
    return Network()


@ pytest.fixture
def alice(eth_tools: EthTools, network: Network, compiled_contract: CompiledContract) -> Node:
    """Create node Alice with a balance of 1000 ether and return it"""
    logger.info("Creating node Alice")
    return create_node(eth_tools.w3, IPAddress("52.174.73.44"), network, compiled_contract)


@ pytest.fixture
def bob(eth_tools: EthTools, network: Network, compiled_contract: CompiledContract) -> Node:
    """Create node Bob with a balance of 1000 ether and return it"""
    logger.info("Creating node Bob")
    return create_node(eth_tools.w3, IPAddress("124.73.47.01"), network, compiled_contract)


@ pytest.fixture
def charlie(eth_tools: EthTools, network: Network, compiled_contract: CompiledContract) -> Node:
    """Create node Charlie with a balance of 1000 ether and return it"""
    logger.info("Creating node Charlie")
    return create_node(eth_tools.w3, IPAddress("117.23.0.1"), network, compiled_contract)


def create_node(w3: Web3, ip: IPAddress, network: Network, compiled_contract: CompiledContract) -> Node:
    """Create a node with a balance of 1000 ether and return it"""
    account = eth_account.Account.create()
    logger.info(
        f"Created account with address {account.address}, private key {account.key.hex()}")

    logger.info("Funding account with 1000 ether")
    amount = Web3.to_wei(1000, "ether")
    result = w3.provider.make_request(RPCEndpoint("hardhat_setBalance"), [
        account.address, Web3.to_hex(amount)])
    logger.info(result)

    logger.info("creating a Lightning node object")
    node = LightningNode(account.key, account.address, network, ip, w3,
                         compiled_contract.bin, compiled_contract.abi)

    logger.info(f"Setting the IP address of the node to {ip}")
    network.set_ip_address_of_node(node, ip)
    assert w3.eth.get_balance(account.address) == 1000*ONE_ETH
    assert node.private_key == account.key

    return node


@ pytest.fixture
def chan(eth_tools: EthTools, alice: Node, bob: Node, compiled_contract: CompiledContract) -> Contract:
    """Create a channel between Alice and Bob with a balance of 10 ether"""
    chan_address = alice.establish_channel(
        bob.eth_address, bob.ip_address, 10*ONE_ETH)
    return Contract(chan_address, compiled_contract.abi, eth_tools.w3)




