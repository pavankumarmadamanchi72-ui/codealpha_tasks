// State management
let faqData = {};

// DOM Elements
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatMessages = document.getElementById('chat-messages-container');
const typingIndicator = document.getElementById('typing-indicator');
const faqExplorer = document.getElementById('faq-explorer-container');
const faqSearch = document.getElementById('faq-search');
const clearChatBtn = document.getElementById('clear-chat-btn');

// Initialize FAQ Explorer and Chat events
document.addEventListener('DOMContentLoaded', () => {
    fetchFAQs();
    
    chatForm.addEventListener('submit', handleChatSubmit);
    faqSearch.addEventListener('input', handleFAQSearch);
    clearChatBtn.addEventListener('click', clearChat);
});

// Fetch all FAQs from API
async function fetchFAQs() {
    try {
        const response = await fetch('/api/faqs');
        if (!response.ok) throw new Error('Failed to fetch FAQs');
        faqData = await response.json();
        renderFAQExplorer(faqData);
    } catch (error) {
        console.error('Error fetching FAQs:', error);
        faqExplorer.innerHTML = '<div class="loading-spinner">Failed to load FAQs. Please refresh.</div>';
    }
}

// Render the FAQ categories in the sidebar
function renderFAQExplorer(data) {
    faqExplorer.innerHTML = '';
    
    const categories = Object.keys(data);
    if (categories.length === 0) {
        faqExplorer.innerHTML = '<div class="loading-spinner">No FAQs available.</div>';
        return;
    }
    
    categories.forEach(category => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'faq-category';
        
        const title = document.createElement('div');
        title.className = 'faq-category-title';
        title.textContent = category;
        categoryDiv.appendChild(title);
        
        const list = document.createElement('ul');
        list.className = 'faq-list';
        
        data[category].forEach(faq => {
            const item = document.createElement('li');
            item.className = 'faq-item';
            item.textContent = faq.question;
            item.title = faq.question;
            item.addEventListener('click', () => sendSuggestion(faq.question));
            list.appendChild(item);
        });
        
        categoryDiv.appendChild(list);
        faqExplorer.appendChild(categoryDiv);
    });
}

// Filter FAQs based on search input
function handleFAQSearch(e) {
    const query = e.target.value.toLowerCase().trim();
    
    if (!query) {
        renderFAQExplorer(faqData);
        return;
    }
    
    const filteredData = {};
    
    Object.keys(faqData).forEach(category => {
        const matchedFaqs = faqData[category].filter(faq => 
            faq.question.toLowerCase().includes(query) || 
            category.toLowerCase().includes(query)
        );
        
        if (matchedFaqs.length > 0) {
            filteredData[category] = matchedFaqs;
        }
    });
    
    renderFAQExplorer(filteredData);
}

// Handle message submission
async function handleChatSubmit(e) {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;
    
    // Add user message to UI
    appendMessage(text, 'user');
    userInput.value = '';
    
    // Show typing state
    showTyping(true);
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        
        if (!response.ok) throw new Error('API Error');
        const data = await response.json();
        
        // Hide typing state and append bot response
        showTyping(false);
        
        if (data.status === 'success') {
            appendBotResponse(data);
        } else {
            appendMessage("Something went wrong. Please try again.", 'bot');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        showTyping(false);
        appendMessage("Sorry, I am having trouble connecting right now.", 'bot');
    }
}

// Quick reply clicked
function sendSuggestion(questionText) {
    appendMessage(questionText, 'user');
    showTyping(true);
    
    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: questionText })
    })
    .then(res => res.json())
    .then(data => {
        showTyping(false);
        if (data.status === 'success') {
            appendBotResponse(data);
        }
    })
    .catch(err => {
        console.error('Error:', err);
        showTyping(false);
        appendMessage("Sorry, I am having trouble connecting right now.", 'bot');
    });
}

// Append plain message
function appendMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = sender === 'user' ? 'U' : '✦';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    // Use paragraph rendering for simple text
    const p = document.createElement('p');
    p.textContent = text;
    bubble.appendChild(p);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    
    scrollToBottom();
}

