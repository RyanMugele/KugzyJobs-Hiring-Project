# Applicant selection and NLP matcher tests

Run on November 18, 2026, locally on macOS with Python 3.14.0. All application tests use isolated databases and fictional accounts, with CSRF enabled.

```sh
python -m pytest tests/test_selection_matcher.py -v
python -m pytest -q
```

Focused result: **11 passed in 6.11 seconds**. Seven parameterized score cases and four application integration tests; these 11 are included in the full suite, not additional to its total.

| Test | Expected and observed result |
| --- | --- |
| Complete coverage | 100% |
| One of two skills plus complete style/niche | 75% |
| Skills only offered for a three-category brief | 50% |
| Unrelated offered terms | 0% |
| Requirements contain skills only | One of two skills scores 50%; absent categories renormalized |
| No recognized requirements | 0%, including when editor offers skills |
| Duplicate/case/whitespace normalization | 100%; duplicate terms do not inflate score |
| Two-applicant ranking and selection | 100% applicant ranked above 75%; neither auto-selected; creator chooses 75%; chosen accepted, other pending declined; job in progress; repeat cannot replace editor |
| Pending/rejected portfolio evidence | Removed from comparison: scores drop from 75/100 to 25/50, based only on profile skills |
| Another creator attempts selection | No assignment or application-state change |
| Nonapplicant selected | No assignment; job stays posted |

The integrated example also asserts the actual parser output for “Cinematic travel editing in Premiere Pro with color grading”. Profile skills contribute directly; approved portfolio title/description/tags supply parsed additional evidence. Percentages measure recognized requirement coverage, not predicted hiring success. These are deterministic fictional examples, not a user study or ranking-quality benchmark.

Source: `tests/test_selection_matcher.py`; raw results: `documentation/selection-matcher-tests.txt`; complete regression: `documentation/deployment-tests.txt`.
