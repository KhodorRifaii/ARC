# ARC Prize 2026: ARC-AGI-2

Inspected symbolic solver reconstructed from the supplied competition ZIP. Read [INSPECTION.md](INSPECTION.md) for fixed defects, evidence, and remaining limitations.

## Run locally

Python 3.9+; standard library only. Run from the project root:

```sh
python3 -m unittest discover -s tests -v
python3 src/score.py
python3 src/arc_solver.py
python3 src/validate.py data/arc-agi_test_challenges.json outputs/submission.json
```

The scorer writes `outputs/metrics.json`; generation writes `outputs/submission.json`. Override input/output paths using `--challenges` and `--output`. Generation validates all output grids before writing. Baseline code is preserved under `audit/`.

## Performance

Training LOO: **118/3,232 (3.65%)**, up from 94. Training test outputs: **43/1,076 (4.00%)**. Public evaluation: **0/172 outputs and 0/120 fully solved tasks**. The solver remains weak and is not competitive. Prior claims that the random LOO subset constituted independent task holdout evaluation were incorrect and have been removed.

## Data boundary

The solver reads demonstrations and test inputs only. Only the local scorer reads solution files, after completing predictions. Evaluation solutions never construct test predictions. All downloadable test tasks overlap with training tasks; this overlap is not used for answer lookup and cannot demonstrate hidden-test generalization.

## Kaggle artifact

`notebooks/arc_submission.ipynb` embeds the solver and validator and writes `/kaggle/working/submission.json`. Attach competition data and disable Internet. It requires no package downloads. The notebook has been checked locally using adapted paths; it has not been executed or submitted on Kaggle. Rebuild its embedded source if the solver changes.
