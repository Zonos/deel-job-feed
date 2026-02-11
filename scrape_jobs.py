#!/usr/bin/env python3
"""
Deel Job Board Scraper
Scrapes jobs from Deel job board and generates XML feeds for job aggregators
"""

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import json
import os

DEEL_JOB_BOARD_URL = "https://jobs.deel.com/job-boards/zonos"
COMPANY_NAME = "Zonos"
COMPANY_URL = "https://zonos.com"

def fetch_job_page():
    """Fetch the Deel job board page"""
    print(f"Fetching jobs from {DEEL_JOB_BOARD_URL}...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    response = requests.get(DEEL_JOB_BOARD_URL, headers=headers)
    response.raise_for_status()
    return response.text

def parse_jobs(html_content):
    """Parse job listings from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    jobs = []

    # Look for job listings - Deel typically uses specific class names or data attributes
    # This may need adjustment based on actual HTML structure
    job_elements = soup.find_all(['div', 'article', 'li'], class_=lambda x: x and any(
        keyword in str(x).lower() for keyword in ['job', 'position', 'listing', 'opening']
    ))

    if not job_elements:
        # Try alternative selectors
        job_elements = soup.find_all('a', href=lambda x: x and '/job/' in str(x))

    print(f"Found {len(job_elements)} potential job elements")

    for idx, element in enumerate(job_elements):
        try:
            # Extract job details - adjust selectors based on actual HTML
            job = {}

            # Try to find job title
            title_elem = element.find(['h2', 'h3', 'h4']) or element
            job['title'] = title_elem.get_text(strip=True) if title_elem else f"Position {idx + 1}"

            # Try to find job URL
            link = element.find('a') if element.name != 'a' else element
            if link and link.get('href'):
                job_url = link['href']
                if not job_url.startswith('http'):
                    job_url = f"https://jobs.deel.com{job_url}"
                job['url'] = job_url
            else:
                job['url'] = DEEL_JOB_BOARD_URL

            # Try to find location
            location_elem = element.find(string=lambda text: text and any(
                keyword in text.lower() for keyword in ['remote', 'location', 'anywhere']
            ))
            job['location'] = location_elem.strip() if location_elem else "Remote"

            # Try to find job type
            type_elem = element.find(string=lambda text: text and any(
                keyword in text.lower() for keyword in ['full-time', 'part-time', 'contract', 'full time', 'part time']
            ))
            job['job_type'] = type_elem.strip() if type_elem else "Full-time"

            # Default values
            job['company'] = COMPANY_NAME
            job['date_posted'] = datetime.now().strftime('%Y-%m-%d')
            job['description'] = ""

            # Only add if we have at least a title
            if job['title'] and len(job['title']) > 3:
                jobs.append(job)
                print(f"  ✓ {job['title']}")

        except Exception as e:
            print(f"  ✗ Error parsing job element: {e}")
            continue

    return jobs

def fetch_job_details(job_url):
    """Fetch detailed job description from job detail page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(job_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Try to find job description
        description = ""
        desc_elem = soup.find(['div', 'section'], class_=lambda x: x and 'description' in str(x).lower())
        if desc_elem:
            description = desc_elem.get_text(strip=True)

        return description
    except Exception as e:
        print(f"    Could not fetch details: {e}")
        return ""

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
        ET.SubElement(job_elem, 'referencenumber').text = str(hash(job['url']))[:8]
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
        # Fetch and parse jobs
        html_content = fetch_job_page()
        jobs = parse_jobs(html_content)

        if not jobs:
            print("\n⚠️  No jobs found! The page structure may have changed.")
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
