// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface WalletI {
    // This is the interface of the wallet to be attacked.
    function deposit() external payable;
    function sendTo(address payable dest) external;
}

contract WalletAttack {
    // A contract used to attack the Vulnerable Wallet.

    constructor() {
        // The constructor for the attacking contract.
        // Do not change the signature
    }

    function exploit(WalletI _target) public payable {
        // runs the exploit on the target wallet.
        // you should not deposit more than 1 Ether to the vulnerable wallet.
        // Assuming the target wallet has more than 3 Ether in deposits,
        // you should withdraw at least 3 Ether from the wallet.
        // The money taken should be sent back to the caller of this function)
    }

    // you may add addtional functions and state variables as needed.
}
