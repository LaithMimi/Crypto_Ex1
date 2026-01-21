const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("RPS Contract Verification", function () {
    let RPS;
    let rps;
    let owner, player1, player2, player3;

    beforeEach(async function () {
        [owner, player1, player2, player3] = await ethers.getSigners();
        const RPSFactory = await ethers.getContractFactory("RPS");
        rps = await RPSFactory.deploy(); // Deploy without arguments if constructor is empty or generic
        // RPS.sol doesn't show a constructor in the view_file output earlier.
    });

    // Helper to calculate commitment
    function createCommitment(move, key) {
        // move is integer, key is bytes32
        // Solidity: keccak256(abi.encodePacked(move, key))
        // We can use ethers.solidityPackedKeccak256
        return ethers.solidityPackedKeccak256(["uint8", "bytes32"], [move, key]);
    }

    const SALT1 = ethers.encodeBytes32String("salt1");
    const SALT2 = ethers.encodeBytes32String("salt2");
    const BET = ethers.parseEther("1.0");

    describe("Deposits and Withdrawals", function () {
        it("Should allow deposits", async function () {
            await rps.connect(player1).deposit({ value: BET });
            expect(await rps.balanceOf(player1.address)).to.equal(BET);
        });

        it("Should allow withdrawals", async function () {
            await rps.connect(player1).deposit({ value: BET });
            await rps.connect(player1).withdraw(BET);
            expect(await rps.balanceOf(player1.address)).to.equal(0);
        });

        it("Should fail withdrawal if insufficient balance", async function () {
            await expect(
                rps.connect(player1).withdraw(BET)
            ).to.be.revertedWith("Insufficient balance");
        });
    });

    describe("Game Flow - Normal Play", function () {
        it("Should allow Player 1 to make a move", async function () {
            await rps.connect(player1).deposit({ value: BET });

            const commit = createCommitment(1, SALT1); // Rock
            await rps.connect(player1).makeMove(1, BET, commit);

            const game = await rps.games(1);
            expect(game.player1).to.equal(player1.address);
            expect(game.bet).to.equal(BET);
            expect(game.phase).to.equal(1); // Move1
            expect(await rps.balanceOf(player1.address)).to.equal(0); // Bet deducted
        });

        it("Should allow Player 2 to join", async function () {
            // P1 setup
            await rps.connect(player1).deposit({ value: BET });
            const commit1 = createCommitment(1, SALT1);
            await rps.connect(player1).makeMove(1, BET, commit1);

            // P2 join
            await rps.connect(player2).deposit({ value: BET });
            const commit2 = createCommitment(2, SALT2); // Paper
            await rps.connect(player2).makeMove(1, BET, commit2); // GameID 1

            const game = await rps.games(1);
            expect(game.player2).to.equal(player2.address);
            expect(game.phase).to.equal(2); // Move2
            expect(await rps.balanceOf(player2.address)).to.equal(0);
        });

        it("Should resolve game correctly (Paper beats Rock)", async function () {
            // Setup Game
            await rps.connect(player1).deposit({ value: BET });
            await rps.connect(player2).deposit({ value: BET });

            const commit1 = createCommitment(1, SALT1); // Rock
            const commit2 = createCommitment(2, SALT2); // Paper (beats Rock)

            await rps.connect(player1).makeMove(1, BET, commit1);
            await rps.connect(player2).makeMove(1, BET, commit2);

            // P1 reveals
            await rps.connect(player1).revealMove(1, 1, SALT1);

            let game = await rps.games(1);
            expect(game.phase).to.equal(3); // Reveal1 (one declared)

            // P2 reveals
            await rps.connect(player2).revealMove(1, 2, SALT2);

            game = await rps.games(1);
            expect(game.phase).to.equal(5); // Finished

            // Check balances
            // P2 should have 2 * BET (plus any initial if not fully withdrawn, checking newly added)
            // Actually balances are internal. P2 wins, so P2 balance += 2*BET.
            // P1 balance should be 0 (Move cost) + (0 win) = 0.
            expect(await rps.balanceOf(player2.address)).to.equal(BET * 2n);
            expect(await rps.balanceOf(player1.address)).to.equal(0);
        });

        it("Should resolve game correctly (Draw)", async function () {
            await rps.connect(player1).deposit({ value: BET });
            await rps.connect(player2).deposit({ value: BET });

            const commit1 = createCommitment(1, SALT1); // Rock
            const commit2 = createCommitment(1, SALT2); // Rock

            await rps.connect(player1).makeMove(2, BET, commit1);
            await rps.connect(player2).makeMove(2, BET, commit2);

            await rps.connect(player1).revealMove(2, 1, SALT1);
            await rps.connect(player2).revealMove(2, 1, SALT2);

            // Each gets back BET
            expect(await rps.balanceOf(player1.address)).to.equal(BET);
            expect(await rps.balanceOf(player2.address)).to.equal(BET);
        });
    });

    describe("Cancellations and Timeouts", function () {
        it("Should allow cancellation by P1 if P2 hasn't joined", async function () {
            await rps.connect(player1).deposit({ value: BET });
            const commit1 = createCommitment(1, SALT1);
            await rps.connect(player1).makeMove(3, BET, commit1);

            await rps.connect(player1).cancelGame(3);
            const game = await rps.games(3);
            expect(game.phase).to.equal(6); // Cancelled (assuming enum order)
            expect(await rps.balanceOf(player1.address)).to.equal(BET); // Refunded
        });

        it("Should NOT allow cancellation if P2 joined", async function () {
            await rps.connect(player1).deposit({ value: BET });
            await rps.connect(player2).deposit({ value: BET });
            const commit1 = createCommitment(1, SALT1);
            const commit2 = createCommitment(1, SALT2);

            await rps.connect(player1).makeMove(4, BET, commit1);
            await rps.connect(player2).makeMove(4, BET, commit2);

            await expect(rps.connect(player1).cancelGame(4)).to.be.revertedWith("Cannot cancel");
        });

        it("Should allow timeout claim if opponent doesn't reveal", async function () {
            // P1 joins, P2 joins
            await rps.connect(player1).deposit({ value: BET });
            await rps.connect(player2).deposit({ value: BET });
            const commit1 = createCommitment(1, SALT1);
            const commit2 = createCommitment(1, SALT2);

            await rps.connect(player1).makeMove(5, BET, commit1);
            await rps.connect(player2).makeMove(5, BET, commit2);

            // P1 reveals
            await rps.connect(player1).revealMove(5, 1, SALT1);

            // Time travel
            await ethers.provider.send("evm_increaseTime", [86401]); // +1 day + 1 second
            await ethers.provider.send("evm_mine");

            // P1 claims timeout
            await rps.connect(player1).revealPhaseEnded(5);

            // P1 wins everything (2 * BET)
            expect(await rps.balanceOf(player1.address)).to.equal(BET * 2n);
        });
    });

    describe("Frontend Compatibility Check", function () {
        it("Should FAIL if commitment is generated as int256 (Frontend Bug Reproduction)", async function () {
            await rps.connect(player1).deposit({ value: BET });

            // Emulate frontend incorrect packing (int256 instead of uint8)
            const move = 1;
            const key = SALT1;
            // int256 in solidityPackedKeccak256 corresponds to 32 bytes
            const badCommitment = ethers.solidityPackedKeccak256(["int256", "bytes32"], [move, key]);

            await rps.connect(player1).makeMove(99, BET, badCommitment);

            // P2 must join to advance phase to Move2
            const commit2 = createCommitment(2, SALT2);
            await rps.connect(player2).deposit({ value: BET });
            await rps.connect(player2).makeMove(99, BET, commit2);

            // This should fail because contract reconstructs hash with uint8 (1 byte)
            await expect(
                rps.connect(player1).revealMove(99, move, key)
            ).to.be.revertedWith("Invalid commitment");
        });
    });
});

