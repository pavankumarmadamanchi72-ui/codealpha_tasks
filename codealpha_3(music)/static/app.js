// DOM Elements
const elGenre = document.getElementById('genre');
const elTemperature = document.getElementById('temperature');
const elTempVal = document.getElementById('temp-val');
const elNotesCount = document.getElementById('notes-count');
const elNotesVal = document.getElementById('notes-val');
const elBtnGenerate = document.getElementById('btn-generate');

const elStatMidiCount = document.getElementById('stat-midi-count');
const elStatModelStatus = document.getElementById('stat-model-status');
const elBtnDownloadSamples = document.getElementById('btn-download-samples');
const elDropZone = document.getElementById('drop-zone');
const elFileInput = document.getElementById('file-input');
const elUploadProgress = document.getElementById('upload-progress');
const elUploadFilename = document.getElementById('upload-filename');
const elMiniProgressFill = document.querySelector('.mini-progress-fill');

const elTrainEpochs = document.getElementById('train-epochs');
const elTrainLr = document.getElementById('train-lr');
const elBtnTrain = document.getElementById('btn-train');
const elTrainingConsole = document.getElementById('training-console');
const elConsoleLogLines = document.getElementById('console-log-lines');
const elConsoleStatusLbl = document.getElementById('console-status-lbl');
const elConsoleProgressFill = document.getElementById('console-progress-fill');
const elConsoleLossVal = document.getElementById('console-loss-val');
const elConsoleEpochVal = document.getElementById('console-epoch-val');

const elCurrentTrackName = document.getElementById('current-track-name');
const elPianoRollCanvas = document.getElementById('piano-roll-canvas');
const elVisualizerOverlay = document.getElementById('visualizer-overlay');
const elBtnPlay = document.getElementById('btn-playback-play');
const elBtnStop = document.getElementById('btn-playback-stop');
const elTimeCurrent = document.getElementById('time-current');
const elTimeTotal = document.getElementById('time-total');
const elTimelineSlider = document.getElementById('timeline-slider');
const elTimelineProgress = document.getElementById('timeline-progress');
const elVolumeSlider = document.getElementById('volume-slider');
const elVolumeIcon = document.getElementById('volume-icon');
const elLibraryList = document.getElementById('library-list');
const elToastContainer = document.getElementById('toast-container');
const elBtnPlayerDownload = document.getElementById('btn-player-download');

// State Variables
let currentMidiData = null;
let midiParts = [];
let synths = [];
let isPlaying = false;
let playheadAnimationId = null;
let currentTrackName = "";
let isPollingTraining = false;

// Visualizer State
let notesToDraw = [];
let visualizerMinNote = 127;
let visualizerMaxNote = 0;
let visualizerDuration = 0;

// Setup UI Listeners
elTemperature.addEventListener('input', () => { elTempVal.textContent = elTemperature.value; });
elNotesCount.addEventListener('input', () => { elNotesVal.textContent = elNotesCount.value; });

// Toast notification helper
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'fa-circle-check';
    if (type === 'error') icon = 'fa-circle-exclamation';
    else if (type === 'info') icon = 'fa-circle-info';
    
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    elToastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// -------------------------------------------------------------
// System Status & Polling
// -------------------------------------------------------------
async function updateSystemStatus() {
    try {
        const r = await fetch('/api/status');
        const data = await r.json();
        
        // Update stats
        elStatMidiCount.textContent = `${data.midi_count} file(s)`;
        
        if (data.model_trained) {
            elStatModelStatus.textContent = 'Trained';
            elStatModelStatus.className = 'stat-val status-badge badge-green';
            elBtnGenerate.disabled = false;
        } else {
            elStatModelStatus.textContent = 'Untrained';
            elStatModelStatus.className = 'stat-val status-badge badge-red';
            elBtnGenerate.disabled = true;
        }
        
        // Handle background training state
        if (data.training.status === 'preprocessing' || data.training.status === 'training') {
            elTrainingConsole.style.display = 'block';
            elConsoleStatusLbl.textContent = data.training.status.toUpperCase();
            elConsoleProgressFill.style.width = `${data.training.progress}%`;
            elConsoleLossVal.textContent = data.training.loss || '--';
            elConsoleEpochVal.textContent = `${data.training.current_epoch}/${data.training.total_epochs}`;
            
            // Add a log entry if not already present
            appendLogLine(data.training.message);
            elBtnTrain.disabled = true;
            elBtnTrain.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Training...';
            
            if (!isPollingTraining) {
                isPollingTraining = true;
                startTrainingPolling();
            }
        } else if (isPollingTraining) {
            // Training just finished/stopped
            isPollingTraining = false;
            elBtnTrain.disabled = false;
            elBtnTrain.innerHTML = '<i class="fa-solid fa-play"></i> Train AI Network';
            
            if (data.training.status === 'completed') {
                showToast("Training completed successfully!", "success");
                appendLogLine("Training Success! Weights saved.");
                elConsoleProgressFill.style.width = '100%';
            } else if (data.training.status === 'error') {
                showToast(`Training failed: ${data.training.message}`, "error");
                appendLogLine(`[ERROR] ${data.training.message}`);
            }
            updateSystemStatus(); // trigger one final update to refresh flags
        }
    } catch (err) {
        console.error("Failed to fetch status:", err);
    }
}

