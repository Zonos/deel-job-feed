#!/usr/bin/env python3
"""
Deel Job Board Scraper with Playwright
Scrapes JavaScript-rendered jobs from Deel job board and generates XML feeds for job aggregators
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import json
import os
import time

DEEL_JOB_BOARD_URL = "https://jobs.deel.com/job-boards/zonos"
COMPANY_NAME = "Zonos"
COMPANY_URL = "https://zonos.com"

def fetch_job_page_with_browser():
    """Fetch the Deel job board page using Playwright to render JavaScript"""
    print(f"Fetching jobs from {DEEL_JOB_BOARD_URL}...")
    print("Using browser automation to handle JavaScript rendering...")

    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the job board
        page.goto(DEEL_JOB_BOARD_URL, wait_until='networkidle', timeout=30000)

        # Wait for jobs to load - try multiple strategies
        try:
            # Wait for any job-related elements to appear
            page.wait_for_selector('div, article, a', timeout=10000)
            print("  ✓ Page loaded, waiting for content to render...")

            # Give extra time for dynamic content
            time.sleep(3)

        except Exception as e:
            print(f"  ⚠ Timeout waiting for selectors: {e}")
            print("  Continuing with whatever content is available...")

        # Get the rendered HTML
        html_content = page.content()

        # Save a screenshot for debugging
        try:
            os.makedirs('feeds', exist_ok=True)
            page.screenshot(path='feeds/debug-screenshot.png')
            print("  ✓ Screenshot saved to feeds/debug-screenshot.png")
        except:
            pass

        browser.close()

        return html_content

def parse_jobs(html_content):
    """Parse job listings from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    jobs = []

    print("\nSearching for job listings...")

    # Strategy 1: Look for common job listing patterns
    job_elements = []

    # Try to find job cards/items
    selectors = [
        {'name': 'div', 'class_contains': ['job', 'position', 'opening', 'card', 'item']},
        {'name': 'article', 'class_contains': None},
        {'name': 'li', 'class_contains': ['job', 'position']},
        {'name': 'a', 'href_contains': ['/job/', '/position/', '/opening/']}
    ]

    for selector in selectors:
        if selector.get('class_contains'):
            elements = soup.find_all(selector['name'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in selector['class_contains']
            ))
        elif selector.get('href_contains'):
            elements = soup.find_all(selector['name'], href=lambda x: x and any(
                keyword in str(x).lower() for keyword in selector['href_contains']
            ))
        else:
            elements = soup.find_all(selector['name'])

        if elements:
            print(f"  Found {len(elements)} elements using selector: {selector}")
            job_elements.extend(elements)

    # Remove duplicates
    job_elements = list(set(job_elements))
    print(f"\nTotal unique elements found: {len(job_elements)}")

    # Parse each job element
    for idx, element in enumerate(job_elements):
        try:
            job = {}

            # Extract job title
            title_elem = (
                element.find(['h1', 'h2', 'h3', 'h4', 'h5']) or
                element.find(class_=lambda x: x and 'title' in str(x).lower()) or
                element.find('a') or
                element
            )

            title_text = title_elem.get_text(strip=True) if title_elem else ""

            # Filter out navigation items and non-job text
            skip_keywords = ['home', 'about', 'contact', 'login', 'sign', 'menu', 'search', 'filter']
            if any(keyword in title_text.lower() for keyword in skip_keywords):
                continue

            if not title_text or len(title_text) < 3 or len(title_text) > 200:
                continue

            job['title'] = title_text

            # Extract job URL
            link = element.find('a') if element.name != 'a' else element
            if link and link.get('href'):
                job_url = link['href']
                if not job_url.startswith('http'):
                    if job_url.startswith('/'):
                        job_url = f"https://jobs.deel.com{job_url}"
                    else:
                        job_url = f"https://jobs.deel.com/{job_url}"
                job['url'] = job_url
            else:
                job['url'] = DEEL_JOB_BOARD_URL

            # Extract location
            location_elem = element.find(class_=lambda x: x and 'location' in str(x).lower())
            if not location_elem:
                location_text = element.find(string=lambda text: text and any(
                    keyword in text.lower() for keyword in ['remote', 'hybrid', 'office', 'worldwide']
                ))
                location_elem = location_text
            job['location'] = location_elem.strip() if location_elem else "Remote"

            # Extract job type
            type_elem = element.find(string=lambda text: text and any(
                keyword in text.lower() for keyword in ['full-time', 'part-time', 'contract', 'full time']
            ))
            job['job_type'] = type_elem.strip() if type_elem else "Full-time"

            # Default values
            job['company'] = COMPANY_NAME
            job['date_posted'] = datetime.now().strftime('%Y-%m-%d')
            job['description'] = job['title']  # Use title as description for now

            # Add to list
            jobs.append(job)
            print(f"  ✓ Found: {job['title']}")

        except Exception as e:
            print(f"  ✗ Error parsing element: {e}")
            continue

    return jobs

