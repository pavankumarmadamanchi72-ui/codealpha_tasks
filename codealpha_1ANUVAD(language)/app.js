// Supported Languages
const languages = {
    // Global Languages
    "en": "English",
    "es": "Spanish (Español)",
    "fr": "French (Français)",
    "de": "German (Deutsch)",
    "it": "Italian (Italiano)",
    "pt": "Portuguese (Português)",
    "ru": "Russian (Русский)",
    "zh-CN": "Chinese (中文 - 简体)",
    "ja": "Japanese (日本語)",
    "ko": "Korean (한국어)",
    "ar": "Arabic (العربية)",
    "tr": "Turkish (Türkçe)",
    "nl": "Dutch (Nederlands)",
    "pl": "Polish (Polski)",
    "vi": "Vietnamese (Tiếng Việt)",
    
    // Indian Languages (22 Official Scheduled Languages)
    "as": "Assamese (অসমীয়া)",
    "bn": "Bengali (বাংলা)",
    "brx": "Bodo (बर')",
    "doi": "Dogri (डोगरी)",
    "gu": "Gujarati (ગુજરાતી)",
    "hi": "Hindi (हिन्दी)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "ks": "Kashmiri (कॉशुर)",
    "kok": "Konkani (कोंकणी)",
    "mai": "Maithili (मैथिली)",
    "ml": "Malayalam (മലയാളം)",
    "mni-Mtei": "Manipuri (মৈতৈলোন্)",
    "mr": "Marathi (मराठी)",
    "ne": "Nepali (नेपाली)",
    "or": "Odia (ଓଡ଼ିଆ)",
    "pa": "Punjabi (ਪੰਜਾਬੀ)",
    "sa": "Sanskrit (संस्कृतम्)",
    "sat": "Santali (संताली)",
    "sd": "Sindhi (सिंधी)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "ur": "Urdu (اُردُو)"
};

// DOM Elements
const sourceTextEl = document.getElementById('source-text');
const targetTextEl = document.getElementById('target-text');
const sourceLangEl = document.getElementById('source-lang');
const targetLangEl = document.getElementById('target-lang');
const translateBtn = document.getElementById('translate-btn');
const swapBtn = document.getElementById('swap-btn');
const clearBtn = document.getElementById('clear-btn');
const voiceBtn = document.getElementById('voice-input-btn');
const ttsBtn = document.getElementById('tts-btn');
const copyBtn = document.getElementById('copy-btn');
const autoTranslateEl = document.getElementById('auto-translate');
const charCountEl = document.getElementById('char-count');
const detectedBadge = document.getElementById('detected-badge');
const loader = document.getElementById('loader');
const historyList = document.getElementById('history-list');
const clearHistoryBtn = document.getElementById('clear-history-btn');
const toastEl = document.getElementById('toast');
const toastMessageEl = document.getElementById('toast-message');
const toastIconEl = document.getElementById('toast-icon');

// State Variables
let debounceTimer;
let lastDetectedLang = '';
let isListening = false;
let recognition = null;
let currentTranslationText = '';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initSpeechRecognition();
    loadHistory();
    updateButtonsState();
    
    // Add event listeners
    sourceTextEl.addEventListener('input', handleSourceInput);
    sourceLangEl.addEventListener('change', handleLangChange);
    targetLangEl.addEventListener('change', handleLangChange);
    
    translateBtn.addEventListener('click', () => translate(true));
    swapBtn.addEventListener('click', swapLanguages);
    clearBtn.addEventListener('click', clearSourceText);
    copyBtn.addEventListener('click', copyTranslation);
    ttsBtn.addEventListener('click', speakTranslation);
    clearHistoryBtn.addEventListener('click', clearHistory);
    
    // Voice typing click
    voiceBtn.addEventListener('click', toggleVoiceInput);
});

