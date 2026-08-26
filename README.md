# Design of Experiments

BMSTU IU7, semester 8.

Queueing system simulation driving a regression model: each lab runs the same
simulated queue under a different experimental design and fits a polynomial to
the response surface. GUI in PyQt6, plots in matplotlib.

## Structure

| Path                            | Topic                                          |
|---------------------------------|------------------------------------------------|
| `lab-01-queueing-simulation`    | Single-channel queue with priorities           |
| `lab-02-full-factorial`         | Full factorial design, 2^6                     |
| `lab-03-fractional-factorial`   | Fractional factorial design                    |
| `lab-04-orthogonal-ccd`         | Orthogonal central composite design            |

Every lab keeps the same layout: `simulation.py` for the queue model,
`regression.py` for fitting, `constants.py` for parameters and styles, `gui/`
for the PyQt6 windows, `docs/` for theory notes and assignment.

## Run

```sh
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cd lab-02-full-factorial && python main.py
```

## Stack

Python, NumPy, matplotlib, PyQt6
