import os
import threading
import glob
import pickle
import mimetypes
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Register MIDI MIME types for browser compatibility
mimetypes.add_type('audio/midi', '.mid')
mimetypes.add_type('audio/midi', '.midi')

# Import our ML functions
import download_data
import preprocess
from train import train
import generate

app = Flask(__name__, static_folder='static')

# Configuration
UPLOAD_FOLDER = 'data'
ALLOWED_EXTENSIONS = {'mid', 'midi'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('processed', exist_ok=True)
os.makedirs('output', exist_ok=True)

# Training state
training_lock = threading.Lock()
training_thread = None
training_status = {
    "status": "idle",        # idle, preprocessing, training, completed, error
    "current_epoch": 0,
    "total_epochs": 0,
    "loss": 0.0,
    "accuracy": 0.0,
    "progress": 0,
    "message": ""
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Status callback for training loop
def update_training_progress(epoch, total_epochs, loss, accuracy):
    global training_status
    training_status["current_epoch"] = epoch
    training_status["total_epochs"] = total_epochs
    training_status["loss"] = round(loss, 4)
    training_status["accuracy"] = round(accuracy, 4)
    training_status["progress"] = int((epoch / total_epochs) * 100)
    training_status["message"] = f"Training epoch {epoch}/{total_epochs}..."

def background_training_task(epochs, batch_size, lr):
    global training_status
    try:
        # 1. Preprocess first
        training_status["status"] = "preprocessing"
        training_status["message"] = "Parsing MIDI files and building vocabulary..."
        notes = preprocess.parse_midi_files(UPLOAD_FOLDER)
        if not notes:
            raise ValueError("No notes extracted from MIDI files. Please upload MIDI files first.")
            
        X, y, vocab, note_to_int, int_to_note = preprocess.prepare_sequences(notes, sequence_length=64)
        
        # Save preprocessed files
        with open("processed/vocab.pkl", "wb") as f:
            pickle.dump((vocab, note_to_int, int_to_note), f)
        import numpy as np
        np.savez("processed/dataset.npz", X=X, y=y)
        
        # 2. Train model
        training_status["status"] = "training"
        training_status["message"] = "Initializing model training..."
        
        # We run the training loop in-line here or import and run it with status updates
        import torch
        import torch.nn as nn
        from torch.utils.data import TensorDataset, DataLoader
        from model import MusicLSTM
        
        # PyTorch Setup
        vocab_size = len(vocab)
        X_tensor = torch.tensor(X, dtype=torch.long)
        y_tensor = torch.tensor(y, dtype=torch.long)
        dataset = TensorDataset(X_tensor, y_tensor)
        batch_size = min(batch_size, len(dataset))
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, drop_last=False)
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = MusicLSTM(vocab_size=vocab_size, embedding_dim=128, hidden_dim=256, num_layers=2)
        model = model.to(device)
        
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        
        checkpoint_path = "processed/weights.pth"
        best_loss = float('inf')
        
        for epoch in range(1, epochs + 1):
            model.train()
            total_loss = 0
            correct = 0
            total = 0
            
            for batch_x, batch_y in dataloader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                
                optimizer.zero_grad()
                logits, _ = model(batch_x)
                
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                _, predicted = logits.max(1)
                correct += predicted.eq(batch_y).sum().item()
                total += batch_y.size(0)
                
            epoch_loss = total_loss / len(dataloader)
            epoch_acc = correct / total if total > 0 else 0.0
            
            # Update status
            update_training_progress(epoch, epochs, epoch_loss, epoch_acc)
            
            # Save best checkpoint
            if epoch_loss < best_loss:
                best_loss = epoch_loss
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'loss': epoch_loss,
                    'hidden_dim': 256,
                    'num_layers': 2
                }, checkpoint_path)
                
        training_status["status"] = "completed"
        training_status["message"] = "Model trained successfully!"
        training_status["progress"] = 100
        
    except Exception as e:
        training_status["status"] = "error"
        training_status["message"] = f"Error: {str(e)}"
        print(f"Error in background training: {e}")

