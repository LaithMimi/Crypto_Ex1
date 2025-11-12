from .utils import BlockHash, PublicKey
from .transaction import Transaction
from .block import Block
from typing import List


class Bank:
    def __init__(self) -> None:
        """Creates a bank with an empty blockchain and an empty mempool."""
        raise NotImplementedError()

    def add_transaction_to_mempool(self, transaction: Transaction) -> bool:
        """
        This function inserts the given transaction to the mempool.
        It will return False iff one of the following conditions hold:
        (i) the transaction is invalid (the signature fails)
        (ii) the source doesn't have the coin that he tries to spend
        (iii) there is contradicting tx in the mempool.
        (iv) there is no input (i.e., this is an attempt to create money from nothing)
        """
        raise NotImplementedError()

    def end_day(self, limit: int = 10) -> BlockHash:
        """
        This function tells the bank that the day ended,
        and that the first `limit` transactions in the mempool should be committed to the blockchain.
        If there are fewer than 'limit' transactions in the mempool, a smaller block is created.
        If there are no transactions, an empty block is created. The hash of the block is returned.
        """
        raise NotImplementedError()

    def get_block(self, block_hash: BlockHash) -> Block:
        """
        This function returns a block object given its hash. If the block doesnt exist, an exception is thrown..
        """
        raise NotImplementedError()

    def get_latest_hash(self) -> BlockHash:
        """
        This function returns the hash of the last Block that was created by the bank.
        """
        raise NotImplementedError()

    def get_mempool(self) -> List[Transaction]:
        """
        This function returns the list of transactions that didn't enter any block yet.
        """
        raise NotImplementedError()

    def get_utxo(self) -> List[Transaction]:
        """
        This function returns the list of unspent transactions.
        """
        raise NotImplementedError()

    def create_money(self, target: PublicKey) -> None:
        """
        This function inserts a transaction into the mempool that creates a single coin out of thin air. Instead of a signature,
        this transaction includes a random string of 48 bytes (so that every two creation transactions are different).
        This function is a secret function that only the bank can use (currently for tests, and will make sense in a later exercise).
        """
        raise NotImplementedError()
