import os
import requests

MIDI_URLS = {
    "fantasie_impromptu.mid": "https://raw.githubusercontent.com/skuldur/Classical-Piano-Composer/master/midi_songs/Fantasie_Impromptu.mid",
    "chpn_op27_2.mid": "https://raw.githubusercontent.com/skuldur/Classical-Piano-Composer/master/midi_songs/chpn_op27_2.mid",
    "grape.mid": "https://raw.githubusercontent.com/skuldur/Classical-Piano-Composer/master/midi_songs/grape.mid",
    "silent_night.mid": "https://raw.githubusercontent.com/skuldur/Classical-Piano-Composer/master/midi_songs/silent_night.mid"
}

def create_fallback_classical(file_path):
    """Generates a classical C major scale and chord progression."""
    from music21 import stream, note, chord, meter, tempo
    
    s = stream.Stream()
    s.append(tempo.MetronomeMark(number=100))
    s.append(meter.TimeSignature('4/4'))
    
    # 1. Scale ascend/descend
    pitches = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5', 'B4', 'A4', 'G4', 'F4', 'E4', 'D4', 'C4']
    for p in pitches:
        n = note.Note(p)
        n.duration.quarterLength = 0.5
        s.append(n)
        
    # 2. Chord Progression
    chords = [
        ['C4', 'E4', 'G4'],
        ['F4', 'A4', 'C5'],
        ['G4', 'B4', 'D5'],
        ['C4', 'E4', 'G4']
    ]
    for c_notes in chords:
        c = chord.Chord(c_notes)
        c.duration.quarterLength = 1.0
        s.append(c)
        
    s.write('midi', fp=file_path)
    print(f"Generated fallback Classical MIDI: {file_path}")

def create_fallback_nocturne(file_path):
    """Generates a Chopin nocturne style melody in E-flat major with arpeggios."""
    from music21 import stream, note, chord, meter, tempo
    
    s = stream.Stream()
    s.append(tempo.MetronomeMark(number=70))
    s.append(meter.TimeSignature('3/4'))
    
    # Eb major progression with melody
    melody = ['G4', 'Bb4', 'Eb5', 'D5', 'C5', 'Bb4', 'G4', 'Ab4', 'F4', 'Eb4']
    for m in melody:
        n = note.Note(m)
        n.duration.quarterLength = 1.0
        s.append(n)
        
    # Arpeggios (Eb -> Ab -> Bb -> Eb)
    arpeggios = [
        ['Eb3', 'G3', 'Bb3', 'Eb4'],
        ['Ab3', 'C4', 'Eb4', 'Ab4'],
        ['Bb3', 'D4', 'F4', 'Bb4'],
        ['Eb3', 'G3', 'Bb3', 'Eb4']
    ]
    for arp in arpeggios:
        for p in arp:
            n = note.Note(p)
            n.duration.quarterLength = 0.5
            s.append(n)
            
    s.write('midi', fp=file_path)
    print(f"Generated fallback Nocturne MIDI: {file_path}")

def create_fallback_jazz(file_path):
    """Generates a 12-bar blues progression with jazz chords."""
    from music21 import stream, note, chord, meter, tempo
    
    s = stream.Stream()
    s.append(tempo.MetronomeMark(number=120))
    s.append(meter.TimeSignature('4/4'))
    
    # C7 -> F7 -> C7 -> C7 -> F7 -> F7 -> C7 -> C7 -> G7 -> F7 -> C7 -> G7
    progression = [
        ['C3', 'E3', 'G3', 'Bb3'], # C7
        ['F3', 'A3', 'C4', 'Eb4'], # F7
        ['C3', 'E3', 'G3', 'Bb3'], # C7
        ['C3', 'E3', 'G3', 'Bb3'], # C7
        ['F3', 'A3', 'C4', 'Eb4'], # F7
        ['F3', 'A3', 'C4', 'Eb4'], # F7
        ['C3', 'E3', 'G3', 'Bb3'], # C7
        ['C3', 'E3', 'G3', 'Bb3'], # C7
        ['G3', 'B3', 'D4', 'F4'],  # G7
        ['F3', 'A3', 'C4', 'Eb4'], # F7
        ['C3', 'E3', 'G3', 'Bb3'], # C7
        ['G3', 'B3', 'D4', 'F4']   # G7
    ]
    
    # Play chords with a swing feel rhythm
    for ch_notes in progression:
        # Beats 1-2: Chord
        c1 = chord.Chord(ch_notes)
        c1.duration.quarterLength = 2.0
        s.append(c1)
        
        # Beat 3: Rest
        r = note.Rest()
        r.duration.quarterLength = 1.0
        s.append(r)
        
        # Beat 4: Walk the bass note
        n = note.Note(ch_notes[0]) # root note
        n.duration.quarterLength = 1.0
        s.append(n)
        
    s.write('midi', fp=file_path)
    print(f"Generated fallback Jazz MIDI: {file_path}")

def main():
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    print("Collecting MIDI music data...")
    downloaded_any = False
    
    for name, url in MIDI_URLS.items():
        dest = os.path.join(data_dir, name)
        if os.path.exists(dest):
            print(f"File already exists: {dest}")
            downloaded_any = True
            continue
            
        print(f"Downloading {name} from {url}...")
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                with open(dest, 'wb') as f:
                    f.write(r.content)
                print(f"Successfully downloaded: {dest}")
                downloaded_any = True
            else:
                print(f"Failed to download {name}: HTTP {r.status_code}")
        except Exception as e:
            print(f"Failed to download {name} due to network error: {e}")
            
    # Always generate local fallbacks to ensure rich training material
    print("Generating/Updating rich offline MIDI files in data/ directory...")
    try:
        create_fallback_classical(os.path.join(data_dir, "fallback_classical_c_major.mid"))
        create_fallback_nocturne(os.path.join(data_dir, "fallback_nocturne_eb_major.mid"))
        create_fallback_jazz(os.path.join(data_dir, "fallback_jazz_blues.mid"))
    except Exception as e:
        print(f"Error creating offline fallback MIDIs: {e}")
        
    print("Data collection completed!")

if __name__ == "__main__":
    main()
