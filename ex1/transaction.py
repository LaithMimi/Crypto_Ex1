from .utils import PublicKey, TxID, Signature
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
        self._txid: Optional[TxID] = None

    def get_txid(self) -> TxID:
        """Returns the identifier of this transaction. This is the SHA256 of the transaction contents."""
        if self._txid is None:
            import hashlib

            hasher = hashlib.sha256()
            if self.input is None:
                hasher.update(b"\x00")
            else:
                hasher.update(b"\x01")
                hasher.update(self.input)
            hasher.update(self.output)
            hasher.update(self.signature)
            self._txid = TxID(hasher.digest())
        return self._txid

    def __eq__(self, other: object) -> bool:
        """Two transactions are equal if they have the same output, input and signature"""
        if not isinstance(other, Transaction):
            return False
        return self.output == other.output and self.input == other.input and self.signature == other.signature
