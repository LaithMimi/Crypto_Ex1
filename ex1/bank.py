import secrets
from typing import Dict, List

from .utils import (
    BlockHash,
    PublicKey,
    Signature,
    TxID,
    GENESIS_BLOCK_PREV,
    verify,
)
from .transaction import Transaction
from .block import Block


class Bank:
    def __init__(self) -> None:
        """Creates a bank with an empty blockchain and an empty mempool."""
        self._mempool: List[Transaction] = []
        self._blocks: Dict[BlockHash, Block] = {} #dict is fast O(1) lookup time for blocks
        self._latest_hash: BlockHash = GENESIS_BLOCK_PREV
        self._utxo: Dict[TxID, Transaction] = {} #dict is fast O(1) lookup time for unspent transactions

    def add_transaction_to_mempool(self, transaction: Transaction) -> bool:
        """
        This function inserts the given transaction to the mempool.
        It will return False iff one of the following conditions hold:
        (i) the transaction is invalid (the signature fails)
        (ii) the source doesn't have the coin that he tries to spend
        (iii) there is contradicting tx in the mempool.
        (iv) there is no input (i.e., this is an attempt to create money from nothing)
        so this mempool basically has the verified txs but not yet committed to the blockchain
        """
        if transaction.input is None:
            return False

        prev_tx = self._utxo.get(transaction.input) 
        #verify that the coin trying to be spent actually exists in the bank’s unspent set
        if prev_tx is None:
            return False

        if any(tx.input == transaction.input for tx in self._mempool): #check if the coin is already being spent in the mempool
            return False

        if transaction in self._mempool: #check if the tx is already in the mempool
            return False

        message = self._serialize_for_signature(transaction.input, transaction.output) #serialize the transaction id and the target public key for the signature
        if not verify(message, transaction.signature, prev_tx.output): #verify the signature of the transaction
            return False

        self._mempool.append(transaction) #add the transaction to the mempool
        return True

    def end_day(self, limit: int = 10) -> BlockHash:
        """
        This function tells the bank that the day ended,
        and that the first `limit` transactions in the mempool should be committed to the blockchain.
        If there are fewer than 'limit' transactions in the mempool, a smaller block is created.
        If there are no transactions, an empty block is created. The hash of the block is returned.
        """
        if limit < 0:
            limit = 0

        to_commit = self._mempool[:limit]
        self._mempool = self._mempool[len(to_commit):]

        block = Block(to_commit, self._latest_hash)
        block_hash = block.get_block_hash()
        self._blocks[block_hash] = block
        self._latest_hash = block_hash

        for tx in to_commit:
            if tx.input is not None:
                self._utxo.pop(tx.input, None)
            self._utxo[tx.get_txid()] = tx #move on to the next tx in to_commit

        return block_hash

    def get_block(self, block_hash: BlockHash) -> Block:
        """
        This function returns a block object given its hash. If the block doesnt exist, an exception is thrown..
        """
        if block_hash not in self._blocks: #check if the block exists in the bank's blocks
            raise KeyError("Block not found") #if not, raise an exception
        return self._blocks[block_hash] #return the block

    def get_latest_hash(self) -> BlockHash:
        """
        This function returns the hash of the last Block that was created by the bank.
        """
        return self._latest_hash #return the hash of the last block

    def get_mempool(self) -> List[Transaction]:
        """
        This function returns the list of transactions that didn't enter any block yet.
        """
        return list(self._mempool) #return the list of transactions in the mempool

    def get_utxo(self) -> List[Transaction]:
        """
        This function returns the list of unspent transactions.
        """
        return list(self._utxo.values())

    def create_money(self, target: PublicKey) -> None:
        """
        This function inserts a transaction into the mempool that creates a single coin out of thin air. Instead of a signature,
        this transaction includes a random string of 48 bytes (so that every two creation transactions are different).
        This function is a secret function that only the bank can use (currently for tests, and will make sense in a later exercise).
        """
        random_sig = Signature(secrets.token_bytes(48)) #generate a random signature for the transaction
        tx = Transaction(output=target, input=None, signature=random_sig) #create a new transaction with the random signature
        self._mempool.append(tx) #add the transaction to the mempool

    @staticmethod
    def _serialize_for_signature(txid: TxID, target: PublicKey) -> bytes:
        return txid + target #serialize the transaction id and the target public key for the signature
