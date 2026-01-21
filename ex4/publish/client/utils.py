import solcx
from dataclasses import dataclass
from typing import NewType, Tuple, Any, Protocol, Optional, Dict, List
import eth_account
import eth_typing
from web3 import Web3
import web3
from hexbytes import HexBytes
from collections import namedtuple


APPEAL_PERIOD = 5  # the appeal period in blocks.

Signature = NewType('Signature', Tuple[int, str, str])
PrivateKey = NewType("PrivateKey", HexBytes)
EthereumAddress = eth_typing.ChecksumAddress
IPAddress = NewType('IPAddress', str)
CompiledContract = namedtuple('CompiledContract', ['bin', 'abi'])


def to_32byte_hex(val: bytes) -> str:
    return Web3.to_hex(Web3.to_bytes(val).rjust(32, b'\0'))


@dataclass(frozen=True)
class ChannelStateMessage:
    """The message represents the state of a payment channel. 
    This object is immutable."""
    contract_address: EthereumAddress
    balance1: int  # internal balance of the channel's creator
    balance2: int  # internal balance of the other party (not the creator)
    serial_number: int
    sig: Signature = Signature((
        0, to_32byte_hex(b""), to_32byte_hex(b"")))

    @ property
    def message_hash(self) -> eth_account.messages.SignableMessage:
        message = [self.contract_address,
                   self.balance1, self.balance2, self.serial_number]
        message_hash = Web3.solidity_keccak(
            ["address", "uint256", "uint256", "uint256"], message)
        encoded_message = eth_account.messages.encode_defunct(message_hash)
        return encoded_message


def sign(private_key: PrivateKey, msg: ChannelStateMessage) -> ChannelStateMessage:
    """returns a new version of the given state message, 
    signed by the given private key. The signature is added to the new message."""

    sig = eth_account.Account.sign_message(msg.message_hash, private_key)
    vrs = Signature((sig.v, to_32byte_hex(sig.r), to_32byte_hex(sig.s)))

    return ChannelStateMessage(msg.contract_address, msg.balance1, msg.balance2, msg.serial_number,
                               vrs)


def validate_signature(msg: ChannelStateMessage, pk: EthereumAddress) -> bool:
    """validates the signature of the channel state message"""
    return bool(eth_account.Account.recover_message(
        msg.message_hash, vrs=msg.sig) == pk)


def compile(files: List[str], contract_name: str) -> CompiledContract:
    """compiles a solidity contract and returns its binary and abi"""
    solcx.install_solc('0.8.19')
    solcx.set_solc_version('0.8.19')

    compiled_sol = solcx.compile_files(
        files, output_values=['abi', 'bin'])

    for contract in compiled_sol:
        if contract.endswith(":" + contract_name):
            contract_interface = compiled_sol[contract]
            return CompiledContract(contract_interface['bin'], contract_interface['abi'])
    raise ValueError(f"Contract {contract_name} not found")


class HasEthAccount(Protocol):
    """Defines a type for objects that have an ethereum address and a private key."""
    @property
    def eth_address(self) -> EthereumAddress: ...

    @property
    def private_key(self) -> PrivateKey: ...


class Contract:
    @staticmethod
    def deploy(w3: Web3, bytecode: str, abi: Dict[str, Any], from_account: HasEthAccount, ctor_args: Tuple[Any, ...], deploy_kwargs: Optional[web3.types.TxParams] = None) -> 'Contract':
        """Deploy a contract using the given web3 instance, bytecode and abi. The constructor arguments are given as a tuple. 
        from_account is the source account that is deploying. Additional arguments for the transactions 
        (like the value it is carrying in wei) can be specified in deploy_kwargs."""
        if deploy_kwargs is None:
            deploy_kwargs = {}
        if 'from' not in deploy_kwargs:
            deploy_kwargs['from'] = from_account.eth_address
        if 'nonce' not in deploy_kwargs:
            deploy_kwargs['nonce'] = w3.eth.get_transaction_count(
                from_account.eth_address)

        contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        tx = contract.constructor(
            *ctor_args).build_transaction(deploy_kwargs)
        signed_tx = w3.eth.account.sign_transaction(
            tx, private_key=from_account.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        assert tx_receipt["status"] == 1
        assert "contractAddress" in tx_receipt
        assert tx_receipt["contractAddress"] is not None
        addr = tx_receipt["contractAddress"]
        return Contract(addr, abi, w3)

    def __init__(self, contract_address: EthereumAddress, abi: Dict[str, Any], w3: Web3) -> None:
        """initializes a contract object that allows calling and transacting with the contract at the specified address, 
        using the given web3 instance."""
        self._w3 = w3
        self._address = contract_address
        self._contract = self._w3.eth.contract(
            address=contract_address, abi=abi)

    def call(self, func_name: str, func_args: Optional[Tuple[Any, ...]] = None, call_kwargs: Optional[web3.types.TxParams] = None) -> Any:
        """ call a function of the contract. This is for 'view' or 'pure' functions only that do 
        not change the state of the blockchain."""
        if call_kwargs is None:
            call_kwargs = {}
        if func_args is None:
            func_args = ()
        return self._contract.functions.__getattribute__(func_name)(*func_args).call(call_kwargs)

    def transact(self, user: HasEthAccount, func_name: str,
                 func_args: Optional[Tuple[Any, ...]] = None,
                 transact_kwargs: Optional[web3.types.TxParams] = None) -> web3.types.TxReceipt:
        """ Calls a method on a deployed smart contract. This code will send a transaction signed 
        with the key of the user. The user is an object that has an ethereum adress and a private key. 
        If transact_kwargs are supplied, they will be used, including a 'from' 
        field that may be different from the signer of the tx."""
        if transact_kwargs is None:
            transact_kwargs = {}
        if 'from' not in transact_kwargs:
            transact_kwargs['from'] = user.eth_address
        if 'nonce' not in transact_kwargs:
            transact_kwargs['nonce'] = self._w3.eth.get_transaction_count(
                user.eth_address)
        if func_args is None:
            func_args = ()

        tx = self._contract.functions.__getattribute__(func_name)(
            *func_args).build_transaction(transact_kwargs)
        signed_tx = self._w3.eth.account.sign_transaction(
            tx, private_key=user.private_key)
        tx_hash = self._w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return self._w3.eth.wait_for_transaction_receipt(tx_hash)

    @ property
    def address(self) -> EthereumAddress:
        """The ethereum address of the contract."""
        return self._address