function appendLogLine(text) {
    // Check if duplicate of last line
    const lastLine = elConsoleLogLines.lastElementChild;
    if (lastLine && lastLine.textContent === text) return;
    
    const div = document.createElement('div');
    div.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
    elConsoleLogLines.appendChild(div);
    elConsoleLogLines.scrollTop = elConsoleLogLines.scrollHeight;
}

function startTrainingPolling() {
    const interval = setInterval(async () => {
        await updateSystemStatus();
        if (!isPollingTraining) {
            clearInterval(interval);
        }
    }, 1500);
}

// -------------------------------------------------------------
// Data Download & Upload handlers
// -------------------------------------------------------------
elBtnDownloadSamples.addEventListener('click', async () => {
    elBtnDownloadSamples.disabled = true;
    elBtnDownloadSamples.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Downloading...';
    showToast("Starting sample dataset download...", "info");
    
    try {
        const r = await fetch('/api/download_samples', { method: 'POST' });
        const data = await r.json();
        if (data.success) {
            showToast(data.message, "success");
        } else {
            showToast(`Download failed: ${data.error}`, "error");
        }
    } catch (e) {
        showToast("Network error downloading samples.", "error");
    } finally {
        elBtnDownloadSamples.disabled = false;
        elBtnDownloadSamples.innerHTML = '<i class="fa-solid fa-download"></i> Load Sample MIDI Dataset';
        updateSystemStatus();
    }
});

// Dropzone Click
elDropZone.addEventListener('click', () => elFileInput.click());

// Drag events
['dragenter', 'dragover'].forEach(eventName => {
    elDropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        elDropZone.classList.add('dragover');
    }, false);
});
['dragleave', 'drop'].forEach(eventName => {
    elDropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        elDropZone.classList.remove('dragover');
    }, false);
});

elDropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
});

elFileInput.addEventListener('change', () => {
    handleFiles(elFileInput.files);
});

async function handleFiles(files) {
    if (!files.length) return;
    
    elUploadProgress.style.display = 'block';
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        elUploadFilename.textContent = `Uploading ${file.name}...`;
        elMiniProgressFill.style.width = '20%';
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            elMiniProgressFill.style.width = '60%';
            const r = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await r.json();
            
            if (data.success) {
                showToast(`Uploaded ${file.name} successfully!`, "success");
            } else {
                showToast(`Upload failed for ${file.name}: ${data.error}`, "error");
            }
        } catch (e) {
            showToast(`Network error uploading ${file.name}`, "error");
        }
    }
    
    elMiniProgressFill.style.width = '100%';
    setTimeout(() => {
        elUploadProgress.style.display = 'none';
        elMiniProgressFill.style.width = '0%';
    }, 1500);
    
    updateSystemStatus();
}

// -------------------------------------------------------------
// Training Trigger
// -------------------------------------------------------------
elBtnTrain.addEventListener('click', async () => {
    const epochs = parseInt(elTrainEpochs.value);
    const lr = parseFloat(elTrainLr.value);
    
    elBtnTrain.disabled = true;
    elBtnTrain.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Initializing...';
    elConsoleLogLines.innerHTML = '';
    elTrainingConsole.style.display = 'block';
    
    try {
        const r = await fetch('/api/train', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ epochs, lr })
        });
        const data = await r.json();
        
        if (data.success) {
            showToast("Training job started in background.", "info");
            isPollingTraining = true;
            startTrainingPolling();
        } else {
            showToast(`Could not start training: ${data.error}`, "error");
            elBtnTrain.disabled = false;
            elBtnTrain.innerHTML = '<i class="fa-solid fa-play"></i> Train AI Network';
        }
    } catch (e) {
        showToast("Network error starting training.", "error");
        elBtnTrain.disabled = false;
        elBtnTrain.innerHTML = '<i class="fa-solid fa-play"></i> Train AI Network';
    }
});

