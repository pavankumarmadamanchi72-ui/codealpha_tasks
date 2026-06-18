import os
import argparse
import pickle
import numpy as np
import torch
from model import MusicLSTM
from music21 import stream, note, chord, instrument

def sample_with_temperature(logits, temperature):
    """Helper to sample an index from the probability distribution, scaled by temperature."""
    if temperature <= 0.0:
        return torch.argmax(logits).item()
        
    # Apply temperature scaling
    logits = logits / temperature
    probabilities = torch.softmax(logits, dim=0)
    
    # Sample from multinomial distribution
    sampled_idx = torch.multinomial(probabilities, 1).item()
    return sampled_idx

def create_midi(note_sequence, output_filepath):
    """Converts a sequence of note/chord string tokens back to a MIDI file using music21."""
    offset = 0
    output_notes = []
    
    for pattern in note_sequence:
        # 1. Rest
        if pattern == "rest":
            r = note.Rest()
            r.duration.quarterLength = 0.5  # standard duration for output notes
            r.offset = offset
            output_notes.append(r)
        
        # 2. Chord (contains dots, e.g., "C4.E4.G4" or midi number representations)
        elif "." in pattern:
            chord_notes = pattern.split(".")
            notes = []
            for n_str in chord_notes:
                try:
                    new_note = note.Note(n_str)
                    new_note.storedInstrument = instrument.Piano()
                    notes.append(new_note)
                except Exception:
                    # Ignore invalid note names
                    pass
            if notes:
                c = chord.Chord(notes)
                c.duration.quarterLength = 0.5
                c.offset = offset
                output_notes.append(c)
                
        # 3. Single Note
        else:
            try:
                n = note.Note(pattern)
                n.storedInstrument = instrument.Piano()
                n.duration.quarterLength = 0.5
                n.offset = offset
                output_notes.append(n)
            except Exception:
                pass
                
        # Increment offset by 0.5 quarter length (e.g. eighth notes at standard 120 bpm)
        offset += 0.5

    midi_stream = stream.Stream(output_notes)
    midi_stream.write('midi', fp=output_filepath)
    print(f"MIDI file saved to: {output_filepath}")

def generate(num_notes=100, temperature=0.8, output_file="generated_music.mid"):
    processed_dir = "processed"
    weights_path = os.path.join(processed_dir, "weights.pth")
    vocab_path = os.path.join(processed_dir, "vocab.pkl")
    dataset_path = os.path.join(processed_dir, "dataset.npz")
    
    if not (os.path.exists(weights_path) and os.path.exists(vocab_path)):
        print("Error: Model weights or vocab.pkl not found. Please train the model first.")
        return None

    # Load vocab
    with open(vocab_path, "rb") as f:
        vocab, note_to_int, int_to_note = pickle.load(f)
    vocab_size = len(vocab)
    
    # Load model checkpoint variables
    checkpoint = torch.load(weights_path, map_location=torch.device('cpu'))
    hidden_dim = checkpoint.get('hidden_dim', 256)
    num_layers = checkpoint.get('num_layers', 2)
    
    # Initialize model and load weights
    model = MusicLSTM(vocab_size=vocab_size, embedding_dim=128, hidden_dim=hidden_dim, num_layers=num_layers)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    # Load dataset to get a seed sequence
    X_seed = None
    if os.path.exists(dataset_path):
        try:
            data = np.load(dataset_path)
            X = data['X']
            # Pick a random sequence as seed
            seed_idx = np.random.randint(0, len(X))
            X_seed = list(X[seed_idx])
            print(f"Initialized generation with a random seed sequence from dataset.")
        except Exception:
            pass
            
    if X_seed is None:
        # Fallback seed: just random indices
        X_seed = [np.random.randint(0, vocab_size) for _ in range(64)]
        print("Initialized generation with a fully random seed sequence.")
        
    sequence_length = len(X_seed)
    current_sequence = list(X_seed)
    generated_indices = []
    
    print(f"Generating {num_notes} notes...")
    with torch.no_grad():
        for _ in range(num_notes):
            # Form input tensor [1, sequence_length]
            input_tensor = torch.tensor([current_sequence[-sequence_length:]], dtype=torch.long)
            
            # Predict logits
            logits, _ = model(input_tensor)
            logits = logits[0]  # get first batch element
            
            # Sample next note
            next_idx = sample_with_temperature(logits, temperature)
            generated_indices.append(next_idx)
            
            # Update current sequence
            current_sequence.append(next_idx)
            
    # Convert generated indices back to note/chord names
    generated_notes = [int_to_note[idx] for idx in generated_indices]
    
    # Ensure output folder exists
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
    
    # Save as MIDI
    create_midi(generated_notes, output_file)
    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Music using Trained LSTM Model")
    parser.add_argument("--notes", type=int, default=100, help="Number of notes to generate")
    parser.add_argument("--temp", type=float, default=0.8, help="Temperature (creativity index, default 0.8)")
    parser.add_argument("--out", type=str, default="output/generated_music.mid", help="Output MIDI file path")
    args = parser.parse_args()
    
    generate(num_notes=args.notes, temperature=args.temp, output_file=args.out)
