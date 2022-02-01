from enum import IntEnum
from typing import List
from copy import deepcopy
from itertools import combinations


class HistoryType(IntEnum):
    decision = 1
    chance = 2
    terminal = 3


class Player(IntEnum):
    agent = 0
    bandit = 1
    chance = 2
    terminal = 3


class Action(IntEnum):
    Up = 1
    Down = 2
    Left = 3
    Right = 4
    Succes = 5
    Fail = 6

    def __str__(self):
        return self.name  # action label


class Infoset:
    def __init__(self, position, history, player, bandits_loc):
        self.position = position
        self.history = history
        self.player = player
        self.bandits_loc = bandits_loc

    def index(self) -> int:
        H = ''
        for action in self.history:
            if action == Action.Up:
                H += 'U'
            elif action == Action.Down:
                H += 'D'
            elif action == Action.Left:
                H += 'L'
            elif action == Action.Right:
                H += 'R'
            elif action == Action.Fail:
                H += 'F'
        H += str(self.position[0])
        H += str(self.position[1])
        if self.player == Player.bandit:
            H += str(self.bandits_loc)
        self.idx = hash(H)
        return self.idx

    def __str__(self):
        return str(self.idx)


class History:
    def __init__(self, maze, start, dest, chance, bandits, dangers, golds):
        self.player = Player.bandit
        self.action_history = []
        self.pos = start
        self.dest = dest
        self.maze = maze
        self.chance = chance
        self.n_bandits = bandits
        self.d_places = dangers
        self.bandit_loc = []
        self.golds = golds
        self.visited = [[False for j in range(len(maze[0]))] for i in range(len(maze))]

    def type(self) -> HistoryType:
        if self.player == Player.chance:
            return HistoryType.chance
        elif self.player == Player.terminal:
            return HistoryType.terminal
        else:
            return HistoryType.decision

    def current_player(self) -> Player:
        return self.player

    # infoset index: histories with the same infoset index belong to the same infoset
    def infoset(self) -> Infoset:
        return Infoset(self.pos, self.action_history, self.player, self.bandit_loc)

    def alarm_triggered(self):
        bandit_moves = 0
        for action in self.action_history:
            if action not in [Action.Up, Action.Down, Action.Left, Action.Right]:
                bandit_moves += 1
            if bandit_moves >= 2:
                return True
        return False

    # Returns list of action availible to the agent
    def get_agent_moves(self):
        actions = []
        if self.maze[self.pos[0]-1][self.pos[1]] != '#' and \
           not self.visited[self.pos[0]-1][self.pos[1]]:
            actions.append(Action.Up)
        if self.maze[self.pos[0]+1][self.pos[1]] != '#' and \
           not self.visited[self.pos[0]+1][self.pos[1]]:
            actions.append(Action.Down)
        if self.maze[self.pos[0]][self.pos[1]-1] != '#' and \
           not self.visited[self.pos[0]][self.pos[1]-1]:
            actions.append(Action.Left)
        if self.maze[self.pos[0]][self.pos[1]+1] != '#' and \
           not self.visited[self.pos[0]][self.pos[1]+1]:
            actions.append(Action.Right)
        return actions

    # Returns possible rellocations of bandits (represented by list of coordinates tuples)
    def get_bandit_moves(self):
        # Initial placement
        if len(self.bandit_loc) == 0:
            return [list(a) for a in list(combinations(self.d_places, self.n_bandits))]
        free_spots = list(set(self.d_places) - set(self.bandit_loc))
        possible_reloc = [self.bandit_loc[:]]
        if len(free_spots) > 0:
            for i in range(len(free_spots)):
                for j in range(len(self.bandit_loc)):
                    new_loc = self.bandit_loc[:]
                    new_loc[j] = free_spots[i]
                    possible_reloc.append(new_loc)
        return possible_reloc

    def actions(self) -> List[Action]:
        if self.player == Player.chance:
            return [Action.Succes, Action.Fail]
        if self.player == Player.agent:
            return self.get_agent_moves()
        if self.player == Player.bandit:
            return self.get_bandit_moves()

    # for player 1
    def utility(self) -> float:
        if Action.Succes in self.action_history:
            return 0
        if self.pos != self.dest:
            return 0
        util = 10
        for gold in self.golds:
            if self.visited[gold[0]][gold[1]]:
                util += 1
        return util

    def chance_prob(self, action: Action) -> float:
        if action == Action.Succes:
            return self.chance
        else:
            return 1 - self.chance

    def child(self, action: Action) -> 'History':
        next = self.clone()
        next.action_history.append(action)
        next.visited[self.pos[0]][self.pos[1]] = True

        # Agent on the move after bandit
        if self.player == Player.bandit:
            next.bandit_loc = action
            next.player = Player.agent
            return next
        # After chance node game ends or agent plays
        if self.player == Player.chance:
            if action == Action.Succes:
                # Ambush succesful
                next.player = Player.terminal
            else:
                # Ambush not succesful
                next.player = Player.agent
                self.n_bandits -= 1
            return next
        # What happens after agent's move
        if self.player == Player.agent:
            # Going UP
            if action == Action.Up:
                next.pos = (self.pos[0]-1, self.pos[1])
            # Going DOWN
            elif action == Action.Down:
                next.pos = (self.pos[0]+1, self.pos[1])
            # Going LEFT
            elif action == Action.Left:
                next.pos = (self.pos[0], self.pos[1]-1)
            # Going RIGHT
            elif action == Action.Right:
                next.pos = (self.pos[0], self.pos[1]+1)
            # Dead End
            if len(next.get_agent_moves()) == 0:
                next.player = Player.terminal
                return next
            # Oops stepped on dangerous place
            if next.pos in self.d_places:
                # Place is occupied by bandit
                if next.pos in self.bandit_loc:
                    next.player = Player.chance
                    return next
                elif not self.alarm_triggered():
                    next.player = Player.bandit
                    return next
            # Next square is the destination
            if next.pos == self.dest:
                next.player = Player.terminal
                return next
            next.player = Player.agent
        return next

    def clone(self) -> 'History':
        return deepcopy(self)

    def __str__(self):
        return ""  # history label


