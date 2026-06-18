import os
import argparse
import pickle
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from model import MusicLSTM

def train(epochs=50, batch_size=64, lr=0.001, hidden_dim=256, num_layers=2):
    # Setup directories
    processed_dir = "processed"
    dataset_path = os.path.join(processed_dir, "dataset.npz")
    vocab_path = os.path.join(processed_dir, "vocab.pkl")
    
    if not (os.path.exists(dataset_path) and os.path.exists(vocab_path)):
        print("Error: Preprocessed dataset or vocabulary not found! Run preprocess.py first.")
        return
        
    # Load vocabulary
    with open(vocab_path, "rb") as f:
        vocab, note_to_int, int_to_note = pickle.load(f)
        
    vocab_size = len(vocab)
    print(f"Loaded vocabulary of size: {vocab_size}")
    
    # Load dataset
    data = np.load(dataset_path)
    X, y = data['X'], data['y']
    print(f"Loaded X shape: {X.shape}, y shape: {y.shape}")
    
    # Convert to PyTorch Tensors
    X_tensor = torch.tensor(X, dtype=torch.long)
    y_tensor = torch.tensor(y, dtype=torch.long)
    
    # Create DataLoader
    dataset = TensorDataset(X_tensor, y_tensor)
    batch_size = min(batch_size, len(dataset))
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, drop_last=False)
    
    # Set device (CPU is default since we installed CPU version, but check CUDA anyway)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Instantiate Model
    model = MusicLSTM(vocab_size=vocab_size, embedding_dim=128, hidden_dim=hidden_dim, num_layers=num_layers)
    model = model.to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    # Checkpoint saving path
    checkpoint_path = os.path.join(processed_dir, "weights.pth")
    best_loss = float('inf')
    
    print("Starting training...")
    for epoch in range(epochs):
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
            
            # Accuracy metric
            _, predicted = logits.max(1)
            correct += predicted.eq(batch_y).sum().item()
            total += batch_y.size(0)
            
        epoch_loss = total_loss / len(dataloader)
        epoch_acc = correct / total
        
        print(f"Epoch {epoch+1}/{epochs} | Loss: {epoch_loss:.4f} | Acc: {epoch_acc:.4f}")
        
        # Save best model checkpoint
        if epoch_loss < best_loss:
            best_loss = epoch_loss
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': epoch_loss,
                'hidden_dim': hidden_dim,
                'num_layers': num_layers
            }, checkpoint_path)
            print(f"  --> Saved new best model checkpoint to {checkpoint_path}")
            
    print("Training finished!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PyTorch LSTM Music Generator")
    parser.add_argument("--epochs", type=int, default=30, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--hidden_dim", type=int, default=256, help="Hidden dimension of LSTM")
    parser.add_argument("--num_layers", type=int, default=2, help="Number of LSTM layers")
    args = parser.parse_args()
    
    train(
        epochs=args.epochs, 
        batch_size=args.batch_size, 
        lr=args.lr, 
        hidden_dim=args.hidden_dim, 
        num_layers=args.num_layers
    )
