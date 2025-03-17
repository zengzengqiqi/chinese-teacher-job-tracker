# Initial Setup

This file ensures that the data directory is properly created and tracked in git.

Daily job data will be saved in this directory in the following formats:
- `chinese_teacher_jobs_YYYY-MM-DD.csv` - Complete dataset in CSV format
- `chinese_teacher_jobs_YYYY-MM-DD.json` - Complete dataset in JSON format
- `summary_YYYY-MM-DD.md` - Summary with statistics and highlights

The first automated job search will be executed when the workflow runs.
