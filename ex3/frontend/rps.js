
// at initialization subscribe to various events, connect to the local Ethereum node, and fetch initial balances.
document.addEventListener('DOMContentLoaded', async () => {
    window.gameStatus = {
        0: "No Game",
        1: "Move 1",
        2: "Move 2",
        3: "Reveal 1",
        4: "Late"
    };

    // we might have the ABI already if the window was refreshed
    await updateABI();

    // wire up the buttons to their respective functions
    document.getElementById('deployButton').addEventListener('click', deployContract);
    document.getElementById('contract-address').addEventListener('change', contractChange);
    document.getElementById('deposit-button').addEventListener('click', depositToContract);
    document.getElementById('withdraw-button').addEventListener('click', withdrawFromContract);
    document.getElementById('game-id').addEventListener('input', updateGameStatus);
    document.getElementById('calc-move').addEventListener('input', calculateCommitment);
    document.getElementById('calc-key').addEventListener('input', calculateCommitment);
    document.getElementById('make-move-button').addEventListener('click', makeMove);
    document.getElementById('reveal-button').addEventListener('click', revealMove);
    document.getElementById('abiInput').addEventListener('change', updateABI);
    document.getElementById('mine-button').addEventListener('click', mineBlock);
    document.getElementById('cancel-button').addEventListener('click', cancelGame);
    document.getElementById('appeal-button').addEventListener('click', appealGame);

    // connect to the eth node for the first time
    window.connection = false;
    writeLogMessage('Trying to connect to Ethereum node');
    await connectToLocalEthereumNode();
    calculateCommitment();
});


async function createProvider() {
    const url = '127.0.0.1:8545';
    const timeout = 2000;

    const provider = await new Web3.providers.WebsocketProvider('ws://' + url);
    provider.on('error', error => {
        if (window.connection) {
            writeLogMessage('Error connecting to local Ethereum node. Attempting reconnect...', true);
            window.connection = false;
        }
        setTimeout(() => {
            console.log(`Retrying connection to ${url}`);
            connectToLocalEthereumNode();
        }, timeout);
    }).on('end', error => {
    }).on('connect', async () => {
        if (!window.connection) {
            window.connection = true;
            writeLogMessage(`Connected to local Ethereum node at ${url}`);
        }

        console.log('Setting base fee to 0');
        await window.lweb3.currentProvider.send({
            jsonrpc: "2.0",
            method: "hardhat_setNextBlockBaseFeePerGas",
            params: ["0x0"],
            id: 12345
        }, (error, _) => {
            if (error) {
                console.error('Error setting base fee:', error);
            }
        });

        window.accounts = await window.lweb3.eth.getAccounts();
        window.players = {
            "Alice": window.accounts[0],
            "Bob": window.accounts[1],
            "Charlie": window.accounts[2]
        };

        subscribeToBlocks();
        contractChange();
        updateEthBalances();
    });
    return provider;
}

async function connectToLocalEthereumNode() {
    if (window.lweb3 == undefined) {
        const provider = await createProvider();
        window.lweb3 = await new Web3(provider);
        console.log('Web3 object created.');
    }
    else if (!window.lweb3.currentProvider.connected) {
        const provider = await createProvider();
        await window.lweb3.setProvider(provider);
        console.log('Web3 object updated with new provider.');
    }
}



async function subscribeToBlocks() {
    // Subscribe to new block headers
    window.lweb3.eth.subscribe('newBlockHeaders', async (error, result) => {
        if (!error) {
            updateEthBalances();
            updateRPSBalances();
            updateGameStatus();
            writeLogMessage(`Block # ${result.number} was mined.`);
        } else {
            console.error('Error in block subscription');
        }
    });
    console.log('Subscribed to new blocks.');
}

async function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsText(file);
    });
}

async function updateABI() {
    const abiInput = document.getElementById('abiInput');
    if (!abiInput.files[0]) {
        window.abi = undefined;
    }
    else {
        window.abi = JSON.parse(await readFileAsText(abiInput.files[0]));
        console.log('ABI loaded');
    }
}


