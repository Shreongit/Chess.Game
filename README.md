# Knightfall Chess

A local two-player chess game built with Python, Pygame, and `python-chess`.

## Features
- Standard legal move validation for all pieces
- Check, checkmate, stalemate, insufficient-material and draw-claim status
- Castling and en passant
- Pawn promotion with Queen, Rook, Bishop, or Knight selection
- Move history in algebraic notation
- Undo, restart, and board flip controls
- Highlighted last move, selected square, legal destinations, and checked king
- Uses the included piece artwork, with Unicode fallback if an image is unavailable

## Requirements
- Python 3.10 or newer
- Pygame
- python-chess

## Run on Windows (PowerShell)

```powershell
cd pygameChess-corrected
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

If PowerShell blocks activation, run the commands without activating the environment:

```powershell
py -m pip install -r requirements.txt
py main.py
```

## Controls
- **Mouse:** Select a piece, then click a highlighted legal destination.
- **Promotion:** Click Queen / Rook / Bishop / Knight in the promotion dialog, or press Q / R / B / N.
- **U:** Undo the last move.
- **R:** Start a new game.
- **F:** Flip the board.
- **Esc:** Close the promotion dialog.

## Implementation note
The original hand-written move generation has been replaced by `python-chess` for rule enforcement. This avoids common correctness bugs involving king safety, castling, en passant, promotion, checkmate, and stalemate. The game is a local two-player application; it does not include AI or online multiplayer.
