from __future__ import annotations

import sys
from pathlib import Path

import pygame
import chess

# ----------------------------- Configuration -----------------------------
pygame.init()
pygame.display.set_caption("Knightfall Chess")
WIDTH, HEIGHT = 1120, 820
BOARD_SIZE = 704
SQUARE_SIZE = BOARD_SIZE // 8
BOARD_X, BOARD_Y = 34, 82
PANEL_X = 780
FPS = 60

BG = (18, 22, 31)
PANEL = (27, 33, 45)
PANEL_LIGHT = (37, 45, 60)
TEXT = (237, 241, 247)
MUTED = (155, 166, 184)
ACCENT = (105, 190, 160)
ACCENT_DARK = (48, 105, 88)
LIGHT_SQUARE = (224, 218, 201)
DARK_SQUARE = (104, 133, 125)
SELECTED = (244, 205, 92)
MOVE_DOT = (40, 48, 56)
LAST_MOVE = (225, 197, 103, 95)
CHECK = (222, 86, 91)
BUTTON = (55, 66, 85)
BUTTON_HOVER = (72, 86, 108)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("segoeui,arial", 18)
small_font = pygame.font.SysFont("segoeui,arial", 14)
title_font = pygame.font.SysFont("segoeui,arial", 30, bold=True)
piece_font = pygame.font.SysFont("dejavusans", 40)

ROOT = Path(__file__).resolve().parent
IMAGE_DIR = ROOT / "assets" / "images"


def load_piece_images():
    images = {}
    names = {
        (chess.WHITE, chess.PAWN): "white pawn",
        (chess.WHITE, chess.KNIGHT): "white knight",
        (chess.WHITE, chess.BISHOP): "white bishop",
        (chess.WHITE, chess.ROOK): "white rook",
        (chess.WHITE, chess.QUEEN): "white queen",
        (chess.WHITE, chess.KING): "white king",
        (chess.BLACK, chess.PAWN): "black pawn",
        (chess.BLACK, chess.KNIGHT): "black knight",
        (chess.BLACK, chess.BISHOP): "black bishop",
        (chess.BLACK, chess.ROOK): "black rook",
        (chess.BLACK, chess.QUEEN): "black queen",
        (chess.BLACK, chess.KING): "black king",
    }
    for key, filename in names.items():
        path = IMAGE_DIR / f"{filename}.png"
        try:
            image = pygame.image.load(str(path)).convert_alpha()
            pad = 14 if key[1] == chess.PAWN else 8
            image = pygame.transform.smoothscale(image, (SQUARE_SIZE - pad, SQUARE_SIZE - pad))
            images[key] = image
        except (pygame.error, FileNotFoundError):
            images[key] = None
    return images


PIECE_IMAGES = load_piece_images()
UNICODE = {
    (chess.WHITE, chess.KING): "♔", (chess.WHITE, chess.QUEEN): "♕",
    (chess.WHITE, chess.ROOK): "♖", (chess.WHITE, chess.BISHOP): "♗",
    (chess.WHITE, chess.KNIGHT): "♘", (chess.WHITE, chess.PAWN): "♙",
    (chess.BLACK, chess.KING): "♚", (chess.BLACK, chess.QUEEN): "♛",
    (chess.BLACK, chess.ROOK): "♜", (chess.BLACK, chess.BISHOP): "♝",
    (chess.BLACK, chess.KNIGHT): "♞", (chess.BLACK, chess.PAWN): "♟",
}

board = chess.Board()
selected_square = None
legal_targets = []
flipped = False
promotion_pending = None
message = "Select a piece, then choose a highlighted square."
message_until = 0
undo_button = pygame.Rect(PANEL_X, 692, 150, 46)
restart_button = pygame.Rect(PANEL_X + 164, 692, 150, 46)
flip_button = pygame.Rect(PANEL_X, 748, 314, 40)


def draw_text(text, x, y, color=TEXT, use_font=font):
    image = use_font.render(str(text), True, color)
    screen.blit(image, (x, y))
    return image.get_rect(topleft=(x, y))


