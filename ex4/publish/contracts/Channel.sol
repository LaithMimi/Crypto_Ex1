//SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./ChannelInterface.sol";

contract Channel is ChannelI {
    // This contract will be deployed every time we establish a new payment channel between two participant.
    // The creator of the channel also injects funds that can be sent (and later possibly sent back) in this channel

    address public party1; // The creator
    address public party2; // The other party
    uint public appealPeriod;

    bool public closed;
    uint public closingBlock;
    
    // State agreed upon closure
    uint public closingBalance1;
    uint public closingBalance2;
    uint public closingSerial;

    // Track withdrawals
    mapping(address => bool) public withdrawn;

    function _verifySig(
        // Do not change this function!
        address contract_address,
        uint _balance1,
        uint _balance2,
        uint serialNum, //<--- the message
        uint8 v,
        bytes32 r,
        bytes32 s, // <---- The signature
        address signerPubKey
    ) public pure returns (bool) {
        // v,r,s together make up the signature.
        // signerPubKey is the public key of the signer
        // contract_address, _balance1, _balance2, and serialNum constitute the message to be signed.
        // returns True if the sig checks out. False otherwise.

        // the message is made shorter:
        bytes32 hashMessage = keccak256(
            abi.encodePacked(contract_address, _balance1, _balance2, serialNum)
        );

        //message signatures are prefixed in ethereum.
        bytes32 messageDigest = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", hashMessage)
        );
        //If the signature is valid, ecrecover ought to return the signer's pubkey:
        return ecrecover(messageDigest, v, r, s) == signerPubKey;
    }

    constructor(address payable _otherOwner, uint _appealPeriodLen) payable {
        require(msg.value > 0, "Initial deposit must be > 0");
        party1 = msg.sender;
        party2 = _otherOwner;
        appealPeriod = _appealPeriodLen;
    }

    // IMPLEMENT ADDITIONAL FUNCTIONS HERE
    // See function definitions in the interface ChannelI.
    // Make sure to implement all of the functions from the interface ChannelI.
    // Define your own state variables, and any additional functions you may need in addition to that...

    function oneSidedClose(
        uint _balance1,
        uint _balance2,
        uint serialNum,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external override {
        require(!closed, "Channel already closed");
        require(msg.sender == party1 || msg.sender == party2, "Not a participant");
        
        // Initial split close (serialNum == 0)
        // logic: "If the serial number is 0, then the provided balance and signatures are ignored, 
        // and the channel is closed according to the initial split, giving all the money to party 1."
        if (serialNum == 0) {
            closingBalance1 = address(this).balance; // Total funds
            closingBalance2 = 0;
            closingSerial = 0;
        } else {
            // Verify signature from the OTHER party
            require(_balance1 + _balance2 == address(this).balance, "Balances do not match total funds");
            address signer;
            if (msg.sender == party1) {
                signer = party2;
            } else {
                signer = party1;
            }
            require(_verifySig(address(this), _balance1, _balance2, serialNum, v, r, s, signer), "Invalid signature");

            closingBalance1 = _balance1;
            closingBalance2 = _balance2;
            closingSerial = serialNum;
        }

        closed = true;
        closingBlock = block.number;
    }

    function appealClosure(
        uint _balance1,
        uint _balance2,
        uint serialNum,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external override {
        require(closed, "Channel not closed");
        require(block.number <= closingBlock + appealPeriod, "Appeal period ended");
        require(serialNum > closingSerial, "New serial must be higher");
        require(msg.sender == party1 || msg.sender == party2, "Not a participant");
        require(_balance1 + _balance2 == address(this).balance, "Balances do not match total funds");

        // The appeal must provide a state signed by the OTHER party (relative to the appealer? 
        // Or essentially, since the channel is already closed with a state, we usually accept a state 
        // signed by BOTH or by the party that is NOT the one presenting it? 
        // Actually, usually the one appealing is the 'victim', so they present a state signed by the 'cheater' (who closed it).
        // BUT, in payment channels, you hold state signed by the OTHER party. 
        // So if I am Party1, I hold a state signed by Party2.
        // If Party1 appeals, they show a state signed by Party2.
        
        address signer;
        if (msg.sender == party1) {
            signer = party2;
        } else {
            signer = party1;
        }

        require(_verifySig(address(this), _balance1, _balance2, serialNum, v, r, s, signer), "Invalid signature");

        closingBalance1 = _balance1;
        closingBalance2 = _balance2;
        closingSerial = serialNum;
    }

    function withdrawFunds(address payable destAddress) external override {
        require(closed, "Channel not closed");
        require(block.number > closingBlock + appealPeriod, "Appeal period not ended");
        require(!withdrawn[msg.sender], "Already withdrawn");
        require(msg.sender == party1 || msg.sender == party2, "Not a participant");

        withdrawn[msg.sender] = true;
        uint amount = 0;
        if (msg.sender == party1) {
            amount = closingBalance1;
        } else {
            amount = closingBalance2;
        }

        if (amount > 0) {
            (bool success, ) = destAddress.call{value: amount}("");
            require(success, "Transfer failed");
        }
    }

    function getBalance() external view override returns (uint) {
        require(closed && block.number > closingBlock + appealPeriod, "Funds locked");
        if (msg.sender == party1) return closingBalance1;
        if (msg.sender == party2) return closingBalance2;
        return 0;
    }
}

