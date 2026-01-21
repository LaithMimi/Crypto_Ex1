//SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// The interface of a channel contract that will be used to test your code. Do not modify this file.

interface ChannelI {
    function oneSidedClose(
        uint _balance1,
        uint _balance2,
        uint serialNum,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external;
    //Closes the channel based on a message by one party.
    //If the serial number is 0, then the provided balance and signatures are ignored, and the channel is closed according to the initial split, giving all the money to party 1.
    //Closing the channel starts the appeal period.
    // If any of the parameters are bad (signature,balance) the transaction reverts.
    // Additionally, the transactions would revert if the party closing the channel isn't one of the two participants.
    // _balance1 is the balance that belongs to the user that opened the channel. _balance2 is for the other user.

    function appealClosure(
        uint _balance1,
        uint _balance2,
        uint serialNum,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external;
    // appeals a one_sided_close. should show a signed message with a higher serial number.
    // _balance1 belongs to the creator of the contract. _balance2 is the money going to the other user.
    // this function reverts upon any problem:
    // It can only be called during the appeal period.
    // only one of the parties participating in the channel can appeal.
    // the serial number, balance, and signature must all be provided correctly.

    function withdrawFunds(address payable destAddress) external;
    //Sends all of the money belonging to msg.sender to the destination address provided.
    //this should only be possible if the channel is closed, and appeals are over.
    // This transaction should revert upon any error.

    function getBalance() external view returns (uint);
    // returns the balance of the caller (the funds that this person can withdraw) if he is one of the channel participants.
    // This function should revert if the channel is still open, or if the appeal period has not yet ended.
}
