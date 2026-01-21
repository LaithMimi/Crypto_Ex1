import logging
from web3.types import RPCEndpoint
import web3
from web3 import Web3


RevertException = web3.exceptions.ContractLogicError
ONE_ETH = Web3.to_wei(1, 'ether')


# Create a logger
logger = logging.getLogger("action_log")
# logger.addHandler(handler)
logger.setLevel(logging.INFO)


class EthTools:
    def __init__(self, w3: Web3) -> None:
        self.w3 = w3
        self.start_tx_count()
        self.get_balance = w3.eth.get_balance  # A shorter name for this useful method

    def mine_blocks(self, num_blocks: int) -> None:
        """Mine a number of blocks"""
        logger.info(f"Mining {num_blocks} blocks")
        # the following line replaces several RPC "eth_mine" calls that would run in a loop:
        result = self.w3.provider.make_request(
            RPCEndpoint("hardhat_mine"), [Web3.to_hex(num_blocks)])
        assert 'error' not in result, f"Hardhat node failed to mine blocks: {result}"

    def start_tx_count(self) -> None:
        """Starts (or re-starts) counting transactions submitted to the blockchain from the current block"""
        self._count = 0
        self._start_block = int(self.w3.eth.get_block_number())
        self._counted_up_to_block = self._start_block

    @property
    def tx_count(self) -> int:
        """Returns the number of transactions submitted to the blockchain since the start of the count"""
        current_block = int(self.w3.eth.get_block_number())
        while self._counted_up_to_block < current_block:
            self._counted_up_to_block += 1
            num_txs = len(self.w3.eth.get_block(
                self._counted_up_to_block, full_transactions=False)["transactions"])
            self._count += num_txs
        return self._count