def square_rect(square):
    file_index = chess.square_file(square)
    rank_index = chess.square_rank(square)
    if flipped:
        col, row = 7 - file_index, rank_index
    else:
        col, row = file_index, 7 - rank_index
    return pygame.Rect(BOARD_X + col * SQUARE_SIZE, BOARD_Y + row * SQUARE_SIZE,
                       SQUARE_SIZE, SQUARE_SIZE)


def square_from_pos(pos):
    x, y = pos
    if not (BOARD_X <= x < BOARD_X + BOARD_SIZE and BOARD_Y <= y < BOARD_Y + BOARD_SIZE):
        return None
    col = (x - BOARD_X) // SQUARE_SIZE
    row = (y - BOARD_Y) // SQUARE_SIZE
    if flipped:
        file_index, rank_index = 7 - col, row
    else:
        file_index, rank_index = col, 7 - row
    return chess.square(file_index, rank_index)


def status_line():
    if board.is_checkmate():
        return f"{'White' if board.turn == chess.BLACK else 'Black'} wins by checkmate"
    if board.is_stalemate():
        return "Draw by stalemate"
    if board.is_insufficient_material():
        return "Draw — insufficient material"
    if board.can_claim_threefold_repetition():
        return "Threefold repetition can be claimed"
    if board.can_claim_fifty_moves():
        return "50-move draw can be claimed"
    side = "White" if board.turn else "Black"
    if board.is_check():
        return f"{side} to move — CHECK!"
    return f"{side} to move"


def game_over():
    return board.is_game_over(claim_draw=False)


def button(rect, label, mouse_pos, disabled=False):
    hovered = rect.collidepoint(mouse_pos) and not disabled
    color = PANEL_LIGHT if disabled else BUTTON_HOVER if hovered else BUTTON
    pygame.draw.rect(screen, color, rect, border_radius=10)
    pygame.draw.rect(screen, (71, 84, 105), rect, width=1, border_radius=10)
    txt = font.render(label, True, MUTED if disabled else TEXT)
    screen.blit(txt, txt.get_rect(center=rect.center))


def draw_board():
    # Board background and squares
    for rank in range(8):
        for file_index in range(8):
            square = chess.square(file_index, rank)
            rect = square_rect(square)
            color = LIGHT_SQUARE if (file_index + rank) % 2 else DARK_SQUARE
            pygame.draw.rect(screen, color, rect)

    # Last move tint
    if board.move_stack:
        last = board.peek()
        for sq in (last.from_square, last.to_square):
            overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            overlay.fill(LAST_MOVE)
            screen.blit(overlay, square_rect(sq).topleft)

    # Legal move markers
    for target in legal_targets:
        rect = square_rect(target)
        if board.piece_at(target):
            pygame.draw.circle(screen, (34, 42, 47), rect.center, 31, 4)
        else:
            pygame.draw.circle(screen, MOVE_DOT, rect.center, 9)

    if selected_square is not None:
        pygame.draw.rect(screen, SELECTED, square_rect(selected_square), width=4)

    # Highlight the king in check
    if board.is_check():
        king_sq = board.king(board.turn)
        if king_sq is not None:
            overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            overlay.fill((222, 65, 74, 125))
            screen.blit(overlay, square_rect(king_sq).topleft)

    # Pieces
    for square, piece in board.piece_map().items():
        rect = square_rect(square)
        image = PIECE_IMAGES.get((piece.color, piece.piece_type))
        if image:
            screen.blit(image, image.get_rect(center=rect.center))
        else:
            glyph = piece_font.render(UNICODE[(piece.color, piece.piece_type)], True,
                                      (250, 250, 245) if piece.color else (20, 23, 30))
            screen.blit(glyph, glyph.get_rect(center=rect.center))

    # Coordinates
    for col in range(8):
        file_index = 7 - col if flipped else col
        rank_index = col
        x = BOARD_X + col * SQUARE_SIZE + 5
        y = BOARD_Y + BOARD_SIZE - 19
        draw_text(chess.FILE_NAMES[file_index], x, y, (250, 250, 240), small_font)
    for row in range(8):
        rank = row + 1 if flipped else 8 - row
        x = BOARD_X + 5
        y = BOARD_Y + row * SQUARE_SIZE + 3
        draw_text(rank, x, y, (250, 250, 240), small_font)

    pygame.draw.rect(screen, (63, 76, 88), (BOARD_X, BOARD_Y, BOARD_SIZE, BOARD_SIZE), width=2)


