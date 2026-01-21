// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

enum GameState {
    NO_GAME, //signifies that there is no game with this id (or there was and it is over)
    MOVE1, //signifies that a single move was entered
    MOVE2, //a second move was enetered
    REVEAL1, //one of the moves was revealed, and the reveal phase just started
    LATE // one of the moves was revealed, and enough blocks have been mined since so that the other player is considered late.
} // These correspond to values 0,1,2,3,4

enum Move {
    NONE,
    ROCK,
    PAPER,
    SCISSORS
} //These correspond to values 0,1,2,3

interface IRPS {
    // WARNING: Do not change this interface!!! these API functions are used to test your code.
    function getGameState(uint gameID) external view returns (GameState);
    function makeMove(uint gameID, uint betAmount, bytes32 hiddenMove) external;
    function cancelGame(uint gameID) external;
    function revealMove(uint gameID, Move move, bytes32 key) external;
    function revealPhaseEnded(uint gameID) external;
    function balanceOf(address player) external view returns (uint);
    function withdraw(uint amount) external;
}

contract RPS is IRPS {
    // This contract lets players play rock-paper-scissors.
    // its constructor receives a uint k which is the number of blocks mined before a reveal phase is over.

    // players can send the contract money to fund their bets, see their balance and withdraw it, as long as the amount is not in an active game.

    // the game mechanics: The players choose a gameID (some uint) that is not being currently used. They then each call make_move() making a bet and committing to a move.
    // in the next phase each of them reveals their committment, and once the second commit is done, the game is over. The winner gets the amount of money they agreed on.

    //TODO: add state variables and additional functions as needed.

    constructor(uint _revealPeriodLength) {
        // Constructs a new contract that allows users to play multiple rock-paper-scissors games.
        // If one of the players does not reveal the move committed to, then the _revealPeriodLength
        // is the number of blocks that a player needs to wait from the moment of revealing her move until
        // she can calim that the other player loses (for not revealing).
        // The _revealPeriodLength must be at least 1 block.
    }

    function checkCommitment(
        bytes32 commitment,
        Move move,
        bytes32 key
    ) public pure returns (bool) {
        // A utility function that can be used to check commitments. See also commit.py.
        // python code to generate the commitment is:
        //  commitment = HexBytes(Web3.solidityKeccak(['int256', 'bytes32'], [move, key]))
        return keccak256(abi.encodePacked(uint(move), key)) == commitment;
    }

    function getGameState(uint gameID) external view returns (GameState) {
        // Returns the state of the game at the current address as a GameState (see enum definition)
        return GameState.NO_GAME;
    }

    function makeMove(
        uint gameID,
        uint betAmount,
        bytes32 hiddenMove
    ) external {
        // The first call to this function starts the game. The second call finishes the commit phase.
        // The amount is the amount of money (in wei) that a user is willing to bet.
        // The amount provided in the call by the second player is ignored, but the user must have an amount matching that of the game to bet.
        // amounts that are wagered are locked for the duration of the game.
        // A player should not be allowed to enter a commitment twice.
        // If two moves have already been entered, then this call reverts.
    }

    function cancelGame(uint gameID) external {
        // This function allows a player to cancel the game, but only if the other player did not yet commit to his move.
        // a canceled game returns the funds to the player. Only the player that made the first move can call this function, and it will run only if
        // no other commitment for a move was entered. This function reverts in any other case.
    }

    function revealMove(uint gameID, Move move, bytes32 key) external {
        // reveals the move of a player (which is checked against his commitment using the key)
        // The first call can be made only after two moves are entered.
        // it will begin the reveal phase that ends in k blocks.
        // the second successful call ends the game and awards the money to the winner.
        // each player is allowed to reveal only once and only the two players that entered moves may reveal.
        // this function reverts on any other case and in any case of failure to properly reveal.
    }

    function revealPhaseEnded(uint gameID) external {
        // If no second reveal is made, and the reveal period ends, the player that did reveal can claim all funds wagered in this game.
        // The game then ends, and the game id is released (and can be reused in another game).
        // this function can only be called by the first revealer. If the reveal phase is not over, this function reverts.
    }

    ////////// Handling money ////////////////////

    function balanceOf(address player) external view returns (uint) {
        // returns the balance of the given player. Funds that are wagered in games that did not complete yet are not counted as part of the balance.
        // make sure the access level of this function is "view" as it does not change the state of the contract.
        return 0;
    }

    function withdraw(uint amount) external {
        // Withdraws amount from the account of the sender
        // (available funds are those that were deposited or won but not currently staked in a game).
    }

    receive() external payable {
        // adds eth to the account of the message sender.
    }
}