# read the maze from input and return the root node
def create_root() -> History:
    m = int(input())
    n = int(input())
    maze = []
    golds = []
    dangers = []
    for i in range(m):
        line = input()
        maze.append(line)
        if line.find('S') != -1:
            start = (i, line.find('S'))
        if line.find('D') != -1:
            dest = (i, line.find('D'))
        for (j, c) in enumerate(line):
            if c == 'G':
                golds.append((i, j))
            if c == 'E':
                dangers.append((i, j))
    bandits = int(input())
    chance = float(input())
    return History(maze, start, dest, chance, bandits, dangers, golds)


def export_gambit(root_history: History) -> str:
    players = ' '.join([f"\"Pl{i}\"" for i in range(2)])
    ret = f"EFG 2 R \"\" {{ {players} }} \n"

    terminal_idx = 1
    chance_idx = 1

    def build_tree(history, depth):
        nonlocal ret, terminal_idx, chance_idx

        ret += " " * depth  # add nice spacing

        if history.type() == HistoryType.terminal:
            util = history.utility()
            ret += f"t \"{history}\" {terminal_idx} \"\" "
            ret += f"{{ {util}, {-util} }}\n"
            terminal_idx += 1
            return

        if history.type() == HistoryType.chance:
            ret += f"c \"{history}\" {chance_idx} \"\" {{ "
            ret += " ".join([f"\"{str(action)}\" {history.chance_prob(action):.3f}"
                             for action in history.actions()])
            ret += " } 0\n"
            chance_idx += 1

        else:  # player node
            player = int(history.current_player()) + 1  # cannot be indexed from 0
            infoset = history.infoset()
            ret += f"p \"{history}\" {player} {infoset.index()} \"\" {{ "
            ret += " ".join([f"\"{str(action)}\"" for action in history.actions()])
            ret += " } 0\n"

        for action in history.actions():
            child = history.child(action)
            build_tree(child, depth + 1)

    build_tree(root_history, 0)
    return ret


if __name__ == '__main__':
    print(export_gambit(create_root()))