def draw_panel(mouse_pos):
    pygame.draw.rect(screen, PANEL, (PANEL_X - 12, 0, WIDTH - PANEL_X + 12, HEIGHT))
    draw_text("KNIGHTFALL", PANEL_X, 30, ACCENT, small_font)
    draw_text("Chess", PANEL_X, 48, TEXT, title_font)
    pygame.draw.line(screen, (58, 68, 84), (PANEL_X, 94), (WIDTH - 28, 94), 1)

    # Current turn card
    pygame.draw.rect(screen, PANEL_LIGHT, (PANEL_X, 112, 314, 94), border_radius=14)
    side = "White" if board.turn else "Black"
    side_color = (245, 245, 238) if board.turn else (184, 194, 207)
    pygame.draw.circle(screen, side_color, (PANEL_X + 28, 143), 10)
    draw_text("GAME STATUS", PANEL_X + 48, 126, MUTED, small_font)
    draw_text(status_line(), PANEL_X + 20, 160, CHECK if board.is_check() else TEXT, font)

    draw_text("MOVE HISTORY", PANEL_X, 230, MUTED, small_font)
    pygame.draw.rect(screen, (21, 26, 36), (PANEL_X, 254, 314, 285), border_radius=12)
    sans = list(board.move_stack)
    history_board = chess.Board()
    rows = []
    for i, move in enumerate(sans):
        san = history_board.san(move)
        if i % 2 == 0:
            rows.append([f"{i // 2 + 1}.", san, ""])
            rows[-1][2] = ""
        else:
            rows[-1][2] = san
        history_board.push(move)
    visible = rows[-10:]
    for i, row in enumerate(visible):
        y = 266 + i * 25
        draw_text(row[0], PANEL_X + 14, y, MUTED, small_font)
        draw_text(row[1], PANEL_X + 58, y, TEXT, small_font)
        draw_text(row[2], PANEL_X + 174, y, TEXT, small_font)

    draw_text("CONTROLS", PANEL_X, 559, MUTED, small_font)
    draw_text("Click a piece, then a legal destination.", PANEL_X, 583, TEXT, small_font)
    draw_text("Promotion: choose Q / R / B / N.", PANEL_X, 606, TEXT, small_font)
    draw_text("U = undo   •   R = restart   •   F = flip", PANEL_X, 629, TEXT, small_font)

    button(undo_button, "Undo move", mouse_pos, disabled=not board.move_stack)
    button(restart_button, "New game", mouse_pos)
    button(flip_button, "Flip board", mouse_pos)

    if message and pygame.time.get_ticks() < message_until:
        draw_text(message, PANEL_X, 660, ACCENT, small_font)


def promotion_rects():
    # Four compact promotion options in the center of the board.
    width, height = 390, 126
    x = BOARD_X + (BOARD_SIZE - width) // 2
    y = BOARD_Y + (BOARD_SIZE - height) // 2
    panel = pygame.Rect(x, y, width, height)
    options = []
    for i, (piece_type, label) in enumerate([
        (chess.QUEEN, "Q  Queen"), (chess.ROOK, "R  Rook"),
        (chess.BISHOP, "B  Bishop"), (chess.KNIGHT, "N  Knight")
    ]):
        rect = pygame.Rect(x + 12 + i * 94, y + 55, 86, 54)
        options.append((rect, piece_type, label))
    return panel, options


def draw_promotion(mouse_pos):
    panel, options = promotion_rects()
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 150))
    screen.blit(shade, (0, 0))
    pygame.draw.rect(screen, PANEL, panel, border_radius=14)
    draw_text("PROMOTE YOUR PAWN", panel.x + 18, panel.y + 15, TEXT, font)
    for rect, piece_type, label in options:
        color = BUTTON_HOVER if rect.collidepoint(mouse_pos) else BUTTON
        pygame.draw.rect(screen, color, rect, border_radius=8)
        text_surface = small_font.render(label, True, TEXT)
        screen.blit(text_surface, text_surface.get_rect(center=rect.center))