async function deployContract() {

    const bytecodeInput = document.getElementById('fileInput');

    if (window.abi == undefined) {
        writeLogMessage('ABI not loaded', true);
        return;
    }
    if (!bytecodeInput.files[0]) {
        writeLogMessage('Bytecode file not selected', true);
        return;
    }

    try {
        const bytecode = await readFileAsText(bytecodeInput.files[0]);

        const contract = new window.lweb3.eth.Contract(window.abi);
        const deploy = contract.deploy({
            data: "0x" + bytecode,
            arguments: [10], // TODO choose from UI
        });

        const gasEstimate = await deploy.estimateGas({
            from: window.accounts[0]
        });

        const receipt = await deploy.send({
            from: window.accounts[0], //TODO determine
            gas: gasEstimate,
            gasPrice: "0"
        });

        writeLogMessage('Contract deployed at address: ' + receipt.options.address);
        document.getElementById('contract-address').value = receipt.options.address;
        contractChange();
    } catch (error) {
        console.error('Error deploying contract:', error);
    }
}



async function calculateCommitment() {
    const move = document.getElementById('calc-move').value;
    const key = document.getElementById('calc-key').value;

    const commitment = window.lweb3.utils.soliditySha3({ type: 'int256', value: move }, { type: 'bytes32', value: key });
    document.getElementById('calc-commit').innerText = commitment;
}

async function makeMove() {
    if (!window.contract) {
        writeLogMessage('No contract loaded', true);
        return;
    }
    const commitment = document.getElementById('calc-commit').innerText;
    const betAmountEth = document.getElementById('move-amount').value;
    const betAmount = window.lweb3.utils.toWei(betAmountEth, 'ether');
    const gameID = document.getElementById('game-id').value;
    const player = document.getElementById('players').value;
    const player_account = window.players[player];

    writeLogMessage(`${player} bets ${betAmountEth} Eth in game ${gameID}, and makes a move.`);
    window.contract.methods.makeMove(gameID, betAmount, commitment).send({
        from: player_account
    }).on('receipt', (receipt) => {
        console.log(receipt);
    }).on('error', (error) => {
        writeLogMessage(`failed when making move: ${error}`, true);
        console.error(error);
    });
}

async function revealMove() {
    if (!window.contract) {
        writeLogMessage('Failed to reveal. No contract loaded.', true);
        return;
    }
    const move = document.getElementById('reveal-move').value;
    const key = "0x" + document.getElementById('reveal-key').value;
    const gameID = document.getElementById('game-id').value;
    const player = document.getElementById('players').value;
    const player_account = window.players[player];



    window.contract.methods.revealMove(gameID, move, key).send({
        from: player_account
    }).on('receipt', (receipt) => {
        writeLogMessage(`${player} reveals move ${move} in game ${gameID}.`);
    }).on('error', (error) => {
        writeLogMessage(`failed when revealing move: ${error}`, true);
    });
}

async function cancelGame() {
    const gameID = document.getElementById('game-id').value;
    const player = document.getElementById('players').value;
    const player_account = window.players[player];

    writeLogMessage(`${player} attempts to cancel game ${gameID}.`);
    window.contract.methods.cancelGame(gameID).send({
        from: player_account
    }).on('receipt', (receipt) => {
        writeLogMessage("Game cancelled")
    }).on('error', (error) => {
        writeLogMessage("Game cancellation failed", true)
    });
}

async function appealGame() {
    const gameID = document.getElementById('game-id').value;
    const player = document.getElementById('players').value;
    const player_account = window.players[player];

    writeLogMessage(`${player} attempts to appeal game ${gameID}.`);
    window.contract.methods.revealPhaseEnded(gameID).send({
        from: player_account
    }).on('receipt', (receipt) => {
        writeLogMessage("Appeal successful")
    }).on('error', (error) => {
        writeLogMessage("Appeal failed", true)
    });
}

async function withdrawFromContract() {
    if (!window.abi) {
        console.log('No ABI loaded.');
        return;
    }
    const withdrawAmount = document.getElementById('withdraw-amount').value;
    if (!withdrawAmount) {
        console.log('Please enter a valid amount of ETH.');
        return;
    }
    const weiAmount = window.lweb3.utils.toWei(withdrawAmount, 'ether');
    try {
        const requester = document.getElementById('players').value;
        const requesterAddress = window.players[requester];
        writeLogMessage(`${requester} attempts to withdraw ${withdrawAmount} Eth`)
        const result = await window.contract.methods.withdraw(weiAmount).send({
            from: requesterAddress
        });
        writeLogMessage(`${requester} withdrew ${withdrawAmount} Eth`)
    } catch (error) {
        // Try to extract the reason
        const reason = error.reason || error.message || error;
        writeLogMessage(`Error withdrawing: ${reason}`, true);
        console.error("Full withdraw error:", error);
    }
}