// -------------------------------------------------------------
// Generation Trigger
// -------------------------------------------------------------
elBtnGenerate.addEventListener('click', async () => {
    elBtnGenerate.disabled = true;
    elBtnGenerate.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles fa-spin"></i> Generating Melody...';
    showToast("Generating new music sequence...", "info");
    
    try {
        const r = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                notes: parseInt(elNotesCount.value),
                temperature: parseFloat(elTemperature.value),
                genre: elGenre.value
            })
        });
        const data = await r.json();
        
        if (data.success) {
            showToast("Generation completed! Loading track...", "success");
            loadHistory();
            loadAndPlayMidi(data.filename, data.download_url);
        } else {
            showToast(`Generation failed: ${data.error}`, "error");
        }
    } catch (e) {
        showToast("Network error during generation.", "error");
    } finally {
        elBtnGenerate.disabled = false;
        elBtnGenerate.innerHTML = '<i class="fa-solid fa-music"></i> Generate New Track';
    }
});

// -------------------------------------------------------------
// History/Library Load
// -------------------------------------------------------------
async function loadHistory() {
    try {
        const r = await fetch('/api/history');
        const data = await r.json();
        
        if (!data.success || !data.history.length) {
            elLibraryList.innerHTML = `
                <div class="empty-library">
                    <i class="fa-regular fa-folder-open"></i>
                    <p>No generated tracks in library. Generate a track to get started.</p>
                </div>`;
            return;
        }
        
        elLibraryList.innerHTML = data.history.map(item => {
            const dateStr = new Date(item.created_at * 1000).toLocaleString(undefined, {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            });
            return `
                <div class="history-item">
                    <div class="history-info">
                        <span class="history-name" title="${item.filename}">${item.filename}</span>
                        <span class="history-meta">${dateStr} &bull; ${item.size_kb} KB</span>
                    </div>
                    <div class="history-actions">
                        <button class="btn-icon play-btn" onclick="loadAndPlayMidi('${item.filename}', '${item.download_url}')" title="Play Track">
                            <i class="fa-solid fa-play"></i>
                        </button>
                        <a href="${item.download_url}" download class="btn-icon" title="Download MIDI">
                            <i class="fa-solid fa-download"></i>
                        </a>
                    </div>
                </div>`;
        }).join('');
    } catch (e) {
        console.error("Error loading library history:", e);
    }
}

// -------------------------------------------------------------
// Audio Synthesis & Playback
// -------------------------------------------------------------
async function loadAndPlayMidi(filename, url) {
    stopPlayback();
    elCurrentTrackName.textContent = "Loading...";
    elVisualizerOverlay.style.opacity = '1';
    elVisualizerOverlay.style.pointerEvents = 'all';
    
    try {
        // Fetch MIDI file as ArrayBuffer
        const r = await fetch(url);
        const arrayBuffer = await r.arrayBuffer();
        
        // Parse MIDI data
        const midi = new Midi(arrayBuffer);
        currentMidiData = midi;
        currentTrackName = filename;
        elCurrentTrackName.textContent = filename;
        
        // Parse notes for drawing
        parseNotesForVisualizer(midi);
        
        // Prepare Tone parts
        prepareAudioSequence(midi);
        
        // Close prompt overlay
        elVisualizerOverlay.style.opacity = '0';
        elVisualizerOverlay.style.pointerEvents = 'none';
        
        // Enable buttons
        elBtnPlay.disabled = false;
        elBtnStop.disabled = false;
        
        // Update player download button
        if (elBtnPlayerDownload) {
            elBtnPlayerDownload.href = url;
            elBtnPlayerDownload.style.opacity = '1';
            elBtnPlayerDownload.style.pointerEvents = 'auto';
        }
        
        // Auto play
        playPlayback();
    } catch (e) {
        showToast("Error loading MIDI file.", "error");
        elCurrentTrackName.textContent = "Error Loading";
        if (elBtnPlayerDownload) {
            elBtnPlayerDownload.href = "#";
            elBtnPlayerDownload.style.opacity = '0.3';
            elBtnPlayerDownload.style.pointerEvents = 'none';
        }
        console.error(e);
    }
}

