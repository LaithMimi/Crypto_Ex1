// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

contract RPS {
    // Mapping for user balances inside the contract
    mapping(address => uint256) public balanceOf;

    // Enum for game phases
    enum GamePhase {
        None,
        Move1,
        Move2,
        Reveal1,
        Reveal2,
        Finished,
        Cancelled
    }

    // Struct to store game details
    struct Game {
        address player1;
        address player2;
        uint256 bet;
        bytes32 commitment1;
        bytes32 commitment2;
        uint8 move1;
        uint8 move2;
        uint256 deadline; // Timestamp relevant for reveal / appeal phases
        GamePhase phase;
    }

    // Mapping to store all games by gameID
    mapping(uint256 => Game) public games;

    // Functions
    // Frontend sends plain ETH transfers, so we need receive()
    receive() external payable {
        balanceOf[msg.sender] += msg.value;
    }

    function deposit() external payable {
        balanceOf[msg.sender] += msg.value;
    }

    function withdraw(uint256 amount) external {
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        
        balanceOf[msg.sender] -= amount;
        
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Withdraw transfer failed");
    }

    function makeMove(uint256 gameID, uint256 bet, bytes32 commitment) external {
        Game storage game = games[gameID];
        
        require(balanceOf[msg.sender] >= bet, "Insufficient balance");
        require(game.phase == GamePhase.None || game.phase == GamePhase.Move1, "Invalid phase");

        if (game.phase == GamePhase.None) {
            game.player1 = msg.sender;
            game.bet = bet;
            game.commitment1 = commitment;
            game.phase = GamePhase.Move1;
            balanceOf[msg.sender] -= bet;
        } else {
            // Player 2 matches
            require(msg.sender != game.player1, "Cannot play against self");
            require(bet == game.bet, "Bet amount mismatch");
            
            game.player2 = msg.sender;
            game.commitment2 = commitment;
            game.phase = GamePhase.Move2; 
            game.deadline = block.timestamp + 1 days; // 24h timeout
            balanceOf[msg.sender] -= bet;
        }
    }

    function revealMove(uint256 gameID, uint8 move, bytes32 key) external {
        Game storage game = games[gameID];
        require(game.phase == GamePhase.Move2 || game.phase == GamePhase.Reveal1, "Invalid phase");
        
        // Verify move is valid (1=Rock, 2=Paper, 3=Scissors, 4=MagicWand?)
        require(move >= 1 && move <= 4, "Invalid move");

        if (msg.sender == game.player1) {
            require(game.move1 == 0, "Already revealed");
            require(keccak256(abi.encodePacked(move, key)) == game.commitment1, "Invalid commitment");
            game.move1 = move;
        } else if (msg.sender == game.player2) {
            require(game.move2 == 0, "Already revealed");
            require(keccak256(abi.encodePacked(move, key)) == game.commitment2, "Invalid commitment");
            game.move2 = move;
        } else {
            revert("Not a player");
        }

        // Logic flow
        if (game.phase == GamePhase.Move2) {
            game.phase = GamePhase.Reveal1;
        } else {
            // Second reveal -> Finish
            game.phase = GamePhase.Finished;
            resolveGame(gameID);
        }
    }

    function cancelGame(uint256 gameID) external {
        Game storage game = games[gameID];
        require(game.phase == GamePhase.Move1, "Cannot cancel");
        require(msg.sender == game.player1, "Not player 1");
        
        game.phase = GamePhase.Cancelled;
        balanceOf[msg.sender] += game.bet;
    }

    function revealPhaseEnded(uint256 gameID) external {
        Game storage game = games[gameID];
        require(game.phase == GamePhase.Move2 || game.phase == GamePhase.Reveal1, "Invalid phase");
        require(block.timestamp > game.deadline, "Deadline not passed");

        game.phase = GamePhase.Finished;

        if (game.move1 != 0) {
            // Player 1 revealed, Player 2 didn't -> P1 wins
            balanceOf[game.player1] += (2 * game.bet);
        } else if (game.move2 != 0) {
            // Player 2 revealed, Player 1 didn't -> P2 wins
            balanceOf[game.player2] += (2 * game.bet);
        } else {
            // Neither revealed -> Refund both
            balanceOf[game.player1] += game.bet;
            balanceOf[game.player2] += game.bet;
        }
    }

    function resolveGame(uint256 gameID) internal {
        Game storage game = games[gameID];
        uint8 m1 = game.move1;
        uint8 m2 = game.move2;
        
        // Determine winner
        // 1=Rock, 2=Paper, 3=Scissors
        // 4=MagicWand (Assume it loses to everything for safety, or beats everything? 
        // Logic: Standard RPS
        // R(1) < P(2)
        // P(2) < S(3)
        // S(3) < R(1)
        
        // If Logic for 4 is unknown, treating as simple value. 
        // Let's implement robust standard Logic.
        
        address winner = address(0);
        
        if (m1 == m2) {
            // Draw
            balanceOf[game.player1] += game.bet;
            balanceOf[game.player2] += game.bet;
            return;
        }
        
        // Win logic
        if (m1 == 1) { // Rock
            if (m2 == 3) winner = game.player1; // vs Scissors
            else if (m2 == 2) winner = game.player2; // vs Paper
            else if (m2 == 4) winner = game.player1; // Assume Rock beats MagicWand?
        } else if (m1 == 2) { // Paper
            if (m2 == 1) winner = game.player1; // vs Rock
            else if (m2 == 3) winner = game.player2; // vs Scissors
            else if (m2 == 4) winner = game.player1; // Assume Paper beats MagicWand?
        } else if (m1 == 3) { // Scissors
            if (m2 == 2) winner = game.player1; // vs Paper
            else if (m2 == 1) winner = game.player2; // vs Rock
            else if (m2 == 4) winner = game.player1; // Assume Scissors beats MagicWand?
        } else if (m1 == 4) { // MagicWand
            // Assume 4 loses to standard moves if they are smart
             winner = game.player2;
        }
        
        // If winner detected
        if (winner != address(0)) {
            balanceOf[winner] += (2 * game.bet);
        } else {
            // Fallback draw (should cover Magic Wand vs Magic Wand)
             balanceOf[game.player1] += game.bet;
             balanceOf[game.player2] += game.bet;
        }
    }

    function getGameState(uint256 gameID) external view returns (GamePhase) {
        return games[gameID].phase;
    }
}
