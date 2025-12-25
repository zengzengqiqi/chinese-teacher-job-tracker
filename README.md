# Chinese Teacher Job Tracker

An automated tracker for Chinese teacher job postings from major job sites.

## Latest Update

- Date: 2025-12-25
- Jobs found: 1

## About This Repository

This repository automatically tracks Chinese teacher job postings from major international job sites:

- Indeed
- LinkedIn
- Glassdoor
- Monster
- SimplyHired

## Job Criteria

- Position: Chinese/Mandarin Teacher
- Salary: $3,000 minimum (when salary is provided)
- Posted: Within the last 7 days
- Location: Worldwide

## How It Works

A GitHub Actions workflow runs daily to:

1. Scrape job listings from major job sites
2. Filter for positions matching our criteria
3. Save the results as CSV and JSON files
4. Generate a summary report
5. Update this README with the latest count

## Data

The job data is stored in the `data` directory:
- CSV files: Complete dataset in spreadsheet format
- JSON files: Complete dataset in structured format
- Summary files: Markdown reports with key statistics

## License

This project is licensed under the MIT License.
