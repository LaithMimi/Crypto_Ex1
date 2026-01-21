//// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract Greeter {
    string public greeting;

    constructor(string memory _greeting) {
        greeting = _greeting;
    }

    function setGreeting(string memory _greeting) public {
        greeting = _greeting;
    }

    function greet() public view returns (string memory) {
        return greeting;
    }

    receive() external payable {} // this contract can accept money

    function withdraw() external payable {
        //this function can receive money
        payable(msg.sender).transfer(address(this).balance); //send all our money to the caller
    }
}