async function depositToContract() {
    const depositAmount = document.getElementById('deposit-amount').value;
    if (!depositAmount) { //we allow for negative deposit amounts to see if contract reverts
        writeLogMessage('Invalid deposit amount', true);
        return;
    }
    const weiAmount = window.lweb3.utils.toWei(depositAmount, 'ether');
    try {
        const sender = document.getElementById('players').value;
        const senderAddress = window.players[sender];

        const destinationAddress = document.getElementById('contract-address').value;
        writeLogMessage(`${sender} deposits ${depositAmount} Eth`)
        const result = await window.lweb3.eth.sendTransaction({
            from: senderAddress,
            to: destinationAddress,
            value: weiAmount,
            gasPrice: '0'
        });
    } catch (error) {
        writeLogMessage(`Error sending ETH.`, true);
    }
}

async function mineBlock() {
    await window.lweb3.currentProvider.send({
        jsonrpc: "2.0",
        method: "evm_mine",
        id: 12345
    }, (error, _) => {
        if (error) {
            console.error('Error mining block:', error);
        }
    });
}



async function updateGameStatus() {
    try {
        if (window.contract == undefined) {
            document.getElementById('game-state').innerText = 'No Contract Loaded'
            return;
        }
        if (document.getElementById('game-id').value == '') {
            document.getElementById('game-state').innerText = 'No Game ID Entered'
            return;
        }
        const gameId = document.getElementById('game-id').value;
        const gameStatus = await window.contract.methods.getGameState(gameId).call();
        document.getElementById('game-state').innerText = window.gameStatus[gameStatus];
        return

    }
    catch (error) {
    }
}


async function contractChange() {
    if (window.abi == undefined) {
        window.contract = undefined;
        console.log('Cannot create contract instance since no ABI loaded');
    } else {
        const address = document.getElementById('contract-address').value;
        if (!window.lweb3.utils.isAddress(address)) {
            window.contract = undefined;
            console.log('Cannot create contract instance since invalid contract address');
        } else {
            const code = await window.lweb3.eth.getCode(address);
            if (code === '0x' || code === '0x0' || code === '') {
                window.contract = undefined;
                console.log('Cannot create contract instance since no contract deployed at address');
            }
            else {
                window.contract = await new window.lweb3.eth.Contract(window.abi, address);
                window.contract.options.gasPrice = '0'; // default gas price in wei
                console.log('Contract address set:', address);
            }
        }
    }
    updateRPSBalances();
    updateGameStatus();
}

async function updateRPSBalances() {
    if (window.contract == undefined) {
        Object.keys(window.players).forEach(player => {
            document.getElementById(player + "-rps-balance").innerText = "N/A";
        });
        return;
    }
    Object.keys(window.players).forEach(async player => {
        try {
            const balance = await window.contract.methods.balanceOf(window.players[player]).call();
            const ethBalance = window.lweb3.utils.fromWei(balance, 'ether');
            document.getElementById(player + "-rps-balance").innerText = ethBalance;
        }
        catch (error) {
            console.error('Error fetching contract balance:', error);
        }
    });

    const contractBalance = await window.lweb3.eth.getBalance(window.contract.options.address);
    document.getElementById("RPS-eth-balance").innerText = window.lweb3.utils.fromWei(contractBalance, 'ether');
}





async function writeLogMessage(message, isError = false) {
    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    const logMessage = `[${currentTime}] ${message}\n`;

    const messageLog = document.getElementById("message-log");
    const messageElement = document.createElement("span");

    messageElement.innerText = logMessage;
    messageElement.style.color = isError ? 'red' : 'blue';

    messageLog.appendChild(messageElement);
    messageLog.scrollTop = messageLog.scrollHeight;
}

async function updateEthBalances() {
    try {
        // Iterate over the players object keys
        Object.keys(window.players).forEach(async key => {
            try {
                let balance = await window.lweb3.eth.getBalance(window.players[key]);
                document.getElementById(key + "-eth-balance").innerText = window.lweb3.utils.fromWei(balance, 'ether');
            } catch (balanceError) {
                console.error(`Error fetching balance for ${key} at address ${players[key]}:`, balanceError);
            }
        });

    } catch (error) {
        console.error('Error updating stats:', error);
    }
}