// Append structured bot response (supports markdown-like styling & chips)
function appendBotResponse(data) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = '✦';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    // Render content
    const formattedHTML = formatMarkdown(data.answer);
    bubble.innerHTML = formattedHTML;
    
    // Add confidence score if matched
    if (data.match && data.score) {
        const scoreSpan = document.createElement('span');
        scoreSpan.className = 'match-score';
        scoreSpan.textContent = `Match Confidence: ${(data.score * 100).toFixed(0)}%`;
        bubble.appendChild(scoreSpan);
    }
    
    // Add quick action suggestion chips if present
    if (data.suggestions && data.suggestions.length > 0) {
        const chipContainer = document.createElement('div');
        chipContainer.className = 'suggestion-chips';
        
        data.suggestions.forEach(suggestion => {
            const btn = document.createElement('button');
            btn.className = 'chip';
            btn.textContent = suggestion;
            btn.addEventListener('click', () => sendSuggestion(suggestion));
            chipContainer.appendChild(btn);
        });
        
        bubble.appendChild(chipContainer);
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    
    scrollToBottom();
}

// Convert markdown style format into HTML structured layout
function formatMarkdown(text) {
    // Clean escape characters
    let escaped = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    
    // Bold tags (**bold**)
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Italic tags (*italic*)
    escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    const lines = escaped.split('\n');
    let htmlResult = [];
    let inList = false;
    let listType = null; // 'ol' or 'ul'
    
    for (let line of lines) {
        const trimmed = line.trim();
        
        // Match numbers like "1. Item"
        const olMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
        // Match bullets like "- Item"
        const ulMatch = trimmed.match(/^([-\*])\s+(.*)$/);
        
        if (olMatch) {
            if (!inList || listType !== 'ol') {
                if (inList) htmlResult.push(`</${listType}>`);
                htmlResult.push('<ol>');
                inList = true;
                listType = 'ol';
            }
            htmlResult.push(`<li>${olMatch[2]}</li>`);
        } else if (ulMatch) {
            if (!inList || listType !== 'ul') {
                if (inList) htmlResult.push(`</${listType}>`);
                htmlResult.push('<ul>');
                inList = true;
                listType = 'ul';
            }
            htmlResult.push(`<li>${ulMatch[2]}</li>`);
        } else {
            if (inList) {
                htmlResult.push(`</${listType}>`);
                inList = false;
                listType = null;
            }
            if (trimmed.length > 0) {
                // If it starts with ** and ends with **, it could be a heading, else regular paragraph
                if (trimmed.startsWith('<strong>') && trimmed.endsWith('</strong>')) {
                    htmlResult.push(`<p class="bubble-subheading">${trimmed}</p>`);
                } else {
                    htmlResult.push(`<p>${line}</p>`);
                }
            }
        }
    }
    
    if (inList) {
        htmlResult.push(`</${listType}>`);
    }
    
    return htmlResult.join('');
}

// Show/Hide typing state
function showTyping(show) {
    if (show) {
        typingIndicator.style.display = 'flex';
        // Move indicator to the end of the message area
        chatMessages.appendChild(typingIndicator);
    } else {
        typingIndicator.style.display = 'none';
    }
    scrollToBottom();
}

// Scroll to chat bottom
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Clear Chat conversation
function clearChat() {
    chatMessages.innerHTML = `
        <div class="message bot-message">
            <div class="avatar">✦</div>
            <div class="message-bubble">
                <p>Hi there! I am Aura's Smart Assistant. Ask me anything about setting up, securing, or troubleshooting your Aura Smart Home Hub.</p>
                <p>Here are some popular topics to get you started:</p>
                <div class="suggestion-chips">
                    <button class="chip" onclick="sendSuggestion('How do I set up my Aura Smart Home Hub for the first time?')">First-time Setup</button>
                    <button class="chip" onclick="sendSuggestion('Does Aura support Apple HomeKit?')">Apple HomeKit Support</button>
                    <button class="chip" onclick="sendSuggestion('Is there a monthly subscription fee?')">Subscriptions & Fees</button>
                </div>
            </div>
        </div>
    `;
    scrollToBottom();
}