def begin_selection(square):
    global selected_square, legal_targets
    piece = board.piece_at(square) if square is not None else None
    if piece and piece.color == board.turn and not game_over():
        selected_square = square
        legal_targets = [m.to_square for m in board.legal_moves if m.from_square == square]
    else:
        selected_square = None
        legal_targets = []


def make_move(from_square, to_square, promotion=None):
    global selected_square, legal_targets, message, message_until
    candidates = [m for m in board.legal_moves
                  if m.from_square == from_square and m.to_square == to_square]
    if not candidates:
        return False
    move = candidates[0]
    if move.promotion:
        move = chess.Move(from_square, to_square, promotion=promotion or chess.QUEEN)
    san = board.san(move)
    board.push(move)
    selected_square = None
    legal_targets = []
    message = f"Played {san}"
    message_until = pygame.time.get_ticks() + 1800
    return True


def reset_game():
    global board, selected_square, legal_targets, promotion_pending, message, message_until
    board = chess.Board()
    selected_square = None
    legal_targets = []
    promotion_pending = None
    message = "New game started."
    message_until = pygame.time.get_ticks() + 1800


running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if promotion_pending:
                if event.key == pygame.K_ESCAPE:
                    promotion_pending = None
                else:
                    key_map = {
                        pygame.K_q: chess.QUEEN, pygame.K_r: chess.ROOK,
                        pygame.K_b: chess.BISHOP, pygame.K_n: chess.KNIGHT
                    }
                    if event.key in key_map:
                        make_move(promotion_pending[0], promotion_pending[1], key_map[event.key])
                        promotion_pending = None
            elif event.key == pygame.K_r:
                reset_game()
            elif event.key == pygame.K_f:
                flipped = not flipped
            elif event.key == pygame.K_u and board.move_stack:
                board.pop()
                selected_square = None
                legal_targets = []

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if promotion_pending:
                _, options = promotion_rects()
                for rect, piece_type, _ in options:
                    if rect.collidepoint(event.pos):
                        make_move(promotion_pending[0], promotion_pending[1], piece_type)
                        promotion_pending = None
                        break
                continue

            if undo_button.collidepoint(event.pos):
                if board.move_stack:
                    board.pop()
                    selected_square = None
                    legal_targets = []
            elif restart_button.collidepoint(event.pos):
                reset_game()
            elif flip_button.collidepoint(event.pos):
                flipped = not flipped
            else:
                square = square_from_pos(event.pos)
                if square is not None and not game_over():
                    if selected_square is not None and square in legal_targets:
                        moving_piece = board.piece_at(selected_square)
                        if moving_piece and moving_piece.piece_type == chess.PAWN and chess.square_rank(square) in (0, 7):
                            promotion_pending = (selected_square, square)
                        else:
                            make_move(selected_square, square)
                    else:
                        begin_selection(square)

    screen.fill(BG)
    draw_text("LOCAL TWO-PLAYER • STANDARD CHESS RULES", BOARD_X, 30, MUTED, small_font)
    draw_board()
    draw_panel(mouse_pos)
    if promotion_pending:
        draw_promotion(mouse_pos)
    if game_over():
        # Result banner remains visible after the final move.
        result = board.result(claim_draw=True)
        banner = pygame.Rect(BOARD_X + 95, BOARD_Y + BOARD_SIZE // 2 - 34, BOARD_SIZE - 190, 68)
        pygame.draw.rect(screen, PANEL, banner, border_radius=12)
        pygame.draw.rect(screen, ACCENT, banner, width=2, border_radius=12)
        if board.is_checkmate():
            result_text = f"CHECKMATE — {('Black' if board.turn else 'White')} wins"
        elif result == "1/2-1/2":
            result_text = "DRAW"
        else:
            result_text = f"GAME OVER — {result}"
        label = font.render(result_text, True, TEXT)
        screen.blit(label, label.get_rect(center=banner.center))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
