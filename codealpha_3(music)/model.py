import torch
import torch.nn as nn

class MusicLSTM(nn.Module):
    def __init__(self, vocab_size, embedding_dim=128, hidden_dim=256, num_layers=2):
        super(MusicLSTM, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(
            embedding_dim, 
            hidden_dim, 
            num_layers=num_layers, 
            batch_first=True, 
            dropout=0.3 if num_layers > 1 else 0.0
        )
        self.fc = nn.Linear(hidden_dim, vocab_size)
        
    def forward(self, x, hidden=None):
        # x shape: [batch_size, seq_len]
        embeds = self.embedding(x) # shape: [batch_size, seq_len, embedding_dim]
        out, hidden = self.lstm(embeds, hidden) # out shape: [batch_size, seq_len, hidden_dim]
        
        # We only take the output from the last time step for classification
        last_out = out[:, -1, :] # shape: [batch_size, hidden_dim]
        logits = self.fc(last_out) # shape: [batch_size, vocab_size]
        return logits, hidden
