import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import time
import random
import json
import os
import re

class JobScraper:
    def __init__(self):
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.results = []
        self.min_salary = 3000  # Minimum salary in USD
        self.date_threshold = datetime.datetime.now() - datetime.timedelta(days=7)
        
        # User agent rotation to avoid being blocked
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
        ]
    
    def get_headers(self):
        """Rotate user agents to avoid scraping detection"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
    
    def extract_salary_value(self, salary_text):
        """Extract numerical salary value from text"""
        if salary_text == "N/A":
            return 0
        
        # Remove non-numeric characters except for digits, comma, dot, and hyphen
        salary_text = re.sub(r'[^\d,.\-]', '', salary_text)
        
        # Handle ranges by taking the lower value
        if '-' in salary_text:
            salary_text = salary_text.split('-')[0]
        
        # Remove commas and convert to float
        salary_text = salary_text.replace(',', '')
        
        # Try to extract a valid number
        matches = re.findall(r'\d+', salary_text)
        if matches:
            return float(matches[0])
        return 0
    
    def check_salary_threshold(self, salary_text):
        """Check if salary meets the minimum threshold"""
        if salary_text == "N/A":
            return True  # Include jobs without salary info
        
        value = self.extract_salary_value(salary_text)
        
        # If we have a value and it's below threshold, exclude
        if value > 0 and value < self.min_salary:
            return False
        return True
    
    def meets_criteria(self, title, salary):
        """Check if job meets our criteria"""
        # Check if it's a Chinese teacher position
        if 'chinese' not in title.lower() and 'mandarin' not in title.lower():
            return False
            
        # Check salary requirement
        if not self.check_salary_threshold(salary):
            return False
            
        return True
    
    def scrape_indeed(self):
        """Scrape Chinese teacher jobs from Indeed"""
        print("Scraping Indeed...")
        try:
            for page in range(0, 3):  # Check first 3 pages
                url = f"https://www.indeed.com/jobs?q=chinese+teacher+${self.min_salary}&sort=date&fromage=7&start={page*10}"
                response = requests.get(url, headers=self.get_headers())
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    job_cards = soup.select('div.job_seen_beacon')
                    
                    if not job_cards:
                        job_cards = soup.select('div.jobsearch-SerpJobCard')
                    
                    for job in job_cards:
                        try:
                            # Extract job title
                            title_elem = job.select_one('h2.jobTitle') or job.select_one('a.jobtitle')
                            if not title_elem:
                                continue
                                
                            title = title_elem.get_text().strip()
                            
                            # Extract company
                            company_elem = job.select_one('span.companyName') or job.select_one('span.company')
                            company = company_elem.get_text().strip() if company_elem else "N/A"
                            
                            # Extract location
                            location_elem = job.select_one('div.companyLocation') or job.select_one('div.recJobLoc')
                            location = location_elem.get_text().strip() if location_elem else "N/A"
                            
                            # Extract salary
                            salary_elem = job.select_one('div.metadata.salary-snippet-container') or job.select_one('span.salaryText')
                            salary = salary_elem.get_text().strip() if salary_elem else "N/A"
                            
                            # Extract job link
                            link_elem = job.select_one('a[id^="job_"]') or job.select_one('a.jobtitle')
                            job_link = "https://www.indeed.com" + link_elem['href'] if link_elem else "N/A"
                            
                            # Check if job meets criteria
                            if self.meets_criteria(title, salary):
                                self.results.append({
                                    'title': title,
                                    'company': company, 
                                    'location': location,
                                    'salary': salary,
                                    'date_posted': 'Within last 7 days',
                                    'job_link': job_link,
                                    'source': 'Indeed'
                                })
                                
                        except Exception as e:
                            print(f"Error parsing Indeed job: {e}")
                            continue
                    
                    # Avoid aggressive scraping
                    time.sleep(random.uniform(2, 5))
                else:
                    print(f"Failed to retrieve Indeed page {page}: Status code {response.status_code}")
                
        except Exception as e:
            print(f"Error scraping Indeed: {e}")
    
    def scrape_linkedin(self):
        """Scrape Chinese teacher jobs from LinkedIn"""
        print("Scraping LinkedIn...")
        try:
            url = "https://www.linkedin.com/jobs/search/?keywords=chinese%20teacher&f_TPR=r604800"
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.select('div.base-card')
                
                for job in job_cards:
                    try:
                        # Extract job title
                        title_elem = job.select_one('h3.base-search-card__title')
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text().strip()
                        
                        # Extract company
                        company_elem = job.select_one('h4.base-search-card__subtitle')
                        company = company_elem.get_text().strip() if company_elem else "N/A"
                        
                        # Extract location
                        location_elem = job.select_one('span.job-search-card__location')
                        location = location_elem.get_text().strip() if location_elem else "N/A"
                        
                        # LinkedIn doesn't always show salary on search page
                        salary = "Check job details"
                        
                        # Extract job link
                        link_elem = job.select_one('a.base-card__full-link')
                        job_link = link_elem['href'] if link_elem else "N/A"
                        
                        # Check if job meets criteria
                        if self.meets_criteria(title, salary):
                            self.results.append({
                                'title': title,
                                'company': company, 
                                'location': location,
                                'salary': salary,
                                'date_posted': 'Within last 7 days',
                                'job_link': job_link,
                                'source': 'LinkedIn'
                            })
                            
                    except Exception as e:
                        print(f"Error parsing LinkedIn job: {e}")
                        continue
                
                # Avoid aggressive scraping
                time.sleep(random.uniform(2, 5))
                
            else:
                print(f"Failed to retrieve LinkedIn jobs: Status code {response.status_code}")
                
        except Exception as e:
            print(f"Error scraping LinkedIn: {e}")
    
    def scrape_glassdoor(self):
        """Scrape Chinese teacher jobs from Glassdoor"""
        print("Scraping Glassdoor...")
        try:
            url = "https://www.glassdoor.com/Job/chinese-teacher-jobs-SRCH_KO0,15.htm"
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.select('li.react-job-listing')
                
                for job in job_cards:
                    try:
                        # Extract job data from data attributes
                        job_title = job.get('data-normalize-job-title', 'N/A')
                        employer_name = job.get('data-employer-name', 'N/A')
                        location = job.get('data-job-loc', 'N/A')
                        
                        # Extract salary
                        salary_elem = job.select_one('span.salary-estimate')
                        salary = salary_elem.get_text().strip() if salary_elem else "N/A"
                        
                        # Extract date posted
                        date_elem = job.select_one('div.listing-age')
                        date_posted = date_elem.get_text().strip() if date_elem else "N/A"
                        
                        # Check if job was posted within last week
                        if date_posted != "N/A" and "d" in date_posted:
                            days_ago = int(''.join(filter(str.isdigit, date_posted)))
                            if days_ago > 7:
                                continue
                        
                        # Extract job link
                        link_elem = job.select_one('a.jobLink')
                        job_link = "https://www.glassdoor.com" + link_elem['href'] if link_elem else "N/A"
                        
                        # Check if job meets criteria
                        if self.meets_criteria(job_title, salary):
                            self.results.append({
                                'title': job_title,
                                'company': employer_name, 
                                'location': location,
                                'salary': salary,
                                'date_posted': date_posted,
                                'job_link': job_link,
                                'source': 'Glassdoor'
                            })
                            
                    except Exception as e:
                        print(f"Error parsing Glassdoor job: {e}")
                        continue
                    
                # Avoid aggressive scraping
                time.sleep(random.uniform(2, 5))
                
            else:
                print(f"Failed to retrieve Glassdoor jobs: Status code {response.status_code}")
                
        except Exception as e:
            print(f"Error scraping Glassdoor: {e}")
    
    def scrape_monster(self):
        """Scrape Chinese teacher jobs from Monster"""
        print("Scraping Monster...")
        try:
            url = "https://www.monster.com/jobs/search?q=Chinese+Teacher&saltyp=1&salary=3000&where=&page=1&so=date.desc"
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.select('div.job-cardstyle__JobCardComponent')
                
                for job in job_cards:
                    try:
                        # Extract job title
                        title_elem = job.select_one('h3.job-cardstyle__JobTitle')
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text().strip()
                        
                        # Extract company
                        company_elem = job.select_one('span.job-cardstyle__CompanyName')
                        company = company_elem.get_text().strip() if company_elem else "N/A"
                        
                        # Extract location
                        location_elem = job.select_one('span.job-cardstyle__Location')
                        location = location_elem.get_text().strip() if location_elem else "N/A"
                        
                        # Extract date posted
                        date_elem = job.select_one('span.job-cardstyle__JobAge')
                        date_posted = date_elem.get_text().strip() if date_elem else "N/A"
                        
                        # Check if job was posted within last week
                        if date_posted != "N/A" and "d" in date_posted:
                            days_ago = int(''.join(filter(str.isdigit, date_posted)))
                            if days_ago > 7:
                                continue
                        
                        # Extract job link
                        link_elem = job.select_one('a')
                        job_link = link_elem['href'] if link_elem else "N/A"
                        
                        # Check if job meets criteria
                        if self.meets_criteria(title, f"Min ${self.min_salary}"):
                            self.results.append({
                                'title': title,
                                'company': company, 
                                'location': location,
                                'salary': f"Min ${self.min_salary}",
                                'date_posted': date_posted,
                                'job_link': job_link,
                                'source': 'Monster'
                            })
                            
                    except Exception as e:
                        print(f"Error parsing Monster job: {e}")
                        continue
                    
                # Avoid aggressive scraping
                time.sleep(random.uniform(2, 5))
                
            else:
                print(f"Failed to retrieve Monster jobs: Status code {response.status_code}")
                
        except Exception as e:
            print(f"Error scraping Monster: {e}")
    
    def scrape_simplyhired(self):
        """Scrape Chinese teacher jobs from SimplyHired"""
        print("Scraping SimplyHired...")
        try:
            url = "https://www.simplyhired.com/search?q=chinese+teacher&fdb=7"  # fdb=7 means last 7 days
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.select('div.SerpJob-jobCard')
                
                for job in job_cards:
                    try:
                        # Extract job title
                        title_elem = job.select_one('h3.jobposting-title')
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text().strip()
                        
                        # Extract company
                        company_elem = job.select_one('span.jobposting-company')
                        company = company_elem.get_text().strip() if company_elem else "N/A"
                        
                        # Extract location
                        location_elem = job.select_one('span.jobposting-location')
                        location = location_elem.get_text().strip() if location_elem else "N/A"
                        
                        # Extract salary
                        salary_elem = job.select_one('div.jobposting-salary')
                        salary = salary_elem.get_text().strip() if salary_elem else "N/A"
                        
                        # Extract job link
                        link_elem = job.select_one('a')
                        job_link = "https://www.simplyhired.com" + link_elem['href'] if link_elem else "N/A"
                        
                        # Check if job meets criteria
                        if self.meets_criteria(title, salary):
                            self.results.append({
                                'title': title,
                                'company': company, 
                                'location': location,
                                'salary': salary,
                                'date_posted': 'Within last 7 days',
                                'job_link': job_link,
                                'source': 'SimplyHired'
                            })
                            
                    except Exception as e:
                        print(f"Error parsing SimplyHired job: {e}")
                        continue
                    
                # Avoid aggressive scraping
                time.sleep(random.uniform(2, 5))
                
            else:
                print(f"Failed to retrieve SimplyHired jobs: Status code {response.status_code}")
                
        except Exception as e:
            print(f"Error scraping SimplyHired: {e}")
    
    def run_all_scrapers(self):
        """Run all job scrapers"""
        self.scrape_indeed()
        self.scrape_linkedin()
        self.scrape_glassdoor()
        self.scrape_monster()
        self.scrape_simplyhired()
        
        print(f"Found {len(self.results)} matching job listings")
        return self.results
    
    def save_results(self):
        """Save results to CSV and JSON files"""
        if not self.results:
            print("No results to save")
            return []
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Save as CSV
        df = pd.DataFrame(self.results)
        csv_filename = f'data/chinese_teacher_jobs_{self.today}.csv'
        df.to_csv(csv_filename, index=False)
        print(f"Results saved to {csv_filename}")
        
        # Save as JSON
        json_filename = f'data/chinese_teacher_jobs_{self.today}.json'
        with open(json_filename, 'w') as f:
            json.dump(self.results, f, indent=4)
        print(f"Results saved to {json_filename}")
        
        # Generate summary file
        summary_filename = f'data/summary_{self.today}.md'
        with open(summary_filename, 'w') as f:
            f.write(f"# Chinese Teacher Job Summary - {self.today}\n\n")
            f.write(f"Total jobs found: {len(self.results)}\n\n")
            
            # Jobs by source
            f.write("## Jobs by Source\n\n")
            source_counts = df['source'].value_counts()
            for source, count in source_counts.items():
                f.write(f"- {source}: {count}\n")
            
            # Jobs by location (top 10)
            f.write("\n## Top Locations\n\n")
            location_counts = df['location'].value_counts().head(10)
            for location, count in location_counts.items():
                f.write(f"- {location}: {count}\n")
            
            # Recent job listings (10 most recent)
            f.write("\n## Recent Job Listings\n\n")
            for i, job in enumerate(self.results[:10]):
                f.write(f"### {i+1}. {job['title']} - {job['company']}\n")
                f.write(f"- Location: {job['location']}\n")
                f.write(f"- Salary: {job['salary']}\n")
                f.write(f"- Posted: {job['date_posted']}\n")
                f.write(f"- Source: {job['source']}\n")
                f.write(f"- Link: {job['job_link']}\n\n")
        
        print(f"Summary saved to {summary_filename}")
        
        return [csv_filename, json_filename, summary_filename]

# Update README file
def update_readme(job_count):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Create or update README.md
    readme_content = f"""# Chinese Teacher Job Tracker

An automated tracker for Chinese teacher job postings from major job sites.

## Latest Update

- Date: {today}
- Jobs found: {job_count}

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
"""
    
    with open('README.md', 'w') as f:
        f.write(readme_content)
    print("Updated README.md")

# Main function
def main():
    try:
        # Initialize and run job scraper
        scraper = JobScraper()
        results = scraper.run_all_scrapers()
        
        if results:
            # Save results to files
            saved_files = scraper.save_results()
            
            # Update README with job count
            update_readme(len(results))
            
            print("Job scraping completed successfully")
            print(f"Found {len(results)} jobs matching criteria")
        else:
            print("No matching jobs found")
            update_readme(0)
            
    except Exception as e:
        print(f"Error in main function: {e}")

if __name__ == "__main__":
    main()
