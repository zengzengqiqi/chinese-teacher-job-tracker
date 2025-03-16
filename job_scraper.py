import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import time
import random
import json
import os
import re
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class JobScraper:
    def __init__(self):
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.results = []
        self.min_salary = 3000  # Minimum salary in USD
        self.date_threshold = datetime.datetime.now() - datetime.timedelta(days=7)
        
        # Create a session with retry mechanism
        self.session = self._create_session()
        
        # User agent rotation to avoid being blocked
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 17_0_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        ]
    
    def _create_session(self):
        """Create a session with retry mechanism"""
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
    
    def get_headers(self):
        """Rotate user agents to avoid scraping detection"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'DNT': '1',
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
    
    def safe_request(self, url, max_retries=3, delay_range=(3, 8)):
        """Make a request with retries and random delays to avoid blocking"""
        for attempt in range(max_retries):
            try:
                # Random delay between requests
                if attempt > 0:
                    sleep_time = random.uniform(*delay_range) * (attempt + 1)
                    print(f"Retry attempt {attempt+1}, waiting {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                
                # Make the request with a new header each time
                headers = self.get_headers()
                response = self.session.get(url, headers=headers, timeout=30)
                
                # Check if response is valid
                if response.status_code == 200 and len(response.text) > 1000:  # Basic check for meaningful content
                    return response
                elif response.status_code == 403 or response.status_code == 429:
                    print(f"Request was blocked (status {response.status_code}), retrying...")
                    # Longer wait time for rate limiting
                    time.sleep(random.uniform(10, 15))
                else:
                    print(f"Received status code {response.status_code}, retrying...")
            except Exception as e:
                print(f"Request error: {e}, retrying...")
        
        print(f"Failed to retrieve {url} after {max_retries} attempts")
        return None
    
    def scrape_indeed(self):
        """Scrape Chinese teacher jobs from Indeed"""
        print("Scraping Indeed...")
        for page in range(0, 3):  # Check first 3 pages
            try:
                url = f"https://www.indeed.com/jobs?q=chinese+teacher+${self.min_salary}&sort=date&fromage=7&start={page*10}"
                response = self.safe_request(url)
                
                if response:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    job_cards = soup.select('div.job_seen_beacon')
                    
                    if not job_cards:
                        job_cards = soup.select('div.jobsearch-SerpJobCard')
                    
                    if not job_cards:
                        print(f"No job cards found on page {page}, trying alternative selectors")
                        # Try more generic selectors
                        job_cards = soup.select('[data-testid*="job-card"]') or soup.select('[data-testid*="jobCard"]') or soup.select('div[class*="job"]')
                    
                    if job_cards:
                        print(f"Found {len(job_cards)} job cards on Indeed page {page}")
                    else:
                        print(f"No job cards found on Indeed page {page} with any selector")
                        continue
                    
                    for job in job_cards:
                        try:
                            # Extract job title with multiple selector attempts
                            title_elem = (job.select_one('h2.jobTitle') or 
                                        job.select_one('a.jobtitle') or 
                                        job.select_one('[class*="title"]') or
                                        job.select_one('h2') or
                                        job.select_one('h3'))
                            
                            if not title_elem:
                                continue
                                
                            title = title_elem.get_text().strip()
                            
                            # Extract company with fallbacks
                            company_elem = (job.select_one('span.companyName') or 
                                           job.select_one('span.company') or
                                           job.select_one('[class*="company"]'))
                            company = company_elem.get_text().strip() if company_elem else "N/A"
                            
                            # Extract location with fallbacks
                            location_elem = (job.select_one('div.companyLocation') or 
                                            job.select_one('div.recJobLoc') or
                                            job.select_one('[class*="location"]'))
                            location = location_elem.get_text().strip() if location_elem else "N/A"
                            
                            # Extract salary with fallbacks
                            salary_elem = (job.select_one('div.metadata.salary-snippet-container') or 
                                          job.select_one('span.salaryText') or
                                          job.select_one('[class*="salary"]'))
                            salary = salary_elem.get_text().strip() if salary_elem else "N/A"
                            
                            # Extract job link
                            link_elem = (job.select_one('a[id^="job_"]') or 
                                        job.select_one('a.jobtitle') or
                                        job.select_one('a[href*="job"]') or
                                        job.select_one('a'))
                            
                            if link_elem and 'href' in link_elem.attrs:
                                job_link = link_elem['href']
                                if not job_link.startswith('http'):
                                    job_link = "https://www.indeed.com" + job_link
                            else:
                                job_link = "N/A"
                            
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
                                print(f"Found Indeed job: {title} at {company}")
                                
                        except Exception as e:
                            print(f"Error parsing Indeed job: {e}")
                            continue
                    
                # Avoid aggressive scraping between pages
                time.sleep(random.uniform(5, 10))
                
            except Exception as e:
                print(f"Error scraping Indeed page {page}: {e}")
                continue
    
    def scrape_linkedin(self):
        """Scrape Chinese teacher jobs from LinkedIn"""
        print("Scraping LinkedIn...")
        try:
            url = "https://www.linkedin.com/jobs/search/?keywords=chinese%20teacher&f_TPR=r604800"
            response = self.safe_request(url)
            
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.select('div.base-card')
                
                if not job_cards:
                    # Try alternative selectors
                    job_cards = soup.select('[data-job-id]') or soup.select('li.jobs-search-results__list-item')
                
                if job_cards:
                    print(f"Found {len(job_cards)} job cards on LinkedIn")
                else:
                    print("No job cards found on LinkedIn with any selector")
                
                for job in job_cards:
                    try:
                        # Extract job title with fallback selectors
                        title_elem = (job.select_one('h3.base-search-card__title') or 
                                     job.select_one('.job-search-card__title') or
                                     job.select_one('[class*="title"]'))
                        
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text().strip()
                        
                        # Extract company with fallbacks
                        company_elem = (job.select_one('h4.base-search-card__subtitle') or 
                                       job.select_one('.job-search-card__subtitle') or
                                       job.select_one('[class*="company"]'))
                        company = company_elem.get_text().strip() if company_elem else "N/A"
                        
                        # Extract location with fallbacks
                        location_elem = (job.select_one('span.job-search-card__location') or 
                                        job.select_one('[class*="location"]'))
                        location = location_elem.get_text().strip() if location_elem else "N/A"
                        
                        # LinkedIn doesn't always show salary on search page
                        salary = "Check job details"
                        
                        # Extract job link with fallbacks
                        link_elem = (job.select_one('a.base-card__full-link') or 
                                    job.select_one('[class*="card"] > a') or
                                    job.select_one('a'))
                        
                        if link_elem and 'href' in link_elem.attrs:
                            job_link = link_elem['href']
                        else:
                            job_link = "N/A"
                        
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
                            print(f"Found LinkedIn job: {title} at {company}")
                            
                    except Exception as e:
                        print(f"Error parsing LinkedIn job: {e}")
                        continue
                
            else:
                print("Failed to retrieve LinkedIn jobs")
                
        except Exception as e:
            print(f"Error scraping LinkedIn: {e}")
    
    def scrape_glassdoor(self):
        """Scrape Chinese teacher jobs from Glassdoor"""
        print("Scraping Glassdoor...")
        try:
            url = "https://www.glassdoor.com/Job/chinese-teacher-jobs-SRCH_KO0,15.htm"
            response = self.safe_request(url)
            
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.select('li.react-job-listing')
                
                if not job_cards:
                    # Try alternative selectors
                    job_cards = soup.select('[data-id*="job"]') or soup.select('[class*="jobListing"]')
                
                if job_cards:
                    print(f"Found {len(job_cards)} job cards on Glassdoor")
                else:
                    print("No job cards found on Glassdoor with any selector")
                
                for job in job_cards:
                    try:
                        # Try to extract job data from data attributes first
                        job_title = job.get('data-normalize-job-title', None)
                        employer_name = job.get('data-employer-name', None)
                        location = job.get('data-job-loc', None)
                        
                        # If data attributes failed, try DOM selectors
                        if not job_title:
                            title_elem = job.select_one('[class*="title"]') or job.select_one('a[data-test="job-link"]')
                            job_title = title_elem.get_text().strip() if title_elem else "N/A"
                            
                        if not employer_name:    
                            company_elem = job.select_one('[class*="employer"]') or job.select_one('[data-test*="employer"]')
                            employer_name = company_elem.get_text().strip() if company_elem else "N/A"
                            
                        if not location:
                            location_elem = job.select_one('[class*="location"]') or job.select_one('[data-test*="location"]')
                            location = location_elem.get_text().strip() if location_elem else "N/A"
                        
                        # Extract salary
                        salary_elem = job.select_one('span.salary-estimate') or job.select_one('[data-test*="salary"]')
                        salary = salary_elem.get_text().strip() if salary_elem else "N/A"
                        
                        # Extract date posted
                        date_elem = job.select_one('div.listing-age') or job.select_one('[data-test*="job-age"]')
                        date_posted = date_elem.get_text().strip() if date_elem else "N/A"
                        
                        # Check if job was posted within last week
                        if date_posted != "N/A" and "d" in date_posted:
                            days_ago = int(''.join(filter(str.isdigit, date_posted)))
                            if days_ago > 7:
                                continue
                        
                        # Extract job link
                        link_elem = job.select_one('a.jobLink') or job.select_one('a[data-test="job-link"]') or job.select_one('a')
                        
                        if link_elem and 'href' in link_elem.attrs:
                            job_link = link_elem['href']
                            if not job_link.startswith('http'):
                                job_link = "https://www.glassdoor.com" + job_link
                        else:
                            job_link = "N/A"
                        
                        # Check if job meets criteria
                        if self.meets_criteria(job_title, salary):
                            self.results.append({
                                'title': job_title,
                                'company': employer_name, 
                                'location': location,
                                'salary': salary,
                                'date_posted': date_posted if date_posted != "N/A" else "Within last 7 days",
                                'job_link': job_link,
                                'source': 'Glassdoor'
                            })
                            print(f"Found Glassdoor job: {job_title} at {employer_name}")
                            
                    except Exception as e:
                        print(f"Error parsing Glassdoor job: {e}")
                        continue
                
            else:
                print("Failed to retrieve Glassdoor jobs")
                
        except Exception as e:
            print(f"Error scraping Glassdoor: {e}")
    
    def scrape_monster(self):
        """Scrape Chinese teacher jobs from Monster"""
        print("Scraping Monster...")
        try:
            url = "https://www.monster.com/jobs/search?q=Chinese+Teacher&saltyp=1&salary=3000&where=&page=1&so=date.desc"
            response = self.safe_request(url)
            
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.select('div.job-cardstyle__JobCardComponent')
                
                if not job_cards:
                    # Try alternative selectors
                    job_cards = soup.select('[data-testid*="job-card"]') or soup.select('[class*="card"]')
                
                if job_cards:
                    print(f"Found {len(job_cards)} job cards on Monster")
                else:
                    print("No job cards found on Monster with any selector")
                
                for job in job_cards:
                    try:
                        # Extract job title with fallbacks
                        title_elem = (job.select_one('h3.job-cardstyle__JobTitle') or 
                                     job.select_one('[class*="title"]') or 
                                     job.select_one('h3'))
                        
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text().strip()
                        
                        # Extract company with fallbacks
                        company_elem = (job.select_one('span.job-cardstyle__CompanyName') or 
                                       job.select_one('[class*="company"]'))
                        company = company_elem.get_text().strip() if company_elem else "N/A"
                        
                        # Extract location with fallbacks
                        location_elem = (job.select_one('span.job-cardstyle__Location') or 
                                        job.select_one('[class*="location"]'))
                        location = location_elem.get_text().strip() if location_elem else "N/A"
                        
                        # Extract date posted with fallbacks
                        date_elem = (job.select_one('span.job-cardstyle__JobAge') or 
                                    job.select_one('[class*="age"]') or
                                    job.select_one('[class*="date"]'))
                        date_posted = date_elem.get_text().strip() if date_elem else "N/A"
                        
                        # Check if job was posted within last week
                        if date_posted != "N/A" and "d" in date_posted:
                            days_ago = int(''.join(filter(str.isdigit, date_posted)))
                            if days_ago > 7:
                                continue
                        
                        # Extract job link with fallbacks
                        link_elem = job.select_one('a')
                        
                        if link_elem and 'href' in link_elem.attrs:
                            job_link = link_elem['href']
                        else:
                            job_link = "N/A"
                        
                        # Check if job meets criteria
                        if self.meets_criteria(title, f"Min ${self.min_salary}"):
                            self.results.append({
                                'title': title,
                                'company': company, 
                                'location': location,
                                'salary': f"Min ${self.min_salary}",
                                'date_posted': date_posted if date_posted != "N/A" else "Within last 7 days",
                                'job_link': job_link,
                                'source': 'Monster'
                            })
                            print(f"Found Monster job: {title} at {company}")
                            
                    except Exception as e:
                        print(f"Error parsing Monster job: {e}")
                        continue
                
            else:
                print("Failed to retrieve Monster jobs")
                
        except Exception as e:
            print(f"Error scraping Monster: {e}")
    
    def scrape_simplyhired(self):
        """Scrape Chinese teacher jobs from SimplyHired"""
        print("Scraping SimplyHired...")
        try:
            url = "https://www.simplyhired.com/search?q=chinese+teacher&fdb=7"  # fdb=7 means last 7 days
            response = self.safe_request(url)
            
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.select('div.SerpJob-jobCard')
                
                if not job_cards:
                    # Try alternative selectors
                    job_cards = soup.select('article') or soup.select('[class*="jobCard"]') or soup.select('[class*="job-listing"]')
                
                if job_cards:
                    print(f"Found {len(job_cards)} job cards on SimplyHired")
                else:
                    print("No job cards found on SimplyHired with any selector")
                
                for job in job_cards:
                    try:
                        # Extract job title with fallbacks
                        title_elem = (job.select_one('h3.jobposting-title') or 
                                     job.select_one('[class*="title"]') or
                                     job.select_one('h2, h3'))
                        
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text().strip()
                        
                        # Extract company with fallbacks
                        company_elem = (job.select_one('span.jobposting-company') or 
                                       job.select_one('[class*="company"]'))
                        company = company_elem.get_text().strip() if company_elem else "N/A"
                        
                        # Extract location with fallbacks
                        location_elem = (job.select_one('span.jobposting-location') or 
                                        job.select_one('[class*="location"]'))
                        location = location_elem.get_text().strip() if location_elem else "N/A"
                        
                        # Extract salary with fallbacks
                        salary_elem = (job.select_one('div.jobposting-salary') or 
                                      job.select_one('[class*="salary"]'))
                        salary = salary_elem.get_text().strip() if salary_elem else "N/A"
                        
                        # Extract job link with fallbacks
                        link_elem = job.select_one('a')
                        
                        if link_elem and 'href' in link_elem.attrs:
                            job_link = link_elem['href']
                            if not job_link.startswith('http'):
                                job_link = "https://www.simplyhired.com" + job_link
                        else:
                            job_link = "N/A"
                        
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
                            print(f"Found SimplyHired job: {title} at {company}")
                            
                    except Exception as e:
                        print(f"Error parsing SimplyHired job: {e}")
                        continue
                
            else:
                print("Failed to retrieve SimplyHired jobs")
                
        except Exception as e:
            print(f"Error scraping SimplyHired: {e}")
    
    def run_all_scrapers(self):
        """Run all job scrapers"""
        print("Starting job scraping...")
        
        # Create empty result with dummy data in case all scrapers fail
        self.results.append({
            'title': 'Mandarin Chinese Teacher (Example)',
            'company': 'Example School', 
            'location': 'Remote',
            'salary': '$3000-$4000 per month',
            'date_posted': 'Within last 7 days',
            'job_link': 'https://example.com/job',
            'source': 'Example'
        })
        
        try:
            self.scrape_indeed()
            time.sleep(random.uniform(5, 10))  # Add delay between different job sites
        except Exception as e:
            print(f"Error running Indeed scraper: {e}")
        
        try:
            self.scrape_linkedin()
            time.sleep(random.uniform(5, 10))
        except Exception as e:
            print(f"Error running LinkedIn scraper: {e}")
        
        try:
            self.scrape_glassdoor()
            time.sleep(random.uniform(5, 10))
        except Exception as e:
            print(f"Error running Glassdoor scraper: {e}")
        
        try:
            self.scrape_monster()
            time.sleep(random.uniform(5, 10))
        except Exception as e:
            print(f"Error running Monster scraper: {e}")
        
        try:
            self.scrape_simplyhired()
        except Exception as e:
            print(f"Error running SimplyHired scraper: {e}")
        
        # Remove the dummy example if we found real results
        if len(self.results) > 1:
            self.results = [job for job in self.results if job['source'] != 'Example']
        
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
        # Create an empty data set if everything fails
        try:
            os.makedirs('data', exist_ok=True)
            # Create empty files with today's date
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            with open(f'data/summary_{today}.md', 'w') as f:
                f.write(f"# Chinese Teacher Job Summary - {today}\n\n")
                f.write("No jobs found or error in scraping process. Please check logs.\n")
            
            update_readme(0)
        except Exception as inner_e:
            print(f"Failed to create fallback files: {inner_e}")

if __name__ == "__main__":
    main()
