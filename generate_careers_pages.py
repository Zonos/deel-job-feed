#!/usr/bin/env python3
"""
Generate static careers pages from Zonos job feed
Optimized for Indeed and job aggregator crawling
"""

import json
import requests
from datetime import datetime
from pathlib import Path
from html import escape
import re

# Configuration
FEED_URL = "https://zonos.github.io/deel-job-feed/feeds/jobs.json"
OUTPUT_DIR = Path("careers")
COMPANY_NAME = "Zonos"
COMPANY_URL = "https://www.zonos.com"
COMPANY_LOGO = "https://www.zonos.com/logo.png"  # Update with actual logo URL
COMPANY_DESCRIPTION = "Zonos provides scalable technology to simplify the complexities of international commerce, making it accessible to everyone. We create trust in global trade."

def fetch_jobs():
    """Fetch jobs from the JSON feed"""
    try:
        # Check if FEED_URL is a local file path or URL
        if FEED_URL.startswith(('http://', 'https://')):
            response = requests.get(FEED_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
        else:
            # Read from local file
            with open(FEED_URL, 'r', encoding='utf-8') as f:
                data = json.load(f)

        # Handle both list and dict responses
        if isinstance(data, list):
            jobs_list = data
        elif isinstance(data, dict):
            jobs_list = data.get('jobs', [])
        else:
            jobs_list = []

        # Extract unique jobs (avoid duplicates)
        # Use URL with job-details as the unique key (prefer detailed URLs)
        seen_urls = {}

        for job in jobs_list:
            raw_title = job.get('title', '')
            raw_description = job.get('description', '')
            raw_job_type = job.get('jobtype', job.get('job_type', 'Full-time'))

            cleaned_title = clean_job_title(raw_title)
            cleaned_description = clean_job_description(raw_description, cleaned_title)
            cleaned_job_type = clean_job_type(raw_job_type)

            url = job.get('url', '')

            # Extract ID from URL
            job_id = job.get('id', job.get('referencenumber', ''))
            if not job_id and url:
                match = re.search(r'/job-details/([a-f0-9-]+)', url)
                if match:
                    job_id = match.group(1)
                else:
                    job_id = str(hash(cleaned_title + url))[:8]

            # Use title as unique key (prefer URLs with job-details)
            unique_key = cleaned_title.lower()

            # Extract city/state/country from raw title if concatenated (e.g. "Account ExecutiveGold Coast")
            city = job.get('city', job.get('location', ''))
            state = job.get('state', '')
            country = job.get('country', 'US')
            if (not city or city.lower() == 'remote') and re.search(r'Gold\s*Coast', raw_title, re.IGNORECASE):
                city = 'Gold Coast'
                state = 'QLD'
                country = 'AU'

            # If we haven't seen this job, or this version has a better URL, use it
            if unique_key not in seen_urls or '/job-details/' in url:
                seen_urls[unique_key] = {
                    'title': cleaned_title,
                    'url': url,
                    'location': job.get('location', ''),
                    'city': city,
                    'state': state,
                    'country': country,
                    'jobtype': cleaned_job_type,
                    'date': job.get('date', job.get('date_posted', '')),
                    'description': cleaned_description,
                    'id': job_id,
                }

        unique_jobs = list(seen_urls.values())

        return unique_jobs
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return []

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def clean_job_title(title):
    """Clean job title by removing unwanted suffixes"""
    # Strip concatenated location suffix (no separator): "TitleSt.George UT..." or "Title(...)St.George UT..."
    title = re.sub(r'(?<=[a-zA-Z)])\s*St\.?\s*George\b.*$', '', title, flags=re.IGNORECASE)
    # Strip concatenated Australian city names (e.g. "Account ExecutiveGold Coast")
    title = re.sub(r'(?<=[a-zA-Z)])\s*Gold\s*Coast.*$', '', title, flags=re.IGNORECASE)
    # Strip concatenated salary suffix
    title = re.sub(r'\s*\$[\d,]+.*$', '', title)
    # Strip concatenated job type without separator
    title = re.sub(r'(?<=[a-zA-Z)])\s*Full[-\s]?time\b.*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'(?<=[a-zA-Z)])\s*Part[-\s]?time\b.*$', '', title, flags=re.IGNORECASE)
    # Handle bullet-separated format: <title><DeptName> - Department · <location>
    match = re.search(r'(?<=[a-z)])[A-Z][a-zA-Z]+\s*-\s*Department[\s·•]', title)
    if match:
        title = title[:match.start()].strip()
    else:
        title = re.split(r'Department\s*[·•]|Department\s*-', title, flags=re.IGNORECASE)[0]
    title = re.split(r'\s*[·•]\s*Remote', title, flags=re.IGNORECASE)[0]
    title = re.split(r'\s*[·•]\s*Full-time', title, flags=re.IGNORECASE)[0]
    title = re.split(r'\s*[·•]\s*Part-time', title, flags=re.IGNORECASE)[0]
    return title.strip()

def format_title_with_breaks(title):
    """Add natural line breaks to job titles for better display"""
    # Add line break before opening parenthesis if title is long enough
    if '(' in title and len(title) > 30:
        title = re.sub(r'\s*\(', '<br>(', title)
    # Add line break before " - " if present
    if ' - ' in title and len(title) > 35:
        title = re.sub(r'\s*-\s*', '<br>- ', title, count=1)
    return title

def clean_job_description(description, title=''):
    """Clean job description by removing unwanted text"""
    # Check if description contains HTML tags - if so, preserve HTML structure
    has_html = bool(re.search(r'<[^>]+>', description))

    if has_html:
        # For HTML content, preserve all HTML tags and structure
        # Only remove specific boilerplate text at the beginning
        # Remove the Deel page header text (before the first <p> tag ideally)
        description = re.sub(r'^[^<]*?You need to enable JavaScript to run this app\.?\s*', '', description, flags=re.IGNORECASE)
        description = re.sub(r'^[^<]*?@ Zonos \| Deel - Your forever people platform\s*', '', description, flags=re.IGNORECASE)

        # Remove opening <p> tags that contain boilerplate
        description = re.sub(r'<p>\s*Corporate Broker[^<]*?@ Zonos \| Deel[^<]*?</p>', '', description, flags=re.IGNORECASE)
        description = re.sub(r'<p>\s*You need to enable JavaScript[^<]*?</p>', '', description, flags=re.IGNORECASE)

        # Strip application form content appended to job descriptions
        description = re.sub(r'<p>\s*Click or drag file to upload\s*</p>.*$', '', description, flags=re.IGNORECASE | re.DOTALL)
        description = re.sub(r'<p>\s*Application Questions\s*</p>.*$', '', description, flags=re.IGNORECASE | re.DOTALL)

        return description.strip()

    # For plain text, do more aggressive cleaning
    # Remove "Department" and related text patterns
    description = re.sub(r'Department\s*[·•]\s*[^·•\n]+', '', description, flags=re.IGNORECASE)
    description = re.sub(r'\bDepartment\b[·•\s-]*', '', description, flags=re.IGNORECASE)
    # Remove standalone "Remote" or "Full-time" mentions
    description = re.sub(r'\s*[·•]\s*Remote\s*[·•]?\s*', ' ', description, flags=re.IGNORECASE)
    description = re.sub(r'\s*[·•]\s*Full-time\s*[·•]?\s*', ' ', description, flags=re.IGNORECASE)
    description = re.sub(r'\s*[·•]\s*Part-time\s*[·•]?\s*', ' ', description, flags=re.IGNORECASE)
    # Clean up extra spaces and bullets
    description = re.sub(r'\s+', ' ', description)
    description = re.sub(r'[·•]\s*$', '', description)
    cleaned = description.strip()

    # If description is just the title repeated, return empty string
    if title and cleaned.lower() == title.lower():
        return ''

    return cleaned

def clean_job_type(job_type):
    """Clean job type field by removing location and extra text"""
    # Extract recognized job type keyword directly from the raw string
    type_match = re.search(r'\b(Full-time|Part-time|Contract|Temporary|Internship)\b', job_type, re.IGNORECASE)
    if type_match:
        return type_match.group(1)
    # Remove everything after and including "Department"
    job_type = re.split(r'Department\s*[·•]', job_type, flags=re.IGNORECASE)[0]
    # Remove location patterns like "St.George UT"
    job_type = re.sub(r'\s*[·•]\s*[A-Z][a-z]+\.?\s*[A-Z]{2}\s*', '', job_type)
    # Remove Remote, Full-time, Part-time
    job_type = re.sub(r'\s*[·•]?\s*(Remote|Full-time|Part-time)\s*[·•]?\s*', '', job_type, flags=re.IGNORECASE)
    # Clean up
    job_type = re.sub(r'\s+', ' ', job_type)
    job_type = re.sub(r'[·•]\s*$', '', job_type)
    cleaned = job_type.strip()

    # Default to "Full-time" if empty
    return cleaned if cleaned else 'Full-time'

def format_date_iso(date_str):
    """Convert date to ISO format for schema.org"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.isoformat()
    except:
        return datetime.now().isoformat()

def extract_location_parts(job):
    """Extract city, state, country from job data"""
    city = job.get('city', '').strip()
    state = job.get('state', '').strip()
    country = job.get('country', 'US').strip()

    # Check if remote
    is_remote = city.lower() == 'remote' or 'remote' in job.get('title', '').lower()

    # Try to extract location from jobtype or title if not already set
    if not city or city.lower() == 'remote':
        jobtype = job.get('jobtype', '')
        raw_title = job.get('title', '')
        # Look for location patterns like "St.George UT" or "St. George, UT"
        location_match = re.search(r'(St\.?\s*George)\s*,?\s*(UT|Utah)', jobtype, re.IGNORECASE)
        if location_match:
            city = 'St. George'
            state = 'UT'
            is_remote = False
        # Extract Gold Coast from concatenated title (e.g. "Account ExecutiveGold Coast")
        elif re.search(r'Gold\s*Coast', raw_title, re.IGNORECASE):
            city = 'Gold Coast'
            state = 'QLD'
            country = 'AU'
            is_remote = False

    return {
        'city': city,
        'state': state,
        'country': country,
        'is_remote': is_remote
    }

def generate_job_schema(job, job_url):
    """Generate JSON-LD schema for JobPosting"""
    location_info = extract_location_parts(job)

    # Build location object
    if location_info['is_remote']:
        location_schema = {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": location_info['country']
            }
        }
        applicant_location = {
            "@type": "Country",
            "name": "US"
        }
    else:
        location_schema = {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": location_info['city'],
                "addressRegion": location_info['state'],
                "addressCountry": location_info['country']
            }
        }
        applicant_location = None

    schema = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": job.get('title', ''),
        "description": job.get('description', ''),
        "identifier": {
            "@type": "PropertyValue",
            "name": COMPANY_NAME,
            "value": job.get('id') or job.get('referencenumber')
        },
        "datePosted": format_date_iso(job.get('date', '')),
        "hiringOrganization": {
            "@type": "Organization",
            "name": COMPANY_NAME,
            "sameAs": COMPANY_URL,
            "logo": COMPANY_LOGO
        },
        "jobLocation": location_schema,
        "employmentType": job.get('jobtype', 'FULL_TIME').upper().replace(' ', '_').replace('-', '_'),
        "url": job_url,
        "applicantLocationRequirements": applicant_location if applicant_location else None
    }

    # Remove None values
    schema = {k: v for k, v in schema.items() if v is not None}

    return json.dumps(schema, indent=2)

def generate_job_page(job, index=0):
    """Generate individual job detail page"""
    job_id = job.get('id') or job.get('referencenumber') or f"job-{index}"
    slug = slugify(job.get('title', f'position-{index}'))
    filename = f"{slug}-{job_id}.html"
    job_url = f"{COMPANY_URL}/careers/{filename}"

    location_info = extract_location_parts(job)

    # Format location display - show actual office location
    if location_info['city'] and location_info['city'].lower() != 'remote':
        location_display = f"{location_info['city']}, {location_info['state']}" if location_info['state'] else location_info['city']
    else:
        location_display = "St. George, UT"  # Default to main office

    # Generate schema
    schema_json = generate_job_schema(job, job_url)

    # Format title with line breaks
    formatted_title = format_title_with_breaks(job.get('title', ''))

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{escape(job.get('title', ''))} at {COMPANY_NAME}. {escape(job.get('description', '')[:150])}">
    <meta name="robots" content="index, follow">
    <title>{escape(job.get('title', ''))} - Careers at {COMPANY_NAME}</title>
    <link rel="canonical" href="{job_url}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/careers/careers.css">

    <!-- Structured Data for Job Posting -->
    <script type="application/ld+json">
{schema_json}
    </script>
</head>
<body>
    <header class="site-header">
        <div class="container">
            <a href="{COMPANY_URL}" class="logo">
                <svg class="logo-svg" viewBox="0 0 1020 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Zonos" fill="currentColor"><path d="M464 63H354a4 4 0 0 0-4 4v24a4 4 0 0 0 4 4h64.533c1.642 0 2.584 1.87 1.607 3.19l-68.571 92.69a7.999 7.999 0 0 0-1.569 4.758V213a4 4 0 0 0 4 4h110a4 4 0 0 0 4-4v-24a4 4 0 0 0-4-4h-64.533c-1.642 0-2.584-1.869-1.607-3.189l68.571-92.69A8 8 0 0 0 468 84.362V67a4 4 0 0 0-4-4Z"/><path fill-rule="evenodd" clip-rule="evenodd" d="M532 62c-24.301 0-44 19.7-44 44v68c0 24.301 19.699 44 44 44h30c24.301 0 44-19.699 44-44v-68c0-24.3-19.699-44-44-44h-30Zm0 32c-6.627 0-12 5.373-12 12v68c0 6.627 5.373 12 12 12h30c6.627 0 12-5.373 12-12v-68c0-6.627-5.373-12-12-12h-30Z"/><path d="M626 68.806v144.69a4 4 0 0 0 4 4h24a4 4 0 0 0 4-4v-93.028c0-4.675 2.716-8.925 6.959-10.89l30-13.888C702.911 92.008 712 97.816 712 106.579v106.917a4 4 0 0 0 4 4h24a4 4 0 0 0 4-4V106.552c0-32.13-33.32-53.426-62.48-39.931l-20.724 9.59a4 4 0 0 1-4.761-1.079l-6.15-7.428a7.999 7.999 0 0 0-6.162-2.898H630a4 4 0 0 0-4 4Z"/><path fill-rule="evenodd" clip-rule="evenodd" d="M808 62c-24.301 0-44 19.7-44 44v68c0 24.301 19.699 44 44 44h30c24.301 0 44-19.699 44-44v-68c0-24.3-19.699-44-44-44h-30Zm0 32c-6.627 0-12 5.373-12 12v68c0 6.627 5.373 12 12 12h30c6.627 0 12-5.373 12-12v-68c0-6.627-5.373-12-12-12h-30Z"/><path d="M945.254 63h34.015C1001.76 63 1020 81.236 1020 103.731a3.701 3.701 0 0 1-3.24 3.674l-25.256 3.157a3.117 3.117 0 0 1-3.504-3.093C988 100.583 982.417 95 975.531 95h-28.229C939.955 95 934 100.955 934 108.302a13.302 13.302 0 0 0 10.45 12.992l41.1 9.022c20.12 4.416 34.45 22.236 34.45 42.832 0 24.219-19.63 43.852-43.852 43.852h-33.417C920.236 217 902 198.764 902 176.269a3.702 3.702 0 0 1 3.244-3.674l25.252-3.157a3.117 3.117 0 0 1 3.504 3.093c0 6.886 5.583 12.469 12.469 12.469h28.567c7.16 0 12.964-5.804 12.964-12.964 0-5.909-3.995-11.07-9.715-12.551l-43.872-11.358C915.329 143.186 902 125.967 902 106.254 902 82.365 921.365 63 945.254 63ZM20 145C20 78.726 73.726 25 140 25s120 53.726 120 120c0 43.67-23.326 81.899-58.218 102.895a1.973 1.973 0 0 1-2.762-.782l-4.672-8.868a2.03 2.03 0 0 1 .751-2.674C225.613 216.97 246 183.369 246 145c0-31.51-13.755-59.814-35.572-79.222l-.749-.666a4 4 0 0 0-5.653.337l-13.351 15.08C176.728 69.551 159.124 63 140 63c-45.287 0-82 36.713-82 82 0 31.57 17.842 58.964 43.968 72.665l.886.464a3.999 3.999 0 0 0 5.399-1.684l8.545-16.287c.482-.918 1.585-1.312 2.554-.943A57.874 57.874 0 0 0 140 203c32.033 0 58-25.967 58-58s-25.967-58-58-58h-1a4 4 0 0 0-4 4v18.638c0 .992-.729 1.828-1.702 2.022C117.73 114.773 106 128.516 106 145c0 10.218 4.513 19.387 11.638 25.612A33.891 33.891 0 0 0 140 179c18.778 0 34-15.222 34-34 0-16.484-11.73-30.227-27.298-33.34-.973-.194-1.702-1.03-1.702-2.022V99.475c0-1.186 1.027-2.115 2.2-1.939C170.294 101.01 188 120.938 188 145c0 26.51-21.49 48-48 48-8.035 0-15.594-1.97-22.237-5.449l-.885-.464a4 4 0 0 0-5.398 1.685l-8.218 15.663c-.538 1.026-1.836 1.383-2.804.746C80.898 192.302 68 170.154 68 145c0-39.765 32.235-72 72-72 18.381 0 35.144 6.882 47.869 18.217l.749.667a4 4 0 0 0 5.656-.335l11.766-13.29c.76-.859 2.088-.905 2.886-.081C225.69 95.465 236 119.026 236 145c0 36.979-20.906 69.082-51.567 85.122C171.152 237.069 156.043 241 140 241c-40.86 0-75.771-25.53-89.626-61.527l-.358-.929a4 4 0 0 0-5.154-2.302l-16.673 6.336a1.973 1.973 0 0 1-2.589-1.237C21.963 169.883 20 157.675 20 145Z"/><path d="M116 145c0-13.255 10.745-24 24-24s24 10.745 24 24-10.745 24-24 24c-6.047 0-11.56-2.23-15.782-5.918C119.174 158.675 116 152.211 116 145Z"/><path fill-rule="evenodd" clip-rule="evenodd" d="M38.828 201.783a2.025 2.025 0 0 0-2.48-.91l-18 6.84a4 4 0 0 1-5.155-2.305l-3.93-10.233C3.276 179.579 0 162.654 0 145 0 67.68 62.68 5 140 5s140 62.68 140 140c0 53.923-30.489 100.699-75.097 124.076l-9.722 5.094a4 4 0 0 1-5.395-1.678l-8.972-17.028a2.025 2.025 0 0 0-2.464-.958C166.333 258.715 153.422 261 140 261c-43.458 0-81.305-23.895-101.172-59.217Zm146.654 41.089a2.027 2.027 0 0 0-2.618-.897C169.753 247.778 155.247 251 140 251c-42.695 0-79.483-25.24-96.278-61.597a2.03 2.03 0 0 0-2.558-1.058l-17.052 6.48a4 4 0 0 1-5.155-2.305l-.358-.93C13.043 177.12 10 161.409 10 145 10 73.203 68.203 15 140 15s130 58.203 130 130c0 50.058-28.294 93.499-69.739 115.218l-.884.463a4 4 0 0 1-5.395-1.678l-8.5-16.131Z"/></svg>
            </a>
            <nav>
                <a href="index.html">← All Jobs</a>
            </nav>
        </div>
    </header>

    <main class="job-detail">
        <div class="container">
            <article>
                <header class="job-header">
                    <h1>{formatted_title}</h1>
                    <div class="job-meta">
                        <span class="meta-item">
                            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M8 16s6-5.686 6-10A6 6 0 0 0 2 6c0 4.314 6 10 6 10zm0-7a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/>
                            </svg>
                            {escape(location_display)}
                        </span>
                        <span class="meta-item">
                            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M1 2.5A1.5 1.5 0 0 1 2.5 1h3A1.5 1.5 0 0 1 7 2.5v3A1.5 1.5 0 0 1 5.5 7h-3A1.5 1.5 0 0 1 1 5.5v-3zM2.5 2a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-3zm6.5.5A1.5 1.5 0 0 1 10.5 1h3A1.5 1.5 0 0 1 15 2.5v3A1.5 1.5 0 0 1 13.5 7h-3A1.5 1.5 0 0 1 9 5.5v-3zm1.5-.5a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-3zM1 10.5A1.5 1.5 0 0 1 2.5 9h3A1.5 1.5 0 0 1 7 10.5v3A1.5 1.5 0 0 1 5.5 15h-3A1.5 1.5 0 0 1 1 13.5v-3zm1.5-.5a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-3zm6.5.5A1.5 1.5 0 0 1 10.5 9h3a1.5 1.5 0 0 1 1.5 1.5v3a1.5 1.5 0 0 1-1.5 1.5h-3A1.5 1.5 0 0 1 9 13.5v-3zm1.5-.5a.5.5 0 0 0-.5.5v3a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 .5-.5v-3a.5.5 0 0 0-.5-.5h-3z"/>
                            </svg>
                            {escape(job.get('jobtype', 'Full-time'))}
                        </span>
                        <span class="meta-item">
                            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M4 .5a.5.5 0 0 0-1 0V1H2a2 2 0 0 0-2 2v1h16V3a2 2 0 0 0-2-2h-1V.5a.5.5 0 0 0-1 0V1H4V.5zM16 14V5H0v9a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2zm-3.5-7h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5z"/>
                            </svg>
                            Posted {escape(job.get('date', ''))}
                        </span>
                    </div>
                    <div class="job-actions">
                        <a href="{escape(job.get('url', '#'))}" class="btn btn-primary" target="_blank" rel="noopener">Apply Now</a>
                    </div>
                </header>

                {f'''<section class="job-description">
                    <div class="description-content">
                        <p>We're looking for a talented professional to join our team in this role. This position offers an opportunity to work with cutting-edge technology and contribute to our mission of creating trust in global trade.</p>
                        <p>For detailed information about responsibilities, qualifications, and benefits, please click "Apply Now" to view the full job posting.</p>
                    </div>
                </section>''' if not job.get('description') else f'''<section class="job-description">
                    <div class="description-content">
                        {job.get('description')}
                    </div>
                </section>'''}

                <section class="job-apply">
                    <h2>Ready to Join the Team?</h2>
                    <p>Become a Zonut and help us create trust in global trade. We're building something meaningful—a company that puts people first and makes cross-border commerce accessible to everyone. If you're passionate about solving complex challenges with cutting-edge technology, we'd love to meet you.</p>
                    <a href="{escape(job.get('url', '#'))}" class="btn btn-primary" target="_blank" rel="noopener">Apply for this Position</a>
                </section>
            </article>
        </div>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p>&copy; {datetime.now().year} {COMPANY_NAME}. All rights reserved.</p>
            <nav>
                <a href="{COMPANY_URL}">Home</a>
                <a href="{COMPANY_URL}/careers/">Careers</a>
            </nav>
        </div>
    </footer>
</body>
</html>"""

    return filename, html

def generate_index_page(jobs):
    """Generate main careers landing page"""

    # Count jobs
    job_count = len(jobs)

    # Generate job cards
    job_cards_html = ""
    for i, job in enumerate(jobs):
        job_id = job.get('id') or job.get('referencenumber') or f"job-{i}"
        slug = slugify(job.get('title', f'position-{i}'))
        filename = f"{slug}-{job_id}.html"

        location_info = extract_location_parts(job)
        # Show the actual office location
        if location_info['city'] and location_info['city'].lower() != 'remote':
            location_display = f"{location_info['city']}, {location_info['state']}" if location_info['state'] else location_info['city']
        else:
            location_display = "St. George, UT"  # Default to main office

        formatted_title = format_title_with_breaks(job.get('title', ''))

        job_cards_html += f"""
                <article class="job-card">
                    <h3><a href="{filename}">{formatted_title}</a></h3>
                    <div class="job-card-meta">
                        <span class="location">{escape(location_display)}</span>
                        <span class="type">{escape(job.get('jobtype', 'Full-time'))}</span>
                    </div>
                    <a href="{filename}" class="btn btn-secondary">View Details</a>
                </article>"""

    if not job_cards_html:
        job_cards_html = """
                <div class="no-jobs">
                    <p>We don't have any open positions at the moment, but we're always looking for talented individuals!</p>
                    <p>Check back soon or send us your resume at careers@zonos.com</p>
                </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Join the {COMPANY_NAME} team. Explore career opportunities and help us shape the future of cross-border e-commerce.">
    <meta name="robots" content="index, follow">
    <title>Careers at {COMPANY_NAME} - Join Our Team</title>
    <link rel="canonical" href="{COMPANY_URL}/careers/">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/careers/careers.css">

    <!-- Open Graph -->
    <meta property="og:title" content="Careers at {COMPANY_NAME}">
    <meta property="og:description" content="Join our team and help shape the future of cross-border commerce. {job_count} open positions.">
    <meta property="og:url" content="{COMPANY_URL}/careers/">
    <meta property="og:type" content="website">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Careers at {COMPANY_NAME}">
    <meta name="twitter:description" content="Join our team. {job_count} open positions.">
</head>
<body>
    <header class="site-header">
        <div class="container">
            <a href="{COMPANY_URL}" class="logo">
                <svg class="logo-svg" viewBox="0 0 1020 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Zonos" fill="currentColor"><path d="M464 63H354a4 4 0 0 0-4 4v24a4 4 0 0 0 4 4h64.533c1.642 0 2.584 1.87 1.607 3.19l-68.571 92.69a7.999 7.999 0 0 0-1.569 4.758V213a4 4 0 0 0 4 4h110a4 4 0 0 0 4-4v-24a4 4 0 0 0-4-4h-64.533c-1.642 0-2.584-1.869-1.607-3.189l68.571-92.69A8 8 0 0 0 468 84.362V67a4 4 0 0 0-4-4Z"/><path fill-rule="evenodd" clip-rule="evenodd" d="M532 62c-24.301 0-44 19.7-44 44v68c0 24.301 19.699 44 44 44h30c24.301 0 44-19.699 44-44v-68c0-24.3-19.699-44-44-44h-30Zm0 32c-6.627 0-12 5.373-12 12v68c0 6.627 5.373 12 12 12h30c6.627 0 12-5.373 12-12v-68c0-6.627-5.373-12-12-12h-30Z"/><path d="M626 68.806v144.69a4 4 0 0 0 4 4h24a4 4 0 0 0 4-4v-93.028c0-4.675 2.716-8.925 6.959-10.89l30-13.888C702.911 92.008 712 97.816 712 106.579v106.917a4 4 0 0 0 4 4h24a4 4 0 0 0 4-4V106.552c0-32.13-33.32-53.426-62.48-39.931l-20.724 9.59a4 4 0 0 1-4.761-1.079l-6.15-7.428a7.999 7.999 0 0 0-6.162-2.898H630a4 4 0 0 0-4 4Z"/><path fill-rule="evenodd" clip-rule="evenodd" d="M808 62c-24.301 0-44 19.7-44 44v68c0 24.301 19.699 44 44 44h30c24.301 0 44-19.699 44-44v-68c0-24.3-19.699-44-44-44h-30Zm0 32c-6.627 0-12 5.373-12 12v68c0 6.627 5.373 12 12 12h30c6.627 0 12-5.373 12-12v-68c0-6.627-5.373-12-12-12h-30Z"/><path d="M945.254 63h34.015C1001.76 63 1020 81.236 1020 103.731a3.701 3.701 0 0 1-3.24 3.674l-25.256 3.157a3.117 3.117 0 0 1-3.504-3.093C988 100.583 982.417 95 975.531 95h-28.229C939.955 95 934 100.955 934 108.302a13.302 13.302 0 0 0 10.45 12.992l41.1 9.022c20.12 4.416 34.45 22.236 34.45 42.832 0 24.219-19.63 43.852-43.852 43.852h-33.417C920.236 217 902 198.764 902 176.269a3.702 3.702 0 0 1 3.244-3.674l25.252-3.157a3.117 3.117 0 0 1 3.504 3.093c0 6.886 5.583 12.469 12.469 12.469h28.567c7.16 0 12.964-5.804 12.964-12.964 0-5.909-3.995-11.07-9.715-12.551l-43.872-11.358C915.329 143.186 902 125.967 902 106.254 902 82.365 921.365 63 945.254 63ZM20 145C20 78.726 73.726 25 140 25s120 53.726 120 120c0 43.67-23.326 81.899-58.218 102.895a1.973 1.973 0 0 1-2.762-.782l-4.672-8.868a2.03 2.03 0 0 1 .751-2.674C225.613 216.97 246 183.369 246 145c0-31.51-13.755-59.814-35.572-79.222l-.749-.666a4 4 0 0 0-5.653.337l-13.351 15.08C176.728 69.551 159.124 63 140 63c-45.287 0-82 36.713-82 82 0 31.57 17.842 58.964 43.968 72.665l.886.464a3.999 3.999 0 0 0 5.399-1.684l8.545-16.287c.482-.918 1.585-1.312 2.554-.943A57.874 57.874 0 0 0 140 203c32.033 0 58-25.967 58-58s-25.967-58-58-58h-1a4 4 0 0 0-4 4v18.638c0 .992-.729 1.828-1.702 2.022C117.73 114.773 106 128.516 106 145c0 10.218 4.513 19.387 11.638 25.612A33.891 33.891 0 0 0 140 179c18.778 0 34-15.222 34-34 0-16.484-11.73-30.227-27.298-33.34-.973-.194-1.702-1.03-1.702-2.022V99.475c0-1.186 1.027-2.115 2.2-1.939C170.294 101.01 188 120.938 188 145c0 26.51-21.49 48-48 48-8.035 0-15.594-1.97-22.237-5.449l-.885-.464a4 4 0 0 0-5.398 1.685l-8.218 15.663c-.538 1.026-1.836 1.383-2.804.746C80.898 192.302 68 170.154 68 145c0-39.765 32.235-72 72-72 18.381 0 35.144 6.882 47.869 18.217l.749.667a4 4 0 0 0 5.656-.335l11.766-13.29c.76-.859 2.088-.905 2.886-.081C225.69 95.465 236 119.026 236 145c0 36.979-20.906 69.082-51.567 85.122C171.152 237.069 156.043 241 140 241c-40.86 0-75.771-25.53-89.626-61.527l-.358-.929a4 4 0 0 0-5.154-2.302l-16.673 6.336a1.973 1.973 0 0 1-2.589-1.237C21.963 169.883 20 157.675 20 145Z"/><path d="M116 145c0-13.255 10.745-24 24-24s24 10.745 24 24-10.745 24-24 24c-6.047 0-11.56-2.23-15.782-5.918C119.174 158.675 116 152.211 116 145Z"/><path fill-rule="evenodd" clip-rule="evenodd" d="M38.828 201.783a2.025 2.025 0 0 0-2.48-.91l-18 6.84a4 4 0 0 1-5.155-2.305l-3.93-10.233C3.276 179.579 0 162.654 0 145 0 67.68 62.68 5 140 5s140 62.68 140 140c0 53.923-30.489 100.699-75.097 124.076l-9.722 5.094a4 4 0 0 1-5.395-1.678l-8.972-17.028a2.025 2.025 0 0 0-2.464-.958C166.333 258.715 153.422 261 140 261c-43.458 0-81.305-23.895-101.172-59.217Zm146.654 41.089a2.027 2.027 0 0 0-2.618-.897C169.753 247.778 155.247 251 140 251c-42.695 0-79.483-25.24-96.278-61.597a2.03 2.03 0 0 0-2.558-1.058l-17.052 6.48a4 4 0 0 1-5.155-2.305l-.358-.93C13.043 177.12 10 161.409 10 145 10 73.203 68.203 15 140 15s130 58.203 130 130c0 50.058-28.294 93.499-69.739 115.218l-.884.463a4 4 0 0 1-5.395-1.678l-8.5-16.131Z"/></svg>
            </a>
        </div>
    </header>

    <main class="careers-page">
        <section class="hero">
            <div class="container">
                <h1>Join the Zonos Team</h1>
                <p class="hero-subtitle">Help us create trust in global trade and make cross-border commerce accessible to everyone</p>
            </div>
        </section>

        <section class="jobs-section">
            <div class="container">
                <div class="section-header">
                    <h2>Open Positions</h2>
                    <p class="job-count">{job_count} {"position" if job_count == 1 else "positions"} available</p>
                </div>

                <div class="jobs-grid">{job_cards_html}
                </div>
            </div>
        </section>

        <section class="company-culture">
            <div class="container">
                <h2>Building a Great Company</h2>
                <div class="culture-intro">
                    <p>At Zonos we provide scalable technology to simplify the complexities of international commerce, making it accessible to everyone. We create products that allow businesses to take complete control of their cross-border trade experience. Our SaaS solutions alleviate the headaches of cross-border trade with APIs and software that provide businesses with the tools and data they need to scale globally, including the only true landed cost solution on the market.</p>
                    <p>If you're looking to join a company with a strong mission and vision that puts people first, we want to meet you. As an organization, we are always striving to be a great company, not just a big company. We are constantly cultivating an environment of collaboration and teamwork, where our core values are the living, breathing heartbeat of everything we do.</p>
                </div>

                <div class="values-grid">
                    <div class="value-card">
                        <h3>Reach Everyone</h3>
                        <p>It's about people. We are empathetic and listen to each other. Our diverse perspectives make us stronger, and we create trust in global trade by putting humanity first.</p>
                    </div>
                    <div class="value-card">
                        <h3>Never Give Up, Never Surrender</h3>
                        <p>We execute with passion and persistence, tackling challenges head-on without burning out. We're here for the long haul, building something that lasts.</p>
                    </div>
                    <div class="value-card">
                        <h3>Do New</h3>
                        <p>Innovation drives us forward. We balance creativity with accountability, always pushing boundaries while taking ownership of our decisions.</p>
                    </div>
                    <div class="value-card">
                        <h3>You're Responsible for Customer Success</h3>
                        <p>We take direct responsibility for our clients' outcomes. Their success is our success, and we're committed to delivering solutions that truly work.</p>
                    </div>
                </div>

                <div class="office-locations">
                    <h3>Our Locations</h3>
                    <div class="offices-grid">
                        <div class="office">
                            <h4>🇺🇸 Utah, United States</h4>
                            <p>Headquartered in St. George, Utah, our team enjoys Southern Utah's 255 days of sunshine each year. Situated at Tech Ridge near the breathtaking Zion National Park, there's no shortage of hiking, biking, and outdoor adventure—all just 90 minutes from Las Vegas.</p>
                        </div>
                        <div class="office">
                            <h4>🇳🇱 Utrecht, Netherlands</h4>
                            <p>Our new European headquarters bringing Zonos closer to international clients and team members across the continent. Experience the perfect blend of Dutch innovation and work-life balance in one of Europe's most dynamic business hubs.</p>
                        </div>
                        <div class="office">
                            <h4>🇦🇺 Gold Coast, Australia</h4>
                            <p>Serving the Asia-Pacific region from Australia's stunning Gold Coast, where innovation meets the ocean. Enjoy year-round sunshine, world-class beaches, and a thriving tech community in one of the world's most livable cities.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p>&copy; {datetime.now().year} {COMPANY_NAME}. All rights reserved.</p>
            <p class="footer-note">Equal Opportunity Employer</p>
            <nav>
                <a href="{COMPANY_URL}">Home</a>
                <a href="{COMPANY_URL}/careers/">Careers</a>
            </nav>
        </div>
    </footer>
</body>
</html>"""

    return html

def main():
    """Main execution"""
    print("Fetching jobs from feed...")
    jobs = fetch_jobs()
    print(f"Found {len(jobs)} unique job(s)")

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Generate individual job pages
    print("Generating job detail pages...")
    for i, job in enumerate(jobs):
        filename, html = generate_job_page(job, i)
        output_path = OUTPUT_DIR / filename
        output_path.write_text(html, encoding='utf-8')
        print(f"  Created: {filename}")

    # Generate index page
    print("Generating careers index page...")
    index_html = generate_index_page(jobs)
    index_path = OUTPUT_DIR / "index.html"
    index_path.write_text(index_html, encoding='utf-8')
    print(f"  Created: index.html")

    # Copy CSS file
    print("Copying stylesheet and assets...")
    import shutil

    css_source = Path(__file__).parent / "careers.css"
    css_dest = OUTPUT_DIR / "careers.css"
    if css_source.exists():
        shutil.copy2(css_source, css_dest)
        print(f"  Created: careers.css")
    else:
        print(f"  Warning: careers.css not found at {css_source}")

    # Copy logo file
    logo_source = Path(__file__).parent / "careers" / "zonos-logo-black.png"
    logo_dest = OUTPUT_DIR / "zonos-logo-black.png"
    if logo_source.exists() and logo_source.resolve() != logo_dest.resolve():
        shutil.copy2(logo_source, logo_dest)
        print(f"  Created: zonos-logo-black.png")
    elif logo_dest.exists():
        print(f"  Logo already exists: zonos-logo-black.png")
    else:
        print(f"  Warning: logo not found at {logo_source}")

    print(f"\n✓ Successfully generated careers pages in {OUTPUT_DIR}/")
    print(f"  - 1 index page")
    print(f"  - {len(jobs)} job detail page(s)")
    print(f"  - 1 stylesheet")
    print(f"  - 1 logo")

if __name__ == "__main__":
    main()