# Routes
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/status', methods=['GET'])
def get_status():
    model_trained = os.path.exists("processed/weights.pth")
    dataset_exists = os.path.exists("processed/dataset.npz")
    midi_count = len(glob.glob(os.path.join(UPLOAD_FOLDER, "*.mid"))) + len(glob.glob(os.path.join(UPLOAD_FOLDER, "*.midi")))
    
    return jsonify({
        "model_trained": model_trained,
        "dataset_exists": dataset_exists,
        "midi_count": midi_count,
        "training": training_status
    })

@app.route('/api/download_samples', methods=['POST'])
def download_samples():
    try:
        download_data.main()
        midi_count = len(glob.glob(os.path.join(UPLOAD_FOLDER, "*.mid")))
        return jsonify({"success": True, "message": f"Successfully downloaded/created sample MIDI files. Total MIDI files: {midi_count}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Fallback if filename was completely stripped by secure_filename (e.g., non-latin characters)
        base, ext = os.path.splitext(filename)
        if not base or filename in ['.mid', '.midi']:
            import time
            filename = f"uploaded_{int(time.time())}{ext or '.mid'}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        midi_count = len(glob.glob(os.path.join(UPLOAD_FOLDER, "*.mid"))) + len(glob.glob(os.path.join(UPLOAD_FOLDER, "*.midi")))
        return jsonify({"success": True, "filename": filename, "midi_count": midi_count})
    return jsonify({"success": False, "error": "Invalid file type. Only .mid or .midi files allowed"}), 400

@app.route('/api/train', methods=['POST'])
def start_training():
    global training_thread, training_status
    
    # Check if already training
    with training_lock:
        if training_status["status"] in ["preprocessing", "training"]:
            return jsonify({"success": False, "error": "Training is already in progress."}), 400
            
        data = request.json or {}
        epochs = int(data.get("epochs", 15))
        batch_size = int(data.get("batch_size", 32))
        lr = float(data.get("lr", 0.005))
        
        # Reset status
        training_status = {
            "status": "preprocessing",
            "current_epoch": 0,
            "total_epochs": epochs,
            "loss": 0.0,
            "accuracy": 0.0,
            "progress": 0,
            "message": "Starting background worker..."
        }
        
        training_thread = threading.Thread(
            target=background_training_task, 
            args=(epochs, batch_size, lr)
        )
        training_thread.daemon = True
        training_thread.start()
        
    return jsonify({"success": True, "message": "Training started in background."})

@app.route('/api/generate', methods=['POST'])
def generate_music():
    try:
        data = request.json or {}
        notes_count = int(data.get("notes", 100))
        temperature = float(data.get("temperature", 0.8))
        genre = data.get("genre", "classical")
        
        # File naming
        import time
        filename = f"generated_{genre}_{int(time.time())}.mid"
        filepath = os.path.join("output", filename)
        
        # Run generator
        generated_path = generate.generate(num_notes=notes_count, temperature=temperature, output_file=filepath)
        
        if generated_path:
            return jsonify({
                "success": True, 
                "filename": filename, 
                "download_url": f"/api/play/{filename}"
            })
        else:
            return jsonify({"success": False, "error": "Generation failed. Is the model trained?"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/play/<filename>', methods=['GET'])
def play_midi(filename):
    # Sanitize filename
    filename = secure_filename(filename)
    # Serve inline (as_attachment=False) so Javascript fetch can parse the binary file.
    # Native download attribute in HTML will still force a download when clicked.
    return send_from_directory(os.path.abspath("output"), filename, as_attachment=False)

@app.route('/api/history', methods=['GET'])
def get_history():
    files = glob.glob("output/*.mid")
    files.sort(key=os.path.getmtime, reverse=True)
    history = []
    for f in files:
        fname = os.path.basename(f)
        history.append({
            "filename": fname,
            "size_kb": round(os.path.getsize(f) / 1024, 2),
            "created_at": int(os.path.getmtime(f)),
            "download_url": f"/api/play/{fname}"
        })
    return jsonify({"success": True, "history": history})

if __name__ == '__main__':
    print("AI Music Generator backend server running at http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
