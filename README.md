# Chinese Teacher Job Tracker

An automated system for tracking Chinese teacher job postings from major international job sites.

## Latest Update

- Initial setup: March 17, 2025
- First data collection will begin automatically

## About This Repository

This repository automatically tracks Chinese teacher job postings from 5 major international job sites:

- Indeed
- LinkedIn
- Glassdoor
- Monster
- SimplyHired

## Job Criteria

- Position: Chinese/Mandarin Teacher
- Salary: $3,000 minimum (when salary is provided)
- Posted: Within the last 7 days
- Location: Worldwide (no location restrictions)

## How It Works

A GitHub Actions workflow runs daily at 2 AM UTC to:

1. Scrape job listings from the five major job sites
2. Filter for positions matching our criteria
3. Save the results as CSV and JSON files
4. Generate a summary report in Markdown format
5. Update this README with the latest count

## Data Storage

The job data is stored in the `data` directory:
- CSV files: Complete dataset in spreadsheet format (daily)
- JSON files: Complete dataset in structured format (daily)
- Summary files: Markdown reports with key statistics and highlights

## How to Use This Repository

### View Latest Job Data
- Check the `data` directory for the most recent files
- Review the summary Markdown file for highlights and key statistics

### Run the Scraper Manually
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the script: `python job_scraper.py`

### Modify the Scraper
If you want to customize the scraper:
1. Fork this repository
2. Modify `job_scraper.py` to change criteria or add job sites
3. Update the GitHub Actions workflow if needed

## License

This project is licensed under the MIT License.
