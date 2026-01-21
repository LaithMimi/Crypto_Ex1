from client.node import Node
from testing_utils import ONE_ETH, EthTools, RevertException
from client.utils import APPEAL_PERIOD, Contract, sign, ChannelStateMessage
import pytest


# here are tests for 3 basic scenarios. These also show how the work-flow with nodes proceeds.

def test_open_and_immediate_close(eth_tools: EthTools, alice: Node, bob: Node) -> None:
    eth_tools.start_tx_count()

    alice_init_balance = eth_tools.get_balance(alice.eth_address)
    bob_init_balance = eth_tools.get_balance(bob.eth_address)

    # Creating channel
    chan_address = alice.establish_channel(
        bob.eth_address, bob.ip_address, ONE_ETH)
    assert eth_tools.tx_count == 1

    # channel created, chan_address
    assert eth_tools.get_balance(chan_address) == ONE_ETH

    # ALICE CLOSING UNILATERALLY
    alice.close_channel(chan_address)
    assert eth_tools.tx_count == 2

    # Waiting
    eth_tools.mine_blocks(APPEAL_PERIOD+2)

    # Bob Withdraws (but this does not generate a transaction since his balance is 0)
    assert bob.withdraw_funds(chan_address) == 0

    # Alice Withdraws
    assert alice.withdraw_funds(chan_address) == ONE_ETH
    assert eth_tools.tx_count == 3

    assert eth_tools.get_balance(chan_address) == 0

    assert alice_init_balance == eth_tools.get_balance(
        alice.eth_address)
    assert bob_init_balance == eth_tools.get_balance(
        bob.eth_address)


def test_nice_open_transfer_and_close(eth_tools: EthTools,  alice: Node, bob: Node) -> None:
    alice_init_balance = eth_tools.get_balance(alice.eth_address)
    bob_init_balance = eth_tools.get_balance(bob.eth_address)

    # Creating channel
    chan_address = alice.establish_channel(
        bob.eth_address, bob.ip_address, 10*ONE_ETH)
    assert eth_tools.get_balance(chan_address) == 10*ONE_ETH

    # Alice sends money thrice
    eth_tools.start_tx_count()
    alice.send(chan_address, ONE_ETH)
    alice.send(chan_address, ONE_ETH)
    alice.send(chan_address, ONE_ETH)
    assert eth_tools.tx_count == 0

    # BOB CLOSING UNILATERALLY
    bob.close_channel(chan_address)

    # waiting
    eth_tools.mine_blocks(APPEAL_PERIOD+2)
    assert eth_tools.get_balance(chan_address) == 10*ONE_ETH

    # Bob Withdraws
    amount_withdrawn = bob.withdraw_funds(chan_address)
    assert amount_withdrawn == 3*ONE_ETH
    assert eth_tools.get_balance(chan_address) == 7*ONE_ETH

    # Alice Withdraws
    assert alice.withdraw_funds(chan_address) == 7*ONE_ETH
    assert eth_tools.get_balance(chan_address) == 0

    assert alice_init_balance == eth_tools.get_balance(
        alice.eth_address) + 3*ONE_ETH
    assert bob_init_balance == eth_tools.get_balance(
        bob.eth_address) - 3*ONE_ETH


def test_alice_tries_to_cheat(eth_tools: EthTools,  alice: Node, bob: Node) -> None:
    alice_init_balance = eth_tools.get_balance(alice.eth_address)
    bob_init_balance = eth_tools.get_balance(bob.eth_address)

    # Creating channel
    chan_address = alice.establish_channel(
        bob.eth_address, bob.ip_address, 10*ONE_ETH)

    # Alice sends money thrice
    alice.send(chan_address, ONE_ETH)
    old_state = alice.get_current_channel_state(chan_address)
    alice.send(chan_address, ONE_ETH)
    alice.send(chan_address, ONE_ETH)

    # ALICE TRIES TO CHEAT
    alice.close_channel(chan_address, old_state)

    # Waiting one block
    eth_tools.mine_blocks(1)

    # Bob checks if he needs to appeal, and sends an appeal
    assert bob.appeal_closed_chan(chan_address)

    # waiting
    eth_tools.mine_blocks(APPEAL_PERIOD)

    # Bob Withdraws
    assert bob.withdraw_funds(chan_address) == 3*ONE_ETH

    # Alice Withdraws
    assert alice.withdraw_funds(chan_address) == 7*ONE_ETH

    assert alice_init_balance == eth_tools.get_balance(
        alice.eth_address) + 3*ONE_ETH
    assert bob_init_balance == eth_tools.get_balance(
        bob.eth_address) - 3*ONE_ETH


def test_channel_list_encapsulation(alice: Node, chan: Contract) -> None:
    # We check that the node does not return an internal data structure which would allow
    # the user to modify the channel state without going through the API.
    chan_list = alice.get_list_of_channels()
    assert len(chan_list) == 1
    chan_list.clear()
    chan_list = alice.get_list_of_channels()
    assert len(chan_list) == 1


# a sample communication test between nodes
def test_node_rejects_receive_message_of_unknown_channel(eth_tools: EthTools, alice: Node, bob: Node, charlie: Node,
                                                         chan: Contract) -> None:
    eth_tools.start_tx_count()
    msg = ChannelStateMessage(
        chan.address, 5*ONE_ETH, 5*ONE_ETH, 10)
    signed_msg = sign(alice.private_key, msg)
    charlie.receive_funds(signed_msg)

    assert charlie.get_list_of_channels() == []
    with pytest.raises(Exception):
        charlie.get_current_channel_state(chan.address)
    assert eth_tools.tx_count == 0

# when we do something wrong, like close the contract twice
# we should be stopped both by the node and by the contract. Here we are stopped by the contract:


def test_close_by_alice_twice(alice: Node, chan: Contract, ) -> None:
    alice.send(chan.address, ONE_ETH)
    msg = alice.get_current_channel_state(chan.address)
    alice.close_channel(chan.address)
    v, r, s = msg.sig

    with pytest.raises(RevertException):
        chan.transact(alice, "oneSidedClose", (msg.balance1, msg.balance2, msg.serial_number,
                      v, r, s))


# Here the node refuses to close the closed channel once again (no transaction should be sent!)
def test_cant_close_channel_twice(eth_tools: EthTools, alice: Node, bob: Node, chan: Contract) -> None:
    alice.send(chan.address, ONE_ETH)
    alice.close_channel(chan.address)
    eth_tools.start_tx_count()
    with pytest.raises(Exception):
        alice.close_channel(chan.address)
    with pytest.raises(Exception):
        bob.close_channel(chan.address)
    assert eth_tools.tx_count == 0


def test_node_rejects_receive_message_of_unknown_channel(eth_tools: EthTools, alice: Node, bob: Node, charlie: Node,
                                                         chan: Contract) -> None:
    eth_tools.start_tx_count()
    msg = ChannelStateMessage(
        chan.address, 5*ONE_ETH, 5*ONE_ETH, 10)
    signed_msg = sign(alice.private_key, msg)
    charlie.receive_funds(signed_msg)

    assert charlie.get_list_of_channels() == []
    with pytest.raises(Exception):
        charlie.get_current_channel_state(chan.address)
    assert eth_tools.tx_count == 0
