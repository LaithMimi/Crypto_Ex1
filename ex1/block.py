from .utils import BlockHash, sha256
from .transaction import Transaction
from typing import List


class Block:
    # implement __init__ as you see fit.
    def __init__(self, prev_block_hash: BlockHash, transactions: List[Transaction]) -> None:
        self.prev_block_hash: BlockHash = prev_block_hash
        self.transactions: List[Transaction] = transactions
        self.block_hash: BlockHash = self.get_block_hash()


    def get_block_hash(self) -> BlockHash:
        """returns hash of this block"""
        block_contents = self.prev_block_hash + b''.join(tx.get_txid() for tx in self.transactions)
        return BlockHash(sha256(block_contents))

    def get_transactions(self) -> List[Transaction]:
        """returns the list of transactions in this block."""
        return self.transactions

    def get_prev_block_hash(self) -> BlockHash:
        """Gets the hash of the previous block in the chain"""
        return self.prev_block_hash
