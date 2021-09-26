import random
from discord_slash.utils import manage_components
from discord_slash.model import ButtonStyle


class TicTacToe:
    def __init__(self):
        self.board = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.blanks = 9
        self.game_over = False

    def __str__(self):
        return (f"{self.board[0]} | {self.board[1]} | {self.board[2]}\n"
                f"----------\n"
                f"{self.board[3]} | {self.board[4]} | {self.board[5]}\n"
                f"----------\n"
                f"{self.board[6]} | {self.board[7]} | {self.board[8]}")

    def update(self, player=None, i=None, full_board=None):
        if self.game_over:
            raise ValueError("Game already over.")
        if i is not None and player is not None:
            if not self.is_blank(i):
                raise ValueError("Board is not empty at i=" + str(i))
            self.board[i] = player
            self.blanks -= 1
        elif full_board is not None:
            for i in range(len(full_board)):
                if full_board[i] == "0":
                    self.blanks += 1
                self.update(int(full_board[i:i+1]), i=i)
        elif player is None:
            raise ValueError("player value missing from function call.")
        else:
            raise ValueError("Too many arguments.")
        if self.blanks == 0:
            self.game_over = True
        if not self.check_win() == -1:
            self.game_over = True

    def copy(self):
        new_obj = TicTacToe()
        new_obj.board = self.board.copy()
        new_obj.blanks = self.blanks
        return new_obj

    def is_blank(self, index: int):
        return self.board[index] == 0

    def check_win(self):
        if check_win(self, 1):
            return 1
        if check_win(self, 2):
            return 2
        return -1

    def get_buttons(self, force_stop=False):
        buttons = []
        for i in range(9):
            buttons.append(
                manage_components.create_button(
                    style=[ButtonStyle.grey, ButtonStyle.blue, ButtonStyle.red][self.board[i]],
                    label=" ",
                    custom_id=f"tictactoe_{i}",
                    disabled=self.board[i] > 0 or self.game_over or force_stop
                )
            )
        buttons.append(manage_components.create_button(
            style=ButtonStyle.green,
            label="Restart game",
            custom_id="tictactoe_restart"
        ))
        buttons.append(manage_components.create_button(
            style=ButtonStyle.red,
            label="Stop game",
            custom_id="tictactoe_stop"
        ))
        actionrows = manage_components.spread_to_rows(*buttons, max_in_row=3)
        return actionrows

    def get_string(self):
        st = ""
        for i in range(9):
            st += str(self.board[i])
        return st


def check_win(board: TicTacToe, player: int):
    consecutive = 0
    for x in range(3):
        for y in range(3):
            if board.board[3 * y + x] == player:
                consecutive += 1
        if consecutive == 3:
            # print("vertical")
            return True
        consecutive = 0
    for x in range(3):
        for y in range(3):
            if board.board[3 * x + y] == player:
                consecutive += 1
        if consecutive == 3:
            # print("horizontal")
            return True
        consecutive = 0
    for n in range(3):
        if board.board[4*n] == player:
            consecutive += 1
    if consecutive == 3:
        # print("top-left diag")
        return True
    consecutive = 0
    for n in range(3):
        if board.board[(n+1)*2] == player:
            consecutive += 1
    if consecutive == 3:
        # print("top-right diag")
        return True
    return False


def compute_step(board: TicTacToe, player: int):
    if check_win(board, player):
        return None
    elif check_win(board, 1 if player == 2 else 2):
        return None
    elif board.blanks == 0:
        return None
    winning_moves = find_vacancy(board, player)  # check if CPU can win
    if len(winning_moves) > 0:
        return winning_moves[0]
    opponent_moves = find_vacancy(board, 1 if player == 2 else 2)  # block enemy from winning
    if len(opponent_moves) > 0:
        return opponent_moves[0]
    future_wins = find_vacancy(board, player, 2)
    best_moves = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    for i in future_wins:
        best_moves[i] += 1
    if max(best_moves) > 0:
        return best_moves.index(max(best_moves))
    x = list(range(9))
    random.shuffle(x)
    for i in x:
        if board.is_blank(i):
            return i


def find_vacancy(board: TicTacToe, player: int, free_slots=1):
    vacant = []
    # check rows:
    for i in range(0, 9, 3):
        row = ""
        for j in range(3):
            row += str(board.board[i+j])
        if row.count(str(1 if player == 2 else 2)) > 0:  # check if opponent played this row
            continue
        if not row.count("0") == free_slots:  # check free slots
            continue
        for j in range(3):
            if row[j] == "0":
                vacant.append(i+j)
    for i in range(3):
        column = ""
        for j in range(0, 9, 3):
            column += str(board.board[i+j])
        if column.count(str(1 if player == 2 else 2)) > 0:  # check if opponent played this column
            continue
        if not column.count("0") == free_slots:  # check free slots
            continue
        for j in range(3):
            if column[j] == "0":
                vacant.append(i+(j*3))
    diag1 = ""
    for i in [0, 4, 8]:
        diag1 += str(board.board[i])
    if not diag1.count(str(1 if player == 2 else 2)) > 0:  # check if opponent played this diagonal
        if diag1.count("0") == free_slots:  # check free slots
            for i in range(3):
                if diag1[i] == "0":
                    vacant.append([0, 4, 8][i])
    diag2 = ""
    for i in [2, 4, 6]:
        diag2 += str(board.board[i])
    if not diag2.count(str(1 if player == 2 else 2)) > 0:  # check if opponent played this diagonal
        if diag2.count("0") == free_slots:  # check free slots
            for i in range(3):
                if diag2[i] == "0":
                    vacant.append([2, 4, 6][i])
    vacant.sort()
    return vacant


def numpad_input(prompt: str):
    x = input(prompt)
    try:
        x = int(x)
        if not 1 <= x <= 9:
            raise Exception()
    except Exception:
        raise ValueError("Input was not a valid number.")
    else:
        matrix = [7, 8, 9, 4, 5, 6, 1, 2, 3]
        return matrix.index(x)
