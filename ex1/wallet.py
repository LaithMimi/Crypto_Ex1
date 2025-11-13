from .utils import *
from .transaction import Transaction
from .bank import Bank
from typing import Optional, Dict, Set


class Wallet:
    def __init__(self) -> None:
        """This function generates a new wallet with a new private key."""
        self._private_key: PrivateKey
        self._public_key: PublicKey
        self._private_key, self._public_key = gen_keys() #generate a new private key and a corresponding public key
        self._utxo: Dict[TxID, Transaction] = {} #dict is fast O(1) lookup time for unspent transactions
        self._frozen: Set[TxID] = set() #set is fast O(1) lookup time for frozen transactions
        self._last_seen_block_hash = GENESIS_BLOCK_PREV 

    def update(self, bank: Bank) -> None:
        """
        This function updates the balance allocated to this wallet by querying the bank.
        Don't read all of the bank's utxo, but rather process the blocks since the last update one at a time.
        For this exercise, there is no need to validate all transactions in the block.
        """
        latest_hash = bank.get_latest_hash()
        if latest_hash == self._last_seen_block_hash:
            return

        blocks_to_process = []
        current_hash = latest_hash
        while current_hash != self._last_seen_block_hash and current_hash != GENESIS_BLOCK_PREV: #check if the current hash is the same as the last seen block hash or the genesis block
            block = bank.get_block(current_hash) #get the block from the bank
            blocks_to_process.append(block) #add the block to the list of blocks to process
            current_hash = block.get_prev_block_hash() #get the previous block hash

        if current_hash != self._last_seen_block_hash: #check if the current hash is not the same as the last seen block hash
            # current_hash is either GENESIS or a hash unknown to the wallet (should not happen in this exercise)
            if current_hash != GENESIS_BLOCK_PREV: #check if the current hash is the genesis block
                raise ValueError("Unknown block chain state encountered during update") #if not, raise an exception

        for block in reversed(blocks_to_process):
            for tx in block.get_transactions():
                if tx.input is not None and tx.input in self._utxo:
                    self._utxo.pop(tx.input, None) #remove the input from the unspent set
                    self._frozen.discard(tx.input)
                if tx.output == self._public_key:
                    self._utxo[tx.get_txid()] = tx #add the transaction to the unspent set

        self._last_seen_block_hash = latest_hash
        # discard any frozen coins that are no longer tracked
        self._frozen.intersection_update(self._utxo.keys())

    def create_transaction(self, target: PublicKey) -> Optional[Transaction]:
        """
        This function returns a signed transaction that moves an unspent coin to the target.
        It chooses the coin based on the unspent coins that this wallet had since the last update.
        If the wallet already spent a specific coin, but that transaction wasn't confirmed by the
        bank just yet (it still wasn't included in a block) then the wallet  should'nt spend it again
        until unfreeze_all() is called. The method returns None if there are no unspent outputs that can be used.
        """
        available = [txid for txid in self._utxo if txid not in self._frozen]
        if not available:
            return None #if there are no unspent outputs that can be used, return None

        input_txid = available[0]
        message = self._serialize_for_signature(input_txid, target) #serialize the transaction id and the target public key for the signature
        signature = sign(message, self._private_key) #sign the message using the private key
        transaction = Transaction(output=target, input=input_txid, signature=signature) #create a new transaction with the input, output and signature
        self._frozen.add(input_txid) #add the input to the frozen set
        return transaction

    def unfreeze_all(self) -> None:
        """
        Allows the wallet to try to re-spend outputs that it created transactions for (unless these outputs made it into the blockchain).
        """
        self._frozen.clear()

    def get_balance(self) -> int:
        """
        This function returns the number of coins that this wallet has.
        It will return the balance according to information gained when update() was last called.
        Coins that the wallet owned and sent away will still be considered as part of the balance until the spending
        transaction is in the blockchain.
        """
        return len(self._utxo)

    def get_address(self) -> PublicKey:
        """
        This function returns the public address of this wallet (see the utils module for generating keys).
        """
        return self._public_key

    @staticmethod
    def _serialize_for_signature(txid: TxID, target: PublicKey) -> bytes:
        return txid + target
