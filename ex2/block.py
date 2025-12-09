from .utils import BlockHash
from .transaction import Transaction
from typing import List


class Block:
    """This class represents a block."""

    def __init__(self, prev_block_hash: BlockHash, transactions: List[Transaction]) -> None:
        """creates a block with the given previous block hash and a list of transactions"""
        self._prev_block_hash: BlockHash = prev_block_hash
        self._transactions: List[Transaction] = list(transactions)

    def get_block_hash(self) -> BlockHash:
        """Gets the hash of this block. 
        This function is used by the tests. Make sure to compute the result from the data in the block every time 
        and not to cache the result"""
        import hashlib

        hasher = hashlib.sha256()
        hasher.update(self._prev_block_hash)
        for tx in self._transactions:
            hasher.update(tx.get_txid())
        return BlockHash(hasher.digest())

    def get_transactions(self) -> List[Transaction]:
        """
        returns the list of transactions in this block.
        """
        return list(self._transactions)

    def get_prev_block_hash(self) -> BlockHash:
        """Gets the hash of the previous block"""
        return self._prev_block_hash