// Toast Notifications Helper
function showToast(message, type = 'info') {
    toastMessageEl.textContent = message;
    
    // SVG icons based on type
    let iconSvg = '';
    if (type === 'success') {
        iconSvg = `<svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2.5" fill="none"><path d="M20 6L9 17l-5-5"></path></svg>`;
        toastIconEl.style.color = '#10b981'; // green
    } else if (type === 'error') {
        iconSvg = `<svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2.5" fill="none"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;
        toastIconEl.style.color = '#ef4444'; // red
    } else if (type === 'mic') {
        iconSvg = `<svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2.5" fill="none"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path></svg>`;
        toastIconEl.style.color = '#f59e0b'; // amber
    } else {
        // default info
        iconSvg = `<svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2.5" fill="none"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
        toastIconEl.style.color = '#06b6d4'; // cyan
    }
    
    toastIconEl.innerHTML = iconSvg;
    toastEl.classList.add('show');
    
    // Hide after 3 seconds
    setTimeout(() => {
        toastEl.classList.remove('show');
    }, 3000);
}

// Update Action Buttons States (Copy / Audio)
function updateButtonsState() {
    const hasTranslation = targetTextEl.textContent && 
                           targetTextEl.textContent !== "Translation will appear here..." && 
                           targetTextEl.textContent !== "Translating..." &&
                           targetTextEl.textContent !== "Error: Could not translate text. Please try again.";
                           
    copyBtn.disabled = !hasTranslation;
    ttsBtn.disabled = !hasTranslation;
}

// Debounce Translator on Input
function handleSourceInput() {
    const textLength = sourceTextEl.value.length;
    charCountEl.textContent = textLength;
    
    if (textLength === 0) {
        clearBtn.style.visibility = 'hidden';
        targetTextEl.textContent = "Translation will appear here...";
        targetTextEl.classList.add('placeholder-text');
        detectedBadge.style.display = 'none';
        updateButtonsState();
        return;
    }
    
    clearBtn.style.visibility = 'visible';
    
    if (autoTranslateEl.checked) {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            translate(false);
        }, 750);
    }
}

// Translate logic
function handleLangChange() {
    // If we change language, trigger translation if there is source text
    if (sourceTextEl.value.trim().length > 0) {
        translate(false);
    }
}

// Translate Function
async function translate(isManual = false) {
    const text = sourceTextEl.value.trim();
    if (!text) return;
    
    const sourceLang = sourceLangEl.value;
    const targetLang = targetLangEl.value;
    
    // Show Loading
    loader.style.display = 'flex';
    targetTextEl.textContent = "Translating...";
    targetTextEl.classList.add('placeholder-text');
    updateButtonsState();
    
    try {
        const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${sourceLang}&tl=${targetLang}&dt=t&q=${encodeURIComponent(text)}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Assemble translation paragraphs/lines
        let translatedText = '';
        if (data && data[0]) {
            data[0].forEach(segment => {
                if (segment[0]) {
                    translatedText += segment[0];
                }
            });
        }
        
        if (translatedText) {
            targetTextEl.textContent = translatedText;
            targetTextEl.classList.remove('placeholder-text');
            currentTranslationText = translatedText;
            
            // Detect Source Language handling
            if (sourceLang === 'auto' && data[2]) {
                const detectedCode = data[2];
                lastDetectedLang = detectedCode;
                const detectedName = languages[detectedCode] || detectedCode;
                detectedBadge.textContent = `Detected: ${detectedName}`;
                detectedBadge.style.display = 'inline-block';
            } else {
                detectedBadge.style.display = 'none';
            }
            
            // Save to history (if it's not a manual query for empty, and is final translation)
            saveToHistory(text, translatedText, sourceLang, targetLang);
        } else {
            targetTextEl.textContent = "Could not translate text.";
        }
        
    } catch (error) {
        console.error("Translation error:", error);
        targetTextEl.textContent = "Error: Could not translate text. Please try again.";
        showToast("Translation failed. Please check your internet connection.", "error");
    } finally {
        loader.style.display = 'none';
        updateButtonsState();
    }
}

// Swap Languages
function swapLanguages() {
    let src = sourceLangEl.value;
    const dest = targetLangEl.value;
    
    // Swap "auto" to either detected language or English
    if (src === 'auto') {
        src = lastDetectedLang || 'en';
    }
    
    sourceLangEl.value = dest;
    targetLangEl.value = src;
    
    // Swap values
    const srcText = sourceTextEl.value.trim();
    const destText = targetTextEl.textContent;
    
    if (destText && destText !== "Translation will appear here..." && destText !== "Translating..." && destText !== "Error: Could not translate text. Please try again.") {
        sourceTextEl.value = destText;
        targetTextEl.textContent = srcText;
        targetTextEl.classList.remove('placeholder-text');
    } else {
        sourceTextEl.value = "";
        targetTextEl.textContent = "Translation will appear here...";
        targetTextEl.classList.add('placeholder-text');
    }
    
    charCountEl.textContent = sourceTextEl.value.length;
    detectedBadge.style.display = 'none';
    
    if (sourceTextEl.value.length > 0) {
        translate(false);
    } else {
        clearBtn.style.visibility = 'hidden';
        updateButtonsState();
    }
}

// Clear source text
function clearSourceText() {
    sourceTextEl.value = "";
    targetTextEl.textContent = "Translation will appear here...";
    targetTextEl.classList.add('placeholder-text');
    detectedBadge.style.display = 'none';
    clearBtn.style.visibility = 'hidden';
    charCountEl.textContent = "0";
    
    if (isListening && recognition) {
        recognition.stop();
    }
    
    updateButtonsState();
}

// Copy translated text
function copyTranslation() {
    const text = targetTextEl.textContent;
    if (!text || text === "Translation will appear here...") return;
    
    navigator.clipboard.writeText(text)
        .then(() => {
            showToast("Translation copied!", "success");
        })
        .catch(err => {
            console.error("Failed to copy:", err);
            showToast("Could not copy text.", "error");
        });
}

// Text to Speech
function speakTranslation() {
    const text = targetTextEl.textContent;
    if (!text || text === "Translation will appear here...") return;
    
    if (!('speechSynthesis' in window)) {
        showToast("Text-to-Speech is not supported in this browser.", "error");
        return;
    }
    
    // Cancel any current speaking
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    const targetLang = targetLangEl.value;
    utterance.lang = targetLang;
    
    // Find matching voice if possible
    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find(v => v.lang.startsWith(targetLang));
    if (voice) {
        utterance.voice = voice;
    }
    
    utterance.onend = () => {
        ttsBtn.classList.remove('active');
    };
    
    utterance.onerror = (e) => {
        console.error("SpeechSynthesis error:", e);
        ttsBtn.classList.remove('active');
    };
    
    window.speechSynthesis.speak(utterance);
    showToast("Playing audio translation...", "info");
}

// Web Speech API - Speech to Text
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        // Voice typing not supported in browser
        return;
    }
    
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    
    recognition.onstart = () => {
        isListening = true;
        voiceBtn.classList.add('active');
        showToast("Microphone listening...", "mic");
    };
    
    recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        isListening = false;
        voiceBtn.classList.remove('active');
        if (event.error === 'not-allowed') {
            showToast("Microphone access blocked. Enable in settings.", "error");
        } else {
            showToast(`Voice typing failed: ${event.error}`, "error");
        }
    };
    
    recognition.onend = () => {
        isListening = false;
        voiceBtn.classList.remove('active');
    };
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        
        // Append result to source text
        const cursorPosition = sourceTextEl.selectionStart;
        const currentVal = sourceTextEl.value;
        
        const newVal = currentVal.slice(0, cursorPosition) + transcript + currentVal.slice(cursorPosition);
        sourceTextEl.value = newVal;
        sourceTextEl.focus();
        
        // Move cursor to end of inserted text
        const newCursorPos = cursorPosition + transcript.length;
        sourceTextEl.setSelectionRange(newCursorPos, newCursorPos);
        
        // Trigger translation
        handleSourceInput();
    };
}

// Toggle Voice Input
function toggleVoiceInput() {
    if (!recognition) {
        showToast("Voice typing is not supported in this browser. Try Chrome.", "error");
        return;
    }
    
    if (isListening) {
        recognition.stop();
    } else {
        // Set speech language based on selection, fallback to browser default if auto
        let srcLang = sourceLangEl.value;
        if (srcLang === 'auto') {
            srcLang = navigator.language || 'en';
        }
        recognition.lang = srcLang;
        
        try {
            recognition.start();
        } catch (e) {
            console.error("Failed to start speech recognition:", e);
        }
    }
}

// Local Storage History Management
function saveToHistory(srcText, destText, srcCode, destCode) {
    if (!srcText.trim() || !destText.trim()) return;
    
    let history = JSON.parse(localStorage.getItem('translation_history')) || [];
    
    // Avoid exact duplicate of the most recent translation
    if (history.length > 0) {
        const last = history[0];
        if (last.srcText === srcText && last.destText === destText && last.srcCode === srcCode && last.destCode === destCode) {
            return;
        }
    }
    
    const historyItem = {
        id: Date.now(),
        srcText,
        destText,
        srcCode,
        destCode,
        srcName: srcCode === 'auto' ? 'Auto' : (languages[srcCode] || srcCode),
        destName: languages[destCode] || destCode
    };
    
    // Add to beginning of history
    history.unshift(historyItem);
    
    // Keep max 10 records
    if (history.length > 10) {
        history.pop();
    }
    
    localStorage.setItem('translation_history', JSON.stringify(history));
    loadHistory();
}

function loadHistory() {
    const history = JSON.parse(localStorage.getItem('translation_history')) || [];
    
    if (history.length === 0) {
        historyList.innerHTML = `<li class="history-empty">No recent translations</li>`;
        clearHistoryBtn.style.display = 'none';
        return;
    }
    
    clearHistoryBtn.style.display = 'inline-block';
    historyList.innerHTML = '';
    
    history.forEach(item => {
        const li = document.createElement('li');
        li.className = 'history-item';
        li.dataset.id = item.id;
        
        // Click to load history item
        li.addEventListener('click', (e) => {
            // If the delete button was clicked, don't load the history item
            if (e.target.closest('.history-delete-btn')) return;
            loadHistoryItem(item);
        });
        
        li.innerHTML = `
            <div class="history-text history-source">
                <span class="history-lang-badge">${item.srcName}</span>
                <span>${escapeHtml(item.srcText)}</span>
            </div>
            <div class="history-arrow">
                <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2.5" fill="none">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                    <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
            </div>
            <div class="history-text history-target">
                <span class="history-lang-badge">${item.destName}</span>
                <span>${escapeHtml(item.destText)}</span>
            </div>
            <button class="history-delete-btn tooltip" data-tooltip="Remove from history" aria-label="Remove item from history">
                <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
        `;
        
        // Individual delete handler
        const delBtn = li.querySelector('.history-delete-btn');
        delBtn.addEventListener('click', () => deleteHistoryItem(item.id));
        
        historyList.appendChild(li);
    });
}

function loadHistoryItem(item) {
    sourceLangEl.value = item.srcCode;
    targetLangEl.value = item.destCode;
    sourceTextEl.value = item.srcText;
    targetTextEl.textContent = item.destText;
    targetTextEl.classList.remove('placeholder-text');
    charCountEl.textContent = item.srcText.length;
    clearBtn.style.visibility = 'visible';
    
    detectedBadge.style.display = 'none';
    
    updateButtonsState();
    showToast("Restored translation from history", "info");
}

function deleteHistoryItem(id) {
    let history = JSON.parse(localStorage.getItem('translation_history')) || [];
    history = history.filter(item => item.id !== id);
    localStorage.setItem('translation_history', JSON.stringify(history));
    loadHistory();
    showToast("Deleted item from history", "info");
}

function clearHistory() {
    localStorage.removeItem('translation_history');
    loadHistory();
    showToast("Cleared all history", "info");
}

// Utility function to escape HTML to prevent XSS in history list
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}