function parseNotesForVisualizer(midi) {
    notesToDraw = [];
    visualizerMinNote = 127;
    visualizerMaxNote = 0;
    visualizerDuration = midi.duration;
    
    midi.tracks.forEach(track => {
        track.notes.forEach(note => {
            notesToDraw.push({
                time: note.time,
                duration: note.duration,
                midi: note.midi,
                name: note.name
            });
            if (note.midi < visualizerMinNote) visualizerMinNote = note.midi;
            if (note.midi > visualizerMaxNote) visualizerMaxNote = note.midi;
        });
    });
    
    // Add safety buffer padding to note margins
    visualizerMinNote = Math.max(0, visualizerMinNote - 2);
    visualizerMaxNote = Math.min(127, visualizerMaxNote + 2);
    
    // Trigger initial visualizer draw
    drawVisualizer();
}

function prepareAudioSequence(midi) {
    // Clear old synthesizers and parts
    midiParts.forEach(part => part.dispose());
    midiParts = [];
    
    synths.forEach(s => s.dispose());
    synths = [];
    
    Tone.Transport.cancel();
    
    // Set duration
    elTimeTotal.textContent = formatTime(midi.duration);
    
    // Create a synth with nice sound (warm triangle/square piano hybrid)
    const polySynth = new Tone.PolySynth(Tone.Synth, {
        oscillator: {
            type: "triangle"
        },
        envelope: {
            attack: 0.05,
            decay: 0.1,
            sustain: 0.3,
            release: 0.8
        }
    }).toDestination();
    
    // Adjust volume slider mapping
    polySynth.volume.value = parseFloat(elVolumeSlider.value);
    synths.push(polySynth);
    
    // Schedule notes
    midi.tracks.forEach(track => {
        const noteEvents = track.notes.map(note => ({
            time: note.time,
            note: note.name,
            duration: note.duration,
            velocity: note.velocity
        }));
        
        const part = new Tone.Part((time, value) => {
            polySynth.triggerAttackRelease(value.note, value.duration, time, value.velocity * 0.7);
        }, noteEvents).start(0);
        
        midiParts.push(part);
    });
    
    // Track timeline progress
    Tone.Transport.scheduleRepeat(() => {
        const time = Tone.Transport.seconds;
        elTimeCurrent.textContent = formatTime(time);
        
        const pct = (time / midi.duration) * 100;
        elTimelineProgress.style.width = `${Math.min(100, pct)}%`;
        
        if (time >= midi.duration) {
            stopPlayback();
        }
    }, 0.1);
}

function playPlayback() {
    if (isPlaying) return;
    
    // Start Audio Context if suspended (browser requirements)
    if (Tone.context.state !== 'running') {
        Tone.start();
    }
    
    isPlaying = true;
    Tone.Transport.start();
    
    elBtnPlay.innerHTML = '<i class="fa-solid fa-pause"></i>';
    elBtnPlay.className = 'btn-control pause';
    
    // Start canvas animation
    animateVisualizer();
}

function pausePlayback() {
    if (!isPlaying) return;
    isPlaying = false;
    Tone.Transport.pause();
    
    elBtnPlay.innerHTML = '<i class="fa-solid fa-play"></i>';
    elBtnPlay.className = 'btn-control play';
    
    if (playheadAnimationId) {
        cancelAnimationFrame(playheadAnimationId);
        playheadAnimationId = null;
    }
}

function stopPlayback() {
    isPlaying = false;
    Tone.Transport.stop();
    
    elBtnPlay.innerHTML = '<i class="fa-solid fa-play"></i>';
    elBtnPlay.className = 'btn-control play';
    
    elTimeCurrent.textContent = "0:00";
    elTimelineProgress.style.width = "0%";
    
    if (playheadAnimationId) {
        cancelAnimationFrame(playheadAnimationId);
        playheadAnimationId = null;
    }
    
    drawVisualizer(); // redraw to reset playhead
}

elBtnPlay.addEventListener('click', () => {
    if (isPlaying) {
        pausePlayback();
    } else {
        playPlayback();
    }
});

elBtnStop.addEventListener('click', stopPlayback);

// Timeline Seeking
elTimelineSlider.addEventListener('click', (e) => {
    if (!currentMidiData) return;
    
    const rect = elTimelineSlider.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const pct = clickX / rect.width;
    
    const seekTime = pct * currentMidiData.duration;
    Tone.Transport.seconds = seekTime;
    
    // Update labels immediately
    elTimeCurrent.textContent = formatTime(seekTime);
    elTimelineProgress.style.width = `${pct * 100}%`;
    
    drawVisualizer();
});

// Volume control
elVolumeSlider.addEventListener('input', () => {
    const vol = parseFloat(elVolumeSlider.value);
    synths.forEach(s => { s.volume.value = vol; });
    
    if (vol === -30) {
        elVolumeIcon.className = "fa-solid fa-volume-xmark";
    } else if (vol < -10) {
        elVolumeIcon.className = "fa-solid fa-volume-low";
    } else {
        elVolumeIcon.className = "fa-solid fa-volume-high";
    }
});

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

