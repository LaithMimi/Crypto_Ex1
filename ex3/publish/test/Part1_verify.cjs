const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Part 1: Reentrancy Attack", function () {
    let Wallet, WalletAttack;
    let wallet, attack;
    let owner, user1, user2, user3;

    beforeEach(async function () {
        [owner, user1, user2, user3] = await ethers.getSigners();

        // Deploy Vulnerable Wallet
        const WalletFactory = await ethers.getContractFactory("Wallet");
        wallet = await WalletFactory.deploy();

        // Fund the wallet with 4 ETH (simulating other users)
        await wallet.connect(user1).deposit({ value: ethers.parseEther("1.0") });
        await wallet.connect(user2).deposit({ value: ethers.parseEther("1.0") });
        await wallet.connect(user3).deposit({ value: ethers.parseEther("2.0") });

        expect(await ethers.provider.getBalance(wallet.target)).to.equal(ethers.parseEther("4.0"));

        // Deploy Attacker
        const AttackFactory = await ethers.getContractFactory("WalletAttack");
        attack = await AttackFactory.deploy();
    });

    it("Should steal at least 3 ETH", async function () {
        const initialAttackerBalance = await ethers.provider.getBalance(owner.address);

        // Run Exploit with 1 ETH
        // We pass the wallet address to exploit
        const tx = await attack.connect(owner).exploit(wallet.target, { value: ethers.parseEther("1.0") });
        const receipt = await tx.wait();

        // Calculate gas used to check net profit accurately (optional, but good for sanity)
        // For this test, simpler to check if we ended up with MORE money than started (minus gas).
        // Or check if the wallet is drained.

        const finalWalletBalance = await ethers.provider.getBalance(wallet.target);
        const finalAttackerBalance = await ethers.provider.getBalance(owner.address);

        console.log("Wallet Balance Left:", ethers.formatEther(finalWalletBalance));

        // Requirement: withdraw at least 3 ETH.
        // Initial wallet balance: 4 ETH.
        // Attacker sent 1 ETH. Total in wallet was 5 ETH.
        // If we steal 3+ ETH (plus our 1 ETH back), wallet should have < 2 ETH.

        // In a perfect drain:
        // 1. Attack deposit 1 (Total 5)
        // 2. Withdraw 1 -> Receive -> Withdraw 1 -> Receive -> Withdraw 1 -> Receive...
        // The balance updates happen after the calls return.
        // So we can drain it all potentially depending on logic.
        // Vulnerable logic: userBalances[msg.sender] = 0 happens AFTER call.
        // So as long as we recurse, `userBalances[attacker]` is still 1 ETH.

        expect(finalWalletBalance).to.be.lessThan(ethers.parseEther("1.0")); // Should have drained most of it
    });
});
