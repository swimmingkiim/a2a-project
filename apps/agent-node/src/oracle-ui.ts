export const oracleHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A2A Oracle Node (a10m.work)</title>
    <!-- Ethers.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/6.7.0/ethers.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.0.6/purify.min.js"></script>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
    <style>
        :root {
            --bg-color: #0f172a;
            --text-color: #f8fafc;
            --primary: #3b82f6;
            --card-bg: #1e293b;
            --border: #334155;
            --success: #10b981;
            --danger: #ef4444;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
        }
        .container {
            max-width: 600px;
            width: 100%;
        }
        h1, h2, h3 { color: var(--text-color); }
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .btn {
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            transition: opacity 0.2s;
            width: 100%;
            margin-top: 10px;
        }
        .btn:hover { opacity: 0.9; }
        .btn:disabled { background-color: var(--border); cursor: not-allowed; }
        .input-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; font-size: 0.9em; color: #cbd5e1; }
        input[type="number"], input[type="text"], select {
            width: 100%;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid var(--border);
            background: #0f172a;
            color: white;
            box-sizing: border-box;
        }
        .status { margin-top: 15px; padding: 10px; border-radius: 4px; display: none; }
        .status.success { background-color: rgba(16, 185, 129, 0.1); color: var(--success); border: 1px solid var(--success); display: block; }
        .status.error { background-color: rgba(239, 68, 68, 0.1); color: var(--danger); border: 1px solid var(--danger); display: block; }
        .reward-badge {
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 10px;
        }
        .radio-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: #0f172a;
            padding: 10px;
            border-radius: 6px;
            border: 1px solid var(--border);
        }
        .radio-group label { margin: 0; font-weight: normal; cursor: pointer; display: flex; align-items: center; gap: 10px; }
        .loader {
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            display: none;
            margin: 0 auto;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔮 A2A Oracle Terminal</h1>
        <p style="color: #94a3b8; font-size: 0.9em;">Human evaluation node for the A2A economy. Solve the CAPTCHA and evaluate tasks to earn $DAIM.</p>
        
        <div class="card" id="wallet-section">
            <button class="btn" id="connect-btn">Connect Wallet</button>
            <p id="wallet-address" style="text-align: center; margin-top: 10px; font-family: monospace;"></p>
        </div>

        <div class="card" id="task-section" style="opacity: 0.5; pointer-events: none;">
            <div class="reward-badge">💎 Reward: 1.5 DAIM (15% Oracle Fee)</div>
            
            <div class="input-group">
                <label for="task-select">Select Pending Task</label>
                <div id="fetch-loader" class="loader"></div>
                <select id="task-select">
                    <option value="">Fetch tasks to evaluate...</option>
                </select>
                <button id="fetch-tasks-btn" class="btn" style="margin-top: 5px; background: var(--border);">🔄 Refresh Queue</button>
            </div>

            <div id="task-metadata-container" style="display: none; background: #0f172a; padding: 15px; border-radius: 6px; border: 1px solid var(--border); margin-bottom: 15px;">
                <h3 style="margin-top: 0; color: #cbd5e1; font-size: 1.1em;">Task Details</h3>
                <div id="task-metadata-content" style="font-size: 0.9em; word-break: break-all;"></div>
            </div>

            <div class="input-group">
                <label>Task Complexity Assessment</label>
                <div class="radio-group">
                    <label><input type="radio" name="complexity" value="10"> <b>0-19 Score:</b> Spam / Simple Repetition (Slash Task)</label>
                    <label><input type="radio" name="complexity" value="30"> <b>20-40 Score:</b> Basic Information Delivery</label>
                    <label><input type="radio" name="complexity" value="60" checked> <b>41-70 Score:</b> Creative Work / Problem Solving</label>
                    <label><input type="radio" name="complexity" value="90"> <b>71-100 Score:</b> High Expertise / Original Contribution</label>
                </div>
            </div>

            <div class="input-group">
                <label for="eudaimonia-score">Eudaimonia Score (Value Impact 0-100)</label>
                <input type="number" id="eudaimonia-score" value="80" min="0" max="100">
            </div>

            <!-- CAPTCHA -->
            <div style="font-size: 0.8em; color: #94a3b8; margin-bottom: 5px; text-align: center;">Click the checkbox to prove you are human.</div>
            <div class="g-recaptcha" data-sitekey="6LeUIXMsAAAAAJcjM5LoTa0dawNXK4bsfI95i20_" style="margin-bottom: 15px; display: flex; justify-content: center;"></div>

            <button class="btn" id="submit-btn" disabled>Evaluate & Finalize Task</button>
            <div id="status-msg" class="status"></div>
        </div>
    </div>

    <script>
        const QUANTUM_TASK_BUFFER_ADDR = "0x68F71c8dd0f056001dB59f34f28eDa92bb15e4B5";
        const ABI = [
            "function finalizeTask(uint256 _taskId, uint256 _assessedComplexity, uint256 _eudaimoniaScore) external",
            "function tasks(uint256) public view returns (uint256 id, address creator, uint256 deposit, uint256 complexityHash, uint256 submissionTime, uint256 assessedComplexity, uint256 eudaimoniaScore, bool exists)",
            "event TaskSubmitted(uint256 indexed taskId, address indexed creator, uint256 deposit, bool overheated, string metadataUri)"
        ];

        let pendingTaskMap = new Map();

        let signer = null;
        let provider = null;

        async function ensureBaseMainnet() {
            if (!window.ethereum) return false;
            const targetChainId = '0x2105'; // Base Mainnet 8453
            try {
                await window.ethereum.request({
                    method: 'wallet_switchEthereumChain',
                    params: [{ chainId: targetChainId }],
                });
                return true;
            } catch (switchError) {
                // This error code indicates that the chain has not been added to MetaMask.
                if (switchError.code === 4902) {
                    try {
                        await window.ethereum.request({
                            method: 'wallet_addEthereumChain',
                            params: [
                                {
                                    chainId: targetChainId,
                                    chainName: 'Base Mainnet',
                                    nativeCurrency: {
                                        name: 'Ether',
                                        symbol: 'ETH',
                                        decimals: 18
                                    },
                                    rpcUrls: ['https://mainnet.base.org'],
                                    blockExplorerUrls: ['https://basescan.org']
                                }
                            ],
                        });
                        return true;
                    } catch (addError) {
                        console.error('Error adding Base network:', addError);
                        return false;
                    }
                }
                console.error('Error switching network:', switchError);
                return false;
            }
        }

        document.getElementById('connect-btn').addEventListener('click', async () => {
            if (!window.ethereum) {
                alert("Please install MetaMask or a Web3 wallet!");
                return;
            }
            try {
                provider = new ethers.BrowserProvider(window.ethereum);
                await provider.send("eth_requestAccounts", []);
                
                // Ensure Base Mainnet
                const isCorrectNetwork = await ensureBaseMainnet();
                if (!isCorrectNetwork) {
                    alert("Please switch to the Base Mainnet to interact with the A2A Oracle.");
                    return;
                }
                
                // Re-initialize provider after potential network switch
                provider = new ethers.BrowserProvider(window.ethereum);
                signer = await provider.getSigner();
                const address = await signer.getAddress();
                
                // Mask Wallet Address (e.g., 0x1234...ABCD)
                const maskedAddress = address.substring(0, 6) + "..." + address.substring(address.length - 4);
                
                document.getElementById('connect-btn').style.display = 'none';
                document.getElementById('wallet-address').innerText = "Connected: " + maskedAddress;
                
                const taskSection = document.getElementById('task-section');
                taskSection.style.opacity = '1';
                taskSection.style.pointerEvents = 'auto';
                document.getElementById('submit-btn').disabled = false;

                // Auto-fetch tasks on connect
                await fetchPendingTasks();
            } catch (e) {
                console.error(e);
                alert("Connection failed.");
            }
        });

        async function fetchPendingTasks() {
            if (!provider) return;
            const selectEl = document.getElementById('task-select');
            const loaderEl = document.getElementById('fetch-loader');
            const statusEl = document.getElementById('status-msg');
            
            loaderEl.style.display = 'block';
            selectEl.style.display = 'none';
            selectEl.innerHTML = '<option value="">Select a task...</option>';
            statusEl.className = 'status';
            statusEl.style.display = 'block';
            statusEl.innerText = 'Syncing recent tasks from Base Mainnet...';
            
            try {
                // To find pending tasks on MVP, we scan recent TaskSubmitted events
                // We use multiple public Base RPCs as fallbacks since public nodes often rate-limit eth_getLogs
                const rpcUrls = [
                    "https://mainnet.base.org",
                    "https://base.publicnode.com",
                    "https://base.llamarpc.com",
                    "https://base-mainnet.public.blastapi.io"
                ];
                
                let events = [];
                let fetchSuccess = false;
                let contract;
                
                for (const rpc of rpcUrls) {
                    try {
                        const readProvider = new ethers.JsonRpcProvider(rpc);
                        contract = new ethers.Contract(QUANTUM_TASK_BUFFER_ADDR, ABI, readProvider);
                        const blockNumber = await readProvider.getBlockNumber();
                        
                        // Fetch last 1,000 blocks to avoid RPC timeout/block range limit errors on mainnet
                        const fromBlock = Math.max(0, blockNumber - 1000); 
                        const filter = contract.filters.TaskSubmitted();
                        events = await contract.queryFilter(filter, fromBlock, "latest");
                        
                        fetchSuccess = true;
                        console.log("Successfully fetched tasks from " + rpc);
                        break; // exit loop on success
                    } catch (err) {
                        console.warn("RPC " + rpc + " failed to fetch logs:", err.message);
                    }
                }
                
                if (!fetchSuccess) {
                    throw new Error("All public RPCs failed to fetch tasks. The network might be congested.");
                }
                
                if (events.length === 0) {
                    selectEl.innerHTML = '<option value="">No pending tasks found</option>';
                    statusEl.style.display = 'none';
                } else {
                    // Pure Web3 Approach: Randomize events and check if they still exist on-chain
                    // This avoids SPOF databases and ensures we only show valid tasks
                    statusEl.innerText = 'Filtering valid pending tasks on-chain...';
                    const shuffledEvents = events.sort(() => 0.5 - Math.random());
                    const validTasks = [];
                    
                    for (const event of shuffledEvents) {
                        try {
                            const taskId = event.args[0].toString();
                            const taskData = await contract.tasks(taskId);
                            if (taskData.exists) { // Only show tasks that haven't been finalized/slashed yet
                                validTasks.push({
                                    taskId,
                                    deposit: ethers.formatEther(event.args[2]),
                                    metadataUri: event.args[4]
                                });
                                if (validTasks.length >= 10) break;
                            }
                        } catch (err) { console.error("Error checking task ID", err); }
                    }
                    
                    if (validTasks.length === 0) {
                        selectEl.innerHTML = '<option value="">No pending tasks found</option>';
                    } else {
                        validTasks.forEach(t => {
                            pendingTaskMap.set(t.taskId, t.metadataUri);
                            const option = document.createElement('option');
                            option.value = t.taskId;
                            option.text = \`Task ID: \${t.taskId} (Deposit: \${t.deposit} DAIM)\`;
                            selectEl.appendChild(option);
                        });
                    }
                    statusEl.style.display = 'none';
                }
            } catch (e) {
                console.error("Failed to fetch tasks:", e);
                selectEl.innerHTML = '<option value="">Error fetching tasks</option>';
                statusEl.className = 'status error';
                statusEl.innerText = 'Failed to fetch tasks from blockchain.';
            } finally {
                loaderEl.style.display = 'none';
                selectEl.style.display = 'block';
            }
        }

        document.getElementById('fetch-tasks-btn').addEventListener('click', fetchPendingTasks);

        document.getElementById('task-select').addEventListener('change', async (e) => {
            const taskId = e.target.value;
            const statusEl = document.getElementById('status-msg');
            const submitBtn = document.getElementById('submit-btn');
            
            if (!taskId) {
                submitBtn.disabled = true;
                statusEl.style.display = 'none';
                return;
            }

            if (!signer) return;

            try {
                const address = await signer.getAddress();
                statusEl.className = 'status';
                statusEl.innerText = 'Acquiring task lock...';
                statusEl.style.display = 'block';

                const response = await fetch('/api/oracle/lock', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ taskId, walletAddress: address })
                });

                if (response.status === 409) {
                    const data = await response.json();
                    statusEl.className = 'status error';
                    statusEl.innerText = '🔒 ' + data.error;
                    submitBtn.disabled = true;
                } else if (response.ok) {
                    statusEl.className = 'status success';
                    statusEl.innerText = '✅ Task claimed! Fetching metadata...';
                    submitBtn.disabled = false;
                    
                    // Fetch and render JSON Metadata
                    const metadataCont = document.getElementById('task-metadata-container');
                    const metadataContent = document.getElementById('task-metadata-content');
                    metadataCont.style.display = 'block';
                    metadataContent.innerHTML = '<div class="loader" style="display:block"></div>';
                    
                    const uri = pendingTaskMap.get(taskId);
                    if (!uri) {
                         metadataContent.innerHTML = '<span style="color:var(--danger)">No metadata URI found.</span>';
                         return;
                    }
                    
                    let fetchUrl = uri;
                    if (uri.startsWith('ipfs://')) {
                         fetchUrl = uri.replace('ipfs://', 'https://ipfs.io/ipfs/');
                    }
                    
                    try {
                        let metaJson = {
                            title: "Untitled Task",
                            description: "No description provided.",
                            input_assets: [],
                            output_assets: []
                        };
                        try {
                            const metaRes = await fetch(fetchUrl);
                            if (metaRes.ok) {
                                metaJson = await metaRes.json();
                            } else {
                                console.warn("Could not fetch metadata JSON. Using fallback display.");
                                metaJson.description = "Metadata could not be loaded (Network Error or Dummy Task). Please evaluate based on context if available.";
                            }
                        } catch (fetchErr) {
                            console.warn("Fetch exception for metadata. Using fallback.", fetchErr);
                            metaJson.description = "Metadata URI unreachable. This is likely a testing dummy task.";
                        }
                        
                        // Sanitize Text
                        const title = DOMPurify.sanitize(metaJson.title || 'Untitled Task');
                        const desc = DOMPurify.sanitize(metaJson.description || 'No description provided.');
                        
                        let html = \`
                            <h4 style="margin:0 0 5px 0">\${title}</h4>
                            <p style="margin:0 0 10px 0; color:#94a3b8">\${desc}</p>
                        \`;
                        
                        // Proxy Assets
                        const renderAssets = (assets, label) => {
                            if (!assets || !assets.length) return '';
                            let assetHtml = \`<div style="margin-bottom:10px"><b>\${label}:</b><br>\`;
                            assets.forEach(asset => {
                                const cleanUrl = DOMPurify.sanitize(asset);
                                const proxyUrl = '/api/oracle/scan?url=' + encodeURIComponent(cleanUrl);
                                assetHtml += \`
                                     <div style="border:1px dashed #334155; padding:5px; margin-top:5px; border-radius:4px;">
                                        <img src="\${proxyUrl}" style="max-width:100%; max-height:300px;" alt="Task Asset" 
                                             onerror="this.onerror=null; this.outerHTML='<span style=\\'color:var(--danger)\\'>🛑 Malware Blocked or Asset Unavailable</span>'">
                                     </div>
                                \`;
                            });
                            return assetHtml + '</div>';
                        };
                        
                        html += renderAssets(metaJson.input_assets, 'Inputs');
                        html += renderAssets(metaJson.output_assets, 'Outputs');
                        
                        metadataContent.innerHTML = html;
                        statusEl.innerText += ' Metadata loaded. You have 5 minutes to evaluate.';
                        
                    } catch (e) {
                         console.error(e);
                         metadataContent.innerHTML = '<span style="color:var(--danger)">Error loading task metadata.</span>';
                    }
                } else {
                    statusEl.className = 'status error';
                    statusEl.innerText = 'Failed to lock task.';
                    submitBtn.disabled = true;
                }
            } catch (err) {
                console.error("Lock error:", err);
                statusEl.className = 'status error';
                statusEl.innerText = 'Error communicating with server lock.';
                submitBtn.disabled = true;
            }
        });

        document.getElementById('submit-btn').addEventListener('click', async () => {
            const taskId = document.getElementById('task-select').value;
            const complexity = document.querySelector('input[name="complexity"]:checked').value;
            const eudaimonia = document.getElementById('eudaimonia-score').value;
            const captchaResp = grecaptcha.getResponse();

            const statusEl = document.getElementById('status-msg');
            
            if (!taskId) {
                statusEl.className = 'status error';
                statusEl.innerText = 'Please select a pending Task ID.';
                return;
            }

            // Verify CAPTCHA
            if (!captchaResp) {
                statusEl.className = 'status error';
                statusEl.innerText = 'Please solve the CAPTCHA first to prove humanity.';
                return;
            }

            try {
                // Final safety check to ensure they are on Base Mainnet before sending TX
                const isCorrectNetwork = await ensureBaseMainnet();
                if (!isCorrectNetwork) {
                    statusEl.className = 'status error';
                    statusEl.innerText = 'Please switch to Base Mainnet to submit.';
                    return;
                }
                
                // Re-init signer after potential network switch
                provider = new ethers.BrowserProvider(window.ethereum);
                signer = await provider.getSigner();

                statusEl.className = 'status';
                statusEl.innerText = 'Processing transaction... Please confirm in wallet.';
                statusEl.style.display = 'block';

                const contract = new ethers.Contract(QUANTUM_TASK_BUFFER_ADDR, ABI, signer);
                
                // Real usage would perhaps call backend to verify captcha Server-Side first.
                // For MVP, we pass the Web3 transaction directly if Captcha is solved locally.
                const tx = await contract.finalizeTask(taskId, complexity, eudaimonia);
                
                statusEl.innerText = 'Transaction submitted! Waiting for confirmation...';
                
                const receipt = await tx.wait();
                
                const isSlashed = Number(complexity) < 20;
                const resultText = isSlashed ? "Task Slashed" : "Task Finalized";
                
                statusEl.className = 'status success';
                statusEl.innerHTML = \`✅ <b>\${resultText}!</b><br>You earned your 1.5 DAIM Oracle Fee.<br>TX Hash: <a href="https://basescan.org/tx/\${receipt.hash}" target="_blank" style="color:var(--success)">Explorer</a>\`;
                
                grecaptcha.reset();

            } catch (error) {
                console.error(error);
                statusEl.className = 'status error';
                // Extract revert reason if available
                let errorMsg = "Transaction failed!";
                if (error.reason) errorMsg += " Reason: " + error.reason;
                else if (error.message.includes("Agent not registered")) errorMsg += " Oracle needs to be registered.";
                else if (error.message.includes("Task does not exist")) errorMsg += " Target Task ID does not exist in buffer.";
                statusEl.innerText = errorMsg;
            }
        });
    </script>
</body>
</html>
`;
