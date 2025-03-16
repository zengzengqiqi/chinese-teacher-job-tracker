# Setup Instructions

This document provides instructions for setting up and running the Chinese Teacher Job Tracker.

## Prerequisites

1. Python 3.8 or higher
2. Git
3. GitHub account

## Manual Setup

### Clone the Repository

```bash
git clone https://github.com/zengzengqiqi/chinese-teacher-job-tracker.git
cd chinese-teacher-job-tracker
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Scraper Manually

```bash
python job_scraper.py
```

## GitHub Actions Setup

The repository is already configured to run the job scraper daily using GitHub Actions. The workflow will:

1. Run automatically at 2 AM UTC every day
2. Scrape job listings from 5 major job sites
3. Filter for Chinese teacher positions with salaries ≥ $3000 posted in the last week
4. Save the results as CSV and JSON files
5. Generate a summary report
6. Commit and push the changes back to the repository

You can also manually trigger the workflow from the "Actions" tab on the GitHub repository page:

1. Go to the repository on GitHub
2. Click on the "Actions" tab
3. Select the "Job Scraper" workflow
4. Click "Run workflow"
5. Confirm by clicking "Run workflow" again

## Customization

### Modify Job Criteria

To change the job search criteria, edit the `job_scraper.py` file:

- Change the minimum salary: Modify the `self.min_salary = 3000` line
- Change the job title filter: Modify the `meets_criteria()` method
- Change the date range: Modify the `self.date_threshold` value

### Add More Job Sites

To add more job sites:

1. Create a new method in the `JobScraper` class (e.g., `scrape_new_site()`)
2. Implement the scraping logic for the new site
3. Add a call to your new method in the `run_all_scrapers()` method

## Troubleshooting

### Common Issues

1. **Rate limiting/blocking**: Job sites may block frequent requests. Try increasing the delay between requests or using a proxy service.
2. **HTML structure changes**: Job sites may change their HTML structure. If scraping stops working, check the selectors and update them accordingly.
3. **Missing data directory**: If you see errors about the data directory, make sure it exists: `mkdir -p data`

### Logs

GitHub Actions logs can be viewed in the Actions tab of the repository. These logs can help diagnose issues with the automated workflow.
