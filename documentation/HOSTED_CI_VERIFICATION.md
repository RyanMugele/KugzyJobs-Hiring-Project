# Hosted GitHub Actions verification

Verified on 23 November 2026 for commit `6907cc08d03aba736801ce034602cd8244aacb0e`.

[Successful run](https://github.com/RyanMugele/KugzyJobs-Hiring-Project/actions/runs/45125726691)

The Ubuntu workflow completed dependency installation, all 49 pytest cases, the 20-case NLP evaluation and the 15-description CSV evaluation successfully. This verifies the source release on Linux; a live Render deployment and hosted persistence remain separate checks.

Hosted pytest result: **49 passed in 16.92s**. This is suite execution time, not page latency.

## Password reset update

Commit `dd015d6ffd1182c9c5c43b915d74e26dbac033a9` passed [Linux run 45131900430](https://github.com/RyanMugele/KugzyJobs-Hiring-Project/actions/runs/45131900430) on 23 November 2026: **56 passed in 17.28s**, plus NLP and CSV evaluations. Seven new cases cover email submission and password recovery. SMTP is mocked in CI; live inbox receipt was separately confirmed by the owner.
