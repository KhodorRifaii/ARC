# Project inspection

## Fixed defects

1. **Candidate verification:** scaling and tiling were accepted without matching the first demonstration. Every inferred program now reproduces every demonstration, including the first.
2. **Color inference:** mappings were inferred from only the first example and unnecessarily required a one-to-one permutation. Mappings now combine all demonstrations and permit multiple colors to map to the same output color.
3. **Geometry search:** the transformation list contained duplicates. It now uses eight stable dihedral operations, including on symmetric inputs.
4. **Scaling and tiling:** scaling unnecessarily required equal vertical and horizontal factors; tiling used an absolute output size. Both now use independent relative factors.
5. **Unsafe crops:** a fixed crop could produce empty or truncated grids on smaller test inputs. Such candidates are rejected at prediction time.
6. **Dead gravity code:** an unreachable operation could erase unrelated colors. Removed rather than representing it as a supported capability.
7. **Submission validation:** the previous checks were temporary shell snippets and did not enforce rectangular grids or dimensions. A reusable validator now enforces task IDs, test counts, exactly two attempts, rectangular dimensions from 1 to 30, and integer colors from 0 to 9. Generation validates before writing.
8. **Misleading evaluation claim:** the purported task holdout was only a random subset of the same LOO calculation after development on the full training collection. Removed this metric and its claim of independent generalization.
9. **Label-loading description:** previous code loaded evaluation labels before prediction despite comments saying otherwise. Predictions now finish before solution files are opened. Only the scorer loads labels.
10. **Missing notebook:** previous updates promised an offline notebook without creating one. A self-contained notebook is now provided, embedding only the solver and validator.
11. **Reproducibility:** saved metrics now include the solver SHA-256 and elapsed scoring time. Original code is preserved in `audit/`.

## Improvements

Added crops based on foreground bounding boxes and largest/smallest monochromatic components. Background can be a specified color or the most frequent input color. Added geometry/object selection followed by a color map inferred jointly from demonstrations. No evaluation targets were used to author these rules.

## Measured results

| Measurement | Previous | Revised |
| --- | ---: | ---: |
| Training LOO correct outputs | 94/3,232 (2.91%) | 118/3,232 (3.65%) |
| Training test outputs | Not previously measured | 43/1,076 (4.00%) |
| Evaluation test outputs | 0/172 | 0/172 |
| Fully solved evaluation tasks | 0/120 | 0/120 |

The previous results come from the recorded pre-audit run; the original implementation is preserved for reproduction. Revised metrics are in `outputs/metrics.json`. This improvement is modest and does not demonstrate improved ARC-AGI-2 evaluation performance. The evaluation set has already been scored repeatedly and is a monitored development benchmark, not a pristine final holdout.

## Data findings

All 240 downloadable test tasks are byte-structure-equivalent JSON objects to tasks in the training challenge collection. None shares an ID with public evaluation. This overlap is recorded in `outputs/data_audit.json`; it is not used to look up answers. Neither known training solutions nor evaluation solutions are imported by the solver. Downloaded test-file success cannot establish performance on Kaggle's hidden replacement inputs.

## Validation

Seven regression tests cover candidate consistency, joint color inference, stable geometry indices, crop bounds, invalid grids, missing outputs, and relative tiling. The generated submission passes strict validation for 240 tasks, 259 test outputs, and 518 grids. The notebook is also executed locally with only its filesystem paths adapted, and its predictions compared to CLI predictions. This does not verify Kaggle's actual execution environment.

## Remaining limitations

- Evaluation accuracy is zero; the project is not competitive or ready for a performance-oriented submission.
- Search covers a small set of operations and shallow compositions. It lacks broad spatial reasoning, relational object inference, iterative rule search, and learned reasoning.
- Exact-fitting programs use deterministic catalog order without calibrated confidence. An unseen color defaults to itself; this is a hypothesis, not learned evidence.
- When no program fits, guesses still copy demonstration outputs. This is explicitly a weak fallback, not successful inference.
- Object extraction uses same-color components and can miss multicolor objects. Fixed crops can overfit demonstration positions.
- Existing shape-safe operations can still be semantically wrong on novel inputs. Passing format validation says nothing about correctness of those predictions.
- Kaggle Version 1 subsequently completed successfully in 29.4 seconds with Internet off; see `outputs/kaggle_run.json`. No hidden leaderboard evaluation, competition submission, or rule-eligibility audit was performed.
- The inspection and regression suite are finite; they do not establish absence of every possible defect.

The next substantive research step is a richer object/program search with a development split fixed before tuning and a fresh independent benchmark for final validation. Adding more operations must be justified by measured generalization, not by copying known answers.

## Follow-up code review

Removed the unused first-demonstration color-map implementation: inference discarded it and used the correct joint mapping implementation instead. Removed blanket exception swallowing in box-fill candidate search so unexpected defects surface during evaluation. Fixed the public prediction API to reject attempt counts other than two. Added a reproducible notebook build script and a regression test that compares its embedded modules to current source. Strengthened the invalid scaling/tiling regression with explicit rejection checks.

Nine regression tests pass. All 259 downloadable test predictions remain identical to the previous artifact. These are maintenance changes, not new reasoning capabilities. The deployed Kaggle Version 1 still contains the prior source; it has not been replaced by this review.

Remaining priorities: broader program composition and multicolor object reasoning; evidence-based candidate ranking; replacing copied-output fallback guesses; a genuinely reserved benchmark before further tuning; and explicit validation of malformed challenge inputs. Those are not solved by notebook format compliance.

The follow-up full scoring run completed in 50.96 seconds: training LOO 118/3,232, training test outputs 43/1,076, and evaluation 0/172, unchanged. Its source hash is recorded in `outputs/metrics.json`.
