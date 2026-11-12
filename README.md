# d5data-agent-test — Agent evaluation package audit

[![CI](https://github.com/wzjaiykz/d5data-agent-test/actions/workflows/ci.yml/badge.svg)](https://github.com/wzjaiykz/d5data-agent-test/actions/workflows/ci.yml)

A reproducible audit of the supplied **restaurant-portfolio traffic-change** Agent
evaluation package. The deliverable is [`answer.md`](answer.md); the Python code
exists only to recompute the evidence and pin the findings with tests.

The short version:

- The source ledger is internally consistent: `374→422 (+48)` and `422→481 (+59)`,
  with every portfolio and daypart chain closing.
- All five supplied rollouts are **content-correct** in the required chains, but
  their recorded scores are `0.294 / 0.294 / 0.944 / 0.350 / 1.000`.
- The public rubric and the executable scorer use different weight vectors. About
  40% of the declared weight (R1, R2, R3, R7) is never applied; R5 falls from 25%
  to 5.5576%; R6 rises from 10% to 65%; an undisclosed R9 is 5.9931%.
- A hash shortcut returns frozen rewards for known artifacts instead of
  recomputing them. Correct work is zeroed by exact-name table binding, while an
  empty probe gets R9 credit. The score is not a reliable measure of business
  quality.
- The scorer is not usable as-is: public and effective weights differ, the hash shortcut freezes rewards instead of recomputing, R5/R6 false-negative correct workbooks, and the undisclosed R9 gives an empty shell 1.0 while Gold gets 0.

## What is in the repository

```text
.
├── answer.md                                  # the submission
├── docs/sample-run.log                        # captured CLI output
├── restaurant-portfolio-traffic-change-audit/ # supplied package, unchanged
├── src/audit/
│   ├── ledger.py                              # recomputes source → totals/bridges/dayparts
│   ├── scorer_audit.py                        # parses public/effective weights, R9, frozen ledger
│   └── cli.py                                 # `python -m audit.cli --check`
├── tests/                                     # pytest: 30 tests
├── .github/workflows/ci.yml                   # Python 3.12 + pytest
├── pyproject.toml
├── requirements.txt
└── README.md
```

The supplied package is vendored unchanged so every cell reference in
`answer.md` (for example `餐段归因!L5` or `核对检查!E6`) can be opened and checked.
No API key, network call, model run or semantic judge is required.

## Why this design

- **Audit, not a solution to the restaurant task.** The written test asks for
  evidence review, not a new workbook. The repository therefore keeps the original
  materials and adds a small independent calculator instead of a LangChain-style
  agent. There is no framework to hide the arithmetic.
- **Source first, Gold second.** `ledger.py` reads `materials/` and derives the
  baseline. Gold is used only as a cross-check. This is deliberate: the task says
  not to treat Gold as the only source of truth.
- **Leaf-level checks.** The tests assert the four totals, the six bridge
  components, the six daypart chains, the 12 status boundaries, the 76 original
  values and the exact score algebra. They do not assert that a particular sheet
  name or layout is “right”.
- **The scorer is inspected as evidence.** `scorer_audit.py` parses the public
  `scoring_params.json`, parses the executable weights in
  `fresh_owner_policy.py`, replays the frozen rewards, and runs the real R9
  function. This is how the weight mismatch and the R9 false positive are pinned.

## Reproduce

Requires Python 3.10+ (CI uses 3.12).

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

python -m pip install -e ".[test]"

# independent baseline + score/weight/R9 report
python -m audit.cli --check

# tests
pytest -q
```

On this machine the tests were run with Python 3.12.10 and `openpyxl` 3.1.5.
The full captured CLI output is in [`docs/sample-run.log`](docs/sample-run.log).

## Example output

```text
SOURCE BASELINE (recomputed from the 36 leaf rows, not Gold)
period       base -> current   net    continuing / new / closed       breakfast / lunch / dinner
2023→2024   374 -> 422      +48    +23 (47.9167%) / +89 (185.4167%) / -64 (-133.3333%)    -11 (-22.9167%) / +21 (43.7500%) / +38 (79.1667%)
2024→2025   422 -> 481      +59    +31 (52.5424%) / +79 (133.8983%) / -51 (-86.4407%)    +1 (1.6949%) / +17 (28.8136%) / +41 (69.4915%)

...

DECLARED vs EFFECTIVE WEIGHTS
item   declared   effective
R1       5.000%     0.000%
R2       8.000%     0.000%
R3      18.000%     0.000%
R4      25.000%    23.449%
R5      25.000%     5.558%
R6      10.000%    65.000%
R7       9.000%     0.000%
R8       0.000%     0.000%
R9       0.000%     5.993%
sum effective = 100.000%

UNDISCLOSED R9 FORMULA-DEPENDENCY HEURISTIC
expected_answer.xlsx R9=0.000000 points=[0, 0, 0, 0, 0, 0]
probe-03.xlsx      R9=1.000000 points=[1, 1, 1, 1, 1, 1]
rollout-01.xlsx    R9=1.000000 points=[1, 1, 1, 1, 1, 1]
...
CHECK OK: source closes, Gold hash is frozen, public/effective weights differ as documented.
```

## What the tests cover

`pytest -q` currently reports **30 passed**:

- source totals, 18 leaves per period, status boundaries and zero placeholders;
- bridge and daypart arithmetic with the brand net-change denominator;
- key evidence cells in all five rollouts;
- the 76-value Gold trace and the fact that Gold contains no formulas;
- public-versus-effective weights, frozen hashes, and exact reward replay;
- the R9 shell/Gold false positive and the unused deduction rules;
- the three probes’ controlled defects.

The tests intentionally pin the supplied snapshot. If the package is fixed, some
tests (for example `test_gold_is_static_not_formula_driven` and the R9 assertions)
should fail and force the answer to be updated. That is the point of a regression
suite for an audit.

## Known limitations

- **The scorer snapshot is not a runnable verifier.** `validator.py` imports
  `bound_cache`, a semantic cache and `llm_judge/contract.json`, which are not in
  the package. I did not rerun the semantic judge. The exact cause of a specific
  zero completion is inferred from the frozen `completion` record plus workbook
  content, not from a live replay.
- **No model was rerun.** This is an audit of supplied artifacts, as requested.
- **R2 = 0.947368 for rollouts 04/05 is ambiguous.** The content contains all
  visible original values; the 4/76 shortfall is most consistent with four unbound
  total cells, but without the semantic/table contract I cannot prove which four.
  The answer states this explicitly rather than treating the number as a content
  error.
- **The answer is in English** because the candidate requested English
  deliverables; Chinese sheet names, labels and quoted cells are kept verbatim.
- The supplied package is company material. If it must not be redistributed,
  make the repository private or replace it with a synthetic fixture before
  publishing; the audit code does not require the real company data to run.

## AI disclosure

An AI assistant was used to help structure the answer, write `src/audit/` and the
tests, and check the wording. All numeric claims were independently recomputed
from the source ledger; the score claims are reproduced from
`scorer/frozen_owner_policy.json` and `scorer/fresh_owner_policy.py`. The
assistant was not used as an authority for any business fact. See §0 of
`answer.md` for the full disclosure.

## License

MIT for the audit code and tests. The supplied
`restaurant-portfolio-traffic-change-audit/` package remains the property of its
original author and is included only as the audit fixture.
