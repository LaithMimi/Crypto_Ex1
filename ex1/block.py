import hashlib
from .utils import BlockHash
from .transaction import Transaction
from typing import List


class Block:
    def __init__(self, transactions: List[Transaction], prev_block_hash: BlockHash) -> None:
        self._transactions: List[Transaction] = list(transactions)
        self._prev_block_hash: BlockHash = prev_block_hash
        self._block_hash: BlockHash = self._compute_block_hash()

    def _compute_block_hash(self) -> BlockHash:
        hasher = hashlib.sha256()
        hasher.update(self._prev_block_hash)
        for tx in self._transactions:
            hasher.update(tx.get_txid())
        return BlockHash(hasher.digest())

    def get_block_hash(self) -> BlockHash:
        """returns hash of this block"""
        return self._block_hash

    def get_transactions(self) -> List[Transaction]:
        """returns the list of transactions in this block."""
        return list(self._transactions)

    def get_prev_block_hash(self) -> BlockHash:
        """Gets the hash of the previous block in the chain"""
        return self._prev_block_hash