def generate_rss_feed(jobs):
    """Generate RSS 2.0 feed"""
    rss = ET.Element('rss', version='2.0', attrib={
        'xmlns:atom': 'http://www.w3.org/2005/Atom'
    })
    channel = ET.SubElement(rss, 'channel')

    ET.SubElement(channel, 'title').text = f"{COMPANY_NAME} Jobs"
    ET.SubElement(channel, 'link').text = COMPANY_URL
    ET.SubElement(channel, 'description').text = f"Current job openings at {COMPANY_NAME}"
    ET.SubElement(channel, 'language').text = "en-us"
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')

    for job in jobs:
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = job['title']
        ET.SubElement(item, 'link').text = job['url']
        ET.SubElement(item, 'description').text = f"{job['title']} - {job['location']}"
        ET.SubElement(item, 'pubDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        ET.SubElement(item, 'guid', isPermaLink='true').text = job['url']

    return prettify_xml(rss)

def generate_indeed_xml(jobs):
    """Generate Indeed-compatible XML feed"""
    source = ET.Element('source')
    publisher = ET.SubElement(source, 'publisher')
    ET.SubElement(publisher, 'name').text = COMPANY_NAME
    publisherurl = ET.SubElement(source, 'publisherurl')
    publisherurl.text = COMPANY_URL
    ET.SubElement(source, 'lastBuildDate').text = datetime.now().strftime('%Y-%m-%d')

    for job in jobs:
        job_elem = ET.SubElement(source, 'job')
        ET.SubElement(job_elem, 'title').text = job['title']
        ET.SubElement(job_elem, 'date').text = job['date_posted']
        ET.SubElement(job_elem, 'referencenumber').text = str(abs(hash(job['url'])))[:8]
        ET.SubElement(job_elem, 'url').text = job['url']
        ET.SubElement(job_elem, 'company').text = job['company']
        ET.SubElement(job_elem, 'city').text = job['location']
        ET.SubElement(job_elem, 'state').text = ""
        ET.SubElement(job_elem, 'country').text = "US"
        ET.SubElement(job_elem, 'postalcode').text = ""
        ET.SubElement(job_elem, 'description').text = job.get('description', job['title'])
        ET.SubElement(job_elem, 'jobtype').text = job.get('job_type', 'Full-time')
        ET.SubElement(job_elem, 'category').text = ""
        ET.SubElement(job_elem, 'experience').text = ""
        ET.SubElement(job_elem, 'education').text = ""

    return prettify_xml(source)

def generate_google_jobs_json(jobs):
    """Generate Google Jobs JSON-LD format"""
    job_postings = []

    for job in jobs:
        posting = {
            "@context": "https://schema.org/",
            "@type": "JobPosting",
            "title": job['title'],
            "description": job.get('description', job['title']),
            "datePosted": job['date_posted'],
            "hiringOrganization": {
                "@type": "Organization",
                "name": COMPANY_NAME,
                "sameAs": COMPANY_URL
            },
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": job['location']
                }
            },
            "url": job['url'],
            "employmentType": job.get('job_type', 'FULL_TIME').upper().replace('-', '_').replace(' ', '_')
        }
        job_postings.append(posting)

    return json.dumps(job_postings, indent=2)

def prettify_xml(elem):
    """Return a pretty-printed XML string"""
    rough_string = ET.tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def main():
    """Main execution function"""
    print(f"\n{'='*60}")
    print(f"Deel Job Board Scraper for {COMPANY_NAME}")
    print(f"{'='*60}\n")

    try:
        # Fetch and parse jobs using Playwright
        html_content = fetch_job_page_with_browser()
        jobs = parse_jobs(html_content)

        if not jobs:
            print("\n⚠️  No jobs found!")
            print("This could mean:")
            print("  1. No jobs are currently posted on your Deel board")
            print("  2. The page structure has changed")
            print("  3. The selectors need adjustment")
            print("\nCheck the screenshot at feeds/debug-screenshot.png")
            print("Creating empty feeds...")
        else:
            print(f"\n✓ Successfully parsed {len(jobs)} jobs")

        # Create feeds directory if it doesn't exist
        os.makedirs('feeds', exist_ok=True)

        # Generate feeds
        print("\nGenerating feeds...")

        # RSS Feed
        rss_feed = generate_rss_feed(jobs)
        with open('feeds/jobs.rss', 'w', encoding='utf-8') as f:
            f.write(rss_feed)
        print("  ✓ RSS feed: feeds/jobs.rss")

        # Indeed XML
        indeed_xml = generate_indeed_xml(jobs)
        with open('feeds/indeed.xml', 'w', encoding='utf-8') as f:
            f.write(indeed_xml)
        print("  ✓ Indeed XML: feeds/indeed.xml")

        # Google Jobs JSON
        google_json = generate_google_jobs_json(jobs)
        with open('feeds/google-jobs.json', 'w', encoding='utf-8') as f:
            f.write(google_json)
        print("  ✓ Google Jobs JSON: feeds/google-jobs.json")

        # Job list JSON for debugging
        with open('feeds/jobs.json', 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2)
        print("  ✓ Job data JSON: feeds/jobs.json")

        print(f"\n{'='*60}")
        print(f"✓ Done! Generated {len(jobs)} job listings")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
