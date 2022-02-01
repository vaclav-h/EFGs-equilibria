from game_tree import *
import gurobipy as gp
import numpy as np


class Sequence:
    def __init__(self, label="", parent=None, iset=None):
        self.label = label
        self.parent = parent
        self.ext = []
        self.iset = iset

    def extend(self, action, iset):
        new_seq = Sequence(self.label + action, self, iset)
        self.ext.append(new_seq)
        return new_seq

    def __eq__(self, other):
        if other is None:
            return False
        return self.label == other.label

    def __str__(self):
        return self.label


def get_sequences(root, player):
    sequences = []

    def traverse(root, seq, player):
        nonlocal sequences

        actions = root.actions()
        if actions is None:
            return
        for action in actions:
            next1 = root.child(action)
            if root.player == player:
                new_seq = seq.extend(str(action) + str(root.infoset().index()),
                                     root.infoset().index())
                if new_seq not in sequences:
                    sequences.append(new_seq)
                traverse(next1, new_seq, player)
            else:
                traverse(next1, seq, player)

    traverse(root, Sequence(), player)

    return sequences


def get_payoff_matrix(root):
    sequences1 = get_sequences(root, 0)
    sequences2 = get_sequences(root, 1)
    A = np.zeros((len(sequences1) + 1, len(sequences2) + 1))
    i = 0
    j = 0

    def traverse(root, seq1, seq2, chances, chance_prob):
        nonlocal A, i, j, sequences1, sequences2
        actions = root.actions()
        if root.utility() > A[i][j]:
            A[i][j] = root.utility() * (chance_prob ** chances)
        if actions is None:
            return
        for action in actions:
            next1 = root.child(action)
            if root.player == 0:
                new_seq1 = seq1.extend(str(action) + str(root.infoset().index()),
                                       root.infoset().index())
                i = sequences1.index(new_seq1) + 1
                j = sequences2.index(seq2) + 1 if seq2 in sequences2 else 0
                traverse(next1, new_seq1, seq2, chances, chance_prob)
            elif root.player == 1:
                new_seq2 = seq2.extend(str(action) + str(root.infoset().index()),
                                       root.infoset().index())
                i = sequences1.index(seq1) + 1 if seq1 in sequences1 else 0
                j = sequences2.index(new_seq2) + 1
                traverse(next1, seq1, new_seq2, chances, chance_prob)
            elif root.player == 2:
                ch = root.chance_prob(action)
                traverse(next1, seq1, seq2, chances + 1, ch)
            else:
                traverse(next1, seq1, seq2, chances, chance_prob)

    traverse(root, Sequence(), Sequence(), 0, 0)

    return A


def EFG_to_seq(root, player):
    """
    Creates sequence-form representation of the EFG
    
    :param root: root history of the EFG tree
    :param player: zero-indexed player: first player has index 0,
             second player has index 1
    :return: A, B, E, e, F, f as specified in [1]
    """
    sequences1 = get_sequences(root, 0)
    sequences2 = get_sequences(root, 1)

    # Compute E
    isets1 = []
    for seq in sequences1:
        if seq.iset not in isets1:
            isets1.append(seq.iset)
    E = np.zeros((len(isets1) + 1, len(sequences1) + 1))
    E[0][0] = 1
    for (i, iset) in enumerate(isets1):
        for seq in sequences1:
            if seq.iset == iset:
                if seq.parent.label == "":
                    E[i+1][0] = -1
                else:
                    parent_idx = sequences1.index(seq.parent) + 1
                    E[i+1][parent_idx] = -1
                seq_idx = sequences1.index(seq) + 1
                E[i+1][seq_idx] = 1
    # Compute F
    isets2 = []
    for seq in sequences2:
        if seq.iset not in isets2:
            isets2.append(seq.iset)
    F = np.zeros((len(isets2) + 1, len(sequences2) + 1))
    F[0][0] = 1
    for (i, iset) in enumerate(isets2):
        for seq in sequences2:
            if seq.iset == iset:
                if seq.parent.label == "":
                    F[i+1][0] = -1
                else:
                    parent_idx = sequences2.index(seq.parent) + 1
                    F[i+1][parent_idx] = -1
                seq_idx = sequences2.index(seq) + 1
                F[i+1][seq_idx] = 1

    # Compute A, B
    A = get_payoff_matrix(root)
    B = -A

    # e, f
    e = np.zeros((E.shape[0], 1))
    f = np.zeros((F.shape[0], 1))
    e[0][0] = 1
    f[0][0] = 1

    return A, B, E, e, F, f


def root_value(root: History, player: Player) -> float:
    """
    Creates sequence-form LP from supplied EFG tree and solves it.

    :param root: root history of the EFG tree
    :param player: zero-indexed player: first player has index 0,
             second player has index 1
    :return: expected value in the root for given player
    """

    A, B, E, e, F, f = EFG_to_seq(root, player)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag', 0)
        env.start()
        with gp.Model(env=env) as m:
            m.Params.LogToConsole = 0
            if player == 0:
                # PLAYER 1 LP FORMULATION
                p = m.addMVar(e.shape[0])
                y = m.addMVar(A.shape[1])
                m.setObjective(e.T @ p, gp.GRB.MINIMIZE)
                m.addConstr(E.T @ p >= A @ y)
                m.addConstr(F @ y == np.squeeze(f))
                m.addConstr(y >= 0)
            else:
                # PLAYER 2 LP FORMULATION
                p = m.addMVar(f.shape[0], lb=-gp.GRB.INFINITY)
                x = m.addMVar(B.shape[0], lb=-gp.GRB.INFINITY)
                m.setObjective(f.T @ p, gp.GRB.MINIMIZE)
                m.addConstr(F.T @ p >= B.T @ x)
                m.addConstr(E @ x == np.squeeze(e))
                m.addConstr(x >= 0)
            m.optimize()

            return m.objVal

if __name__ == '__main__':
    # read input specification in the body of this function
    root_history = create_root()
    # additionally specify for which player it should be solved
    player = int(input())

    print(root_value(root_history, player))
