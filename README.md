# EFGs-equilibria


Solution to an assignmnet from Computational Game Theory course.

Finds Nash Equilibrium strategy in an extensive form game by first converting it to the sequence form and then solving linear program.
The sequence form is specified in [1].

* `game_tree.py` reads a game specification and outputs the game representation in a format compatible with [Gambit](http://www.gambit-project.org/).
* `game_lp.py` reads a game specification and outputs the value of the game for a given player. Linear program is solved using the [Gurobi optimizer](https://www.gurobi.com/). Solves any game following the interface given in `game_tree.py`.

## References:
[1] Koller, Daphne et al. “Efficient Computation of Equilibria for Extensive Two-Person Games.” Games and Economic Behavior 14 (1996): 247-259.

[2] Assignment specification: https://cw.fel.cvut.cz/wiki/_media/courses/cgt/efg2021.pdf
