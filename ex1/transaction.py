from .utils import PublicKey, TxID, Signature,sha256
from typing import Optional


class Transaction:
    """Represents a transaction that moves a single coin
    A transaction with no source creates money. It will only be created by the bank."""

    def __init__(self, output: PublicKey, input: Optional[TxID], signature: Signature) -> None:
        # do not change the name of this field:
        self.output: PublicKey = output
        # do not change the name of this field:
        self.input: Optional[TxID] = input
        # do not change the name of this field:
        self.signature: Signature = signature

    def get_txid(self) -> TxID:
        """Returns the identifier of this transaction. This is the SHA256 of the transaction contents."""
        tx_contents = self.output + (self.input or b'') + self.signature
        return TxID(sha256(tx_contents))

    def __eq__(self, other: object) -> bool:
        """Two transactions are equal if they have the same output, input and signature"""
        if not isinstance(other, Transaction):
            return False
        return self.output == other.output and self.input == other.input and self.signature == other.signature
