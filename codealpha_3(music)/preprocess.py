import os
import glob
import pickle
import numpy as np
from music21 import converter, note, chord

def parse_midi_files(data_dir):
    """Parses all MIDI files in data_dir and extracts notes, chords, and rests."""
    notes = []
    midi_files = glob.glob(os.path.join(data_dir, "*.mid"))
    
    if not midi_files:
        print(f"No MIDI files found in {data_dir}!")
        return notes

    print(f"Found {len(midi_files)} MIDI files to parse.")
    
    for file_path in midi_files:
        print(f"Parsing {os.path.basename(file_path)}...")
        try:
            midi = converter.parse(file_path)
            # Use flatten() to collapse all parts/voices, and notesAndRests to grab notes, chords, rests
            elements = midi.flatten().notesAndRests
            
            file_notes = []
            for element in elements:
                if isinstance(element, note.Note):
                    file_notes.append(str(element.pitch))
                elif isinstance(element, chord.Chord):
                    # Join notes in the chord with dot, e.g., "C4.E4.G4"
                    chord_str = ".".join(str(n.pitch) for n in element.notes)
                    file_notes.append(chord_str)
                elif isinstance(element, note.Rest):
                    # Only add rests that are not extremely short
                    if element.duration.quarterLength >= 0.25:
                        file_notes.append("rest")
            
            print(f"  Extracted {len(file_notes)} note/chord events.")
            notes.extend(file_notes)
        except Exception as e:
            print(f"  Error parsing {file_path}: {e}")
            
    return notes

def prepare_sequences(notes, sequence_length=64):
    """Prepares input sequences and output targets from note list."""
    # Get all unique notes/chords
    vocab = sorted(list(set(notes)))
    vocab_size = len(vocab)
    print(f"Vocabulary Size: {vocab_size} unique elements (notes, chords, rests).")
    
    # Create mapping from note to integer and vice versa
    note_to_int = {note: i for i, note in enumerate(vocab)}
    int_to_note = {i: note for i, note in enumerate(vocab)}
    
    network_input = []
    network_output = []
    
    # Create training patterns
    for i in range(0, len(notes) - sequence_length):
        seq_in = notes[i:i + sequence_length]
        seq_out = notes[i + sequence_length]
        network_input.append([note_to_int[char] for char in seq_in])
        network_output.append(note_to_int[seq_out])
        
    n_patterns = len(network_input)
    print(f"Total training sequences created: {n_patterns}")
    
    return np.array(network_input), np.array(network_output), vocab, note_to_int, int_to_note

def main():
    data_dir = "data"
    output_dir = "processed"
    os.makedirs(output_dir, exist_ok=True)
    
    notes = parse_midi_files(data_dir)
    
    if not notes:
        print("No notes extracted! Please make sure MIDI files exist in 'data/' directory.")
        return
        
    sequence_length = 64
    X, y, vocab, note_to_int, int_to_note = prepare_sequences(notes, sequence_length)
    
    # Save the data
    with open(os.path.join(output_dir, "vocab.pkl"), "wb") as f:
        pickle.dump((vocab, note_to_int, int_to_note), f)
        
    np.savez(os.path.join(output_dir, "dataset.npz"), X=X, y=y)
    
    # Also save raw notes sequence just in case
    with open(os.path.join(output_dir, "notes_raw.pkl"), "wb") as f:
        pickle.dump(notes, f)
        
    print("Preprocessing completed and files saved successfully!")

if __name__ == "__main__":
    main()
