// DOM Elements
const btnUserMode = document.getElementById('btn-user-mode');
const btnAnalystMode = document.getElementById('btn-analyst-mode');
const viewUserMode = document.getElementById('view-user-mode');
const viewAnalystMode = document.getElementById('view-analyst-mode');

const personaSelect = document.getElementById('persona-select');
const jsonViewer = document.getElementById('json-viewer');
const profilerCache = document.getElementById('profiler-cache');
const orchestratorThoughts = document.getElementById('orchestrator-thoughts');

const userChatHistory = document.getElementById('user-chat-history');
const userChatInput = document.getElementById('user-chat-input');
const userChatSend = document.getElementById('user-chat-send');

const analystChatHistory = document.getElementById('analyst-chat-history');
const analystChatInput = document.getElementById('analyst-chat-input');
const analystChatSend = document.getElementById('analyst-chat-send');

// Orchestrator Backend API URL (Relative to current domain)
const ORCHESTRATOR_URL = "";

// --- Mode Toggling ---
btnUserMode.addEventListener('click', () => {
    btnUserMode.classList.add('active');
    btnAnalystMode.classList.remove('active');
    viewUserMode.classList.replace('view-hidden', 'view-active');
    viewAnalystMode.classList.replace('view-active', 'view-hidden');
});

btnAnalystMode.addEventListener('click', () => {
    btnAnalystMode.classList.add('active');
    btnUserMode.classList.remove('active');
    viewAnalystMode.classList.replace('view-hidden', 'view-active');
    viewUserMode.classList.replace('view-active', 'view-hidden');
});

// --- Persona Selection (Hydrate JSON Data) ---
personaSelect.addEventListener('change', async (e) => {
    const userId = e.target.value;
    userChatInput.disabled = false;
    userChatSend.disabled = false;
    
    // Reset Chat
    userChatHistory.innerHTML = `<div class="message system-msg">Switched to Persona: ${userId}.</div>`;
    orchestratorThoughts.innerHTML = `<span class="placeholder-text">Awaiting input...</span>`;

    try {
        // Fetch live cloud memory from the Orchestrator's new endpoint
        const response = await fetch(`${ORCHESTRATOR_URL}/user-data/${userId}`);
        if (!response.ok) throw new Error("Could not load data.");
        const data = await response.json();
        
        // Display Raw Data
        jsonViewer.textContent = JSON.stringify(data, null, 2);
        
        // Display Profiler Memory Cache
        const cache = data.latest_ai_models_access_summary;
        if (cache) {
            profilerCache.innerHTML = `<strong>Cached Profile:</strong><br>${cache}`;
        } else {
            profilerCache.innerHTML = `<span class="placeholder-text">No previous session cache found.</span>`;
        }
    } catch (err) {
        jsonViewer.textContent = "// Error loading live cloud data. " + err.message;
        profilerCache.innerHTML = `<span class="placeholder-text">Error fetching data.</span>`;
    }
});

// --- User Mode Chat Logic ---
function addMessage(targetHistory, text, senderClass) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${senderClass}`;
    msgDiv.textContent = text;
    targetHistory.appendChild(msgDiv);
    targetHistory.scrollTop = targetHistory.scrollHeight;
}

userChatSend.addEventListener('click', async () => {
    const message = userChatInput.value.trim();
    const userId = personaSelect.value;
    if (!message || !userId) return;

    // 1. Add User Msg
    addMessage(userChatHistory, message, 'user-msg');
    userChatInput.value = '';

    // 2. Mock Orchestrator Thoughts Animation
    orchestratorThoughts.innerHTML = `<em>Intercepting message...</em><br>Calling Profiler Memory Engine...`;

    // 3. Call Live Orchestrator Backend
    try {
        const payload = { user_id: userId, message: message };
        
        // Timeout to simulate "Thinking" in the UI visually
        setTimeout(async () => {
            try {
                // To actually hit the backend, CORS must be enabled on the FastAPI server.
                // If it fails, we fall back to a visual mock simulation.
                const res = await fetch(`${ORCHESTRATOR_URL}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
                orchestratorThoughts.innerHTML = `<strong>Memory Retrieved:</strong> ${data.user_context_used}<br><br><strong>ADK Intent Detection:</strong> Routing to -> ${data.routed_to}`;
                addMessage(userChatHistory, data.final_answer, 'agent-msg');

            } catch (backendErr) {
                // Fallback for Demo Purposes if Backend isn't reachable
                orchestratorThoughts.innerHTML = `<strong>Memory Retrieved:</strong> [MOCK] High Debt Detected.<br><br><strong>ADK Intent Detection:</strong> Routing to -> Wealth Advisor`;
                addMessage(userChatHistory, `[MOCK AGENT]: Given your current debt load, I cannot recommend investing in stocks.`, 'agent-msg');
            }
        }, 800);
        
    } catch (err) {
        addMessage(userChatHistory, "Error: Could not reach the Mesh.", 'system-msg');
    }
});

userChatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') userChatSend.click();
});

// --- Analyst Mode Logic ---
analystChatSend.addEventListener('click', () => {
    const message = analystChatInput.value.trim();
    if (!message) return;

    addMessage(analystChatHistory, message, 'user-msg');
    analystChatInput.value = '';

    // Simulate reading the global_trends.json
    setTimeout(() => {
        addMessage(analystChatHistory, "Reading global_trends.json... Based on recent aggregated sessions across all pods, the most prominent topics are 'Tesla Options' (40%) and 'Debt Consolidation' (35%).", 'agent-msg');
    }, 1000);
});

analystChatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') analystChatSend.click();
});