// -------------------------------------------------------------
// Canvas Piano Roll Visualizer Rendering
// -------------------------------------------------------------
function resizeCanvas() {
    const rect = elPianoRollCanvas.parentElement.getBoundingClientRect();
    elPianoRollCanvas.width = rect.width;
    elPianoRollCanvas.height = rect.height;
    drawVisualizer();
}

window.addEventListener('resize', resizeCanvas);

function drawVisualizer() {
    const canvas = elPianoRollCanvas;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    
    // Clear
    ctx.fillStyle = '#070911';
    ctx.fillRect(0, 0, w, h);
    
    if (!notesToDraw.length) return;
    
    const time = Tone.Transport.seconds;
    
    // Drawing Dimensions
    // We scroll notes horizontally. Let's make 8 seconds visible at a time.
    const secondsVisible = 8;
    const scaleX = w / secondsVisible;
    
    // We want the playhead centered horizontally (at w/2), or offset to left (at w/4)
    const playheadX = w / 4;
    const scrollOffsetTime = time - (playheadX / scaleX);
    
    const noteRange = visualizerMaxNote - visualizerMinNote;
    const rowHeight = h / (noteRange || 1);
    
    // 1. Draw Grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.02)';
    ctx.lineWidth = 1;
    for (let noteNum = visualizerMinNote; noteNum <= visualizerMaxNote; noteNum++) {
        const y = h - ((noteNum - visualizerMinNote) * rowHeight);
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
    }
    
    // Beat lines (vertical lines every 0.5s)
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
    const startBeat = Math.floor(scrollOffsetTime * 2) / 2;
    for (let beatTime = startBeat; beatTime < scrollOffsetTime + secondsVisible; beatTime += 0.5) {
        const x = (beatTime - scrollOffsetTime) * scaleX;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
    }
    
    // 2. Draw Notes
    notesToDraw.forEach(note => {
        // Calculate coordinates
        const x = (note.time - scrollOffsetTime) * scaleX;
        const width = note.duration * scaleX;
        
        // Pitch calculation (higher pitch = higher y in canvas, so subtract from h)
        const y = h - ((note.midi - visualizerMinNote + 1) * rowHeight);
        const height = rowHeight - 2;
        
        // Only draw if visible
        if (x + width < 0 || x > w) return;
        
        // Check if note is currently active (playing)
        const isActive = (time >= note.time && time <= note.time + note.duration);
        
        if (isActive) {
            // Glowing style for active note
            ctx.fillStyle = '#00ffff';
            ctx.shadowBlur = 15;
            ctx.shadowColor = '#00ffff';
        } else {
            // Normal purple gradient style for inactive note
            const grad = ctx.createLinearGradient(x, y, x + width, y);
            grad.addColorStop(0, '#8a2be2');
            grad.addColorStop(1, '#a14dff');
            ctx.fillStyle = grad;
            ctx.shadowBlur = 0;
        }
        
        // Draw round rect for note
        drawRoundRect(ctx, x, y, width, height, 4);
    });
    
    // Reset shadow
    ctx.shadowBlur = 0;
    
    // 3. Draw Playhead Line
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(playheadX, 0);
    ctx.lineTo(playheadX, h);
    ctx.stroke();
    
    // Glowing cap at the top of the playhead
    ctx.fillStyle = '#fff';
    ctx.shadowBlur = 8;
    ctx.shadowColor = '#fff';
    ctx.beginPath();
    ctx.arc(playheadX, 0, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
}

function drawRoundRect(ctx, x, y, width, height, radius) {
    if (width < 2 * radius) radius = width / 2;
    if (height < 2 * radius) radius = height / 2;
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.arcTo(x + width, y, x + width, y + height, radius);
    ctx.arcTo(x + width, y + height, x, y + height, radius);
    ctx.arcTo(x, y + height, x, y, radius);
    ctx.arcTo(x, y, x + width, y, radius);
    ctx.closePath();
    ctx.fill();
}

function animateVisualizer() {
    if (!isPlaying) return;
    drawVisualizer();
    playheadAnimationId = requestAnimationFrame(animateVisualizer);
}

// -------------------------------------------------------------
// Initialization
// -------------------------------------------------------------
window.addEventListener('DOMContentLoaded', () => {
    resizeCanvas();
    updateSystemStatus();
    loadHistory();
    
    // Periodically update status to check if anything is modified
    setInterval(updateSystemStatus, 10000);
});
