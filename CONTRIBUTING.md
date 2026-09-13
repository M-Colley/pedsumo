# Contributing to PedSUMO

Thanks for considering a contribution. PedSUMO is a research tool: results produced with it end up in
papers, so the bar for changes that touch the crossing model is "a reader could reproduce this", not
just "it runs".

The maintenance commitments behind this project (SUMO version tracking, backward compatibility,
review of external contributions) are described in the [Maintenance Plan](README.md#pedsumo-maintenance-plan).

## Getting set up

PedSUMO is run from source, with `SumoWithAVs` as the working directory.

1. Install [Eclipse SUMO](https://eclipse.dev/sumo/) and set `SUMO_HOME`. `traci` and `sumolib` come
   from `$SUMO_HOME/tools`, which `main.py` adds to `sys.path`.
2. Install the Python dependencies:

   ```console
   pip install -r requirements.txt
   ```

   A headless run (`--nogui`) needs only `sumolib` plus SUMO itself; `PySide6`, `screeninfo` and
   `matplotlib` are imported lazily and are only required when a GUI is shown.
   The LLM crossing model additionally needs `pip install -r requirements_llm.txt`.
3. Run the tests from the repository root:

   ```console
   python -m unittest discover -v
   ```

The tests stub `traci`, `sumolib` and the GUI, so they need neither a SUMO installation nor a display
and finish in well under a second. If a change makes them slow, something is being imported that
should not be.

## Before opening a pull request

- **Run the tests**, and add one for the behaviour you changed or fixed. Tests live in
  `tests/test_main_logic.py`.
- **Keep runs reproducible.** This is the constraint that is easiest to break by accident and the
  hardest to notice. See the section below.
- **Use `os.path.join`** for every path, and never assume a separator. The repository is developed on
  Windows and tested on Linux, Windows and macOS.
- **Do not import optional dependencies at module level.** `transformers` and `torch` cost tens of
  seconds to import and are only needed for `--prob_computation llm`; the GUI stack needs a display.
- **Catch specific exceptions.** A bare `except:` also swallows `KeyboardInterrupt` and hides the
  cause of missing result rows.

CI runs the unit tests on Linux, Windows and macOS across Python 3.11-3.13, builds the distribution,
and runs a short headless simulation twice to check that the results are reproducible.

## Reproducibility

A PedSUMO run must be a function of its parameters and its `--seed`, and of nothing else.

The trap: CPython randomises string hashing per process, so iterating a `set` of SUMO IDs yields a
different order in every run. Because the model draws a random number per vehicle and per pedestrian
in iteration order, iterating a set silently makes results irreproducible even with a fixed seed —
this was a real bug, and identical configurations produced different crossing probabilities from one
run to the next.

So: **whenever iteration order can influence a random draw, a returned value, or a sum, iterate in
sorted order.** `sorted(some_set)` is enough. The places this already applies are marked with a
comment in `main.py`.

You can check a change locally by running the same configuration under two different hash seeds and
diffing the results, ignoring the `timestamp` column:

```console
PYTHONHASHSEED=1 python main.py --nogui --scenario Small_Test_Network --time_steps 300 --seed 42
PYTHONHASHSEED=2 python main.py --nogui --scenario Small_Test_Network --time_steps 300 --seed 42
```

The two `probabilities-*.csv` files must be identical apart from the timestamps. CI performs exactly
this check.

Use `--seed` to produce independent replications of the same configuration; the seed is recorded in
the `random_seed` column of every results file.

## Changing the crossing model

Parameters of the behavioural model belong in `config.py`, not inline in `main.py`, and every
parameter is written to the results CSV so that a run can be reconstructed from its output alone. If
you add a parameter, add it to the CSV header and row as well.

If you change what a defiance factor means, say so in the pull request and cite the source, the same
way the existing factors reference the literature they come from.

## Reporting bugs

Please open a [GitHub issue](https://github.com/M-Colley/pedsumo/issues) including:

- your SUMO version (`sumo --version`), Python version and operating system,
- the scenario and the exact command line you ran,
- what you expected and what happened.

Scenario-specific problems (no pedestrians appear, the simulation stalls) are often configuration
rather than code: the [Quick Advice](README.md#quick-advice) section covers the common cases.

## License

By contributing you agree that your contribution is licensed under the [MIT License](LICENSE).
