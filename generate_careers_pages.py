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
        response = requests.get(FEED_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

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

            # If we haven't seen this job, or this version has a better URL, use it
            if unique_key not in seen_urls or '/job-details/' in url:
                seen_urls[unique_key] = {
                    'title': cleaned_title,
                    'url': url,
                    'location': job.get('location', ''),
                    'city': job.get('city', job.get('location', '')),
                    'state': job.get('state', ''),
                    'country': job.get('country', 'US'),
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
    # Remove everything after common delimiters
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

    # Try to extract location from jobtype or description if not already set
    if not city or city.lower() == 'remote':
        jobtype = job.get('jobtype', '')
        # Look for location patterns like "St.George UT" or "St. George, UT"
        location_match = re.search(r'(St\.?\s*George)\s*,?\s*(UT|Utah)', jobtype, re.IGNORECASE)
        if location_match:
            city = 'St. George'
            state = 'UT'
            is_remote = False  # If we found a specific location, it's not just remote

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
        location_display = f"{location_info['city']}, {location_info['state']}"
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
                <img src="/careers/zonos-logo-black.png" alt="{COMPANY_NAME}" />
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
                    <h2>About the Position</h2>
                    <div class="description-content">
                        <p>We're looking for a talented professional to join our team in this role. This position offers an opportunity to work with cutting-edge technology and contribute to our mission of creating trust in global trade.</p>
                        <p>For detailed information about responsibilities, qualifications, and benefits, please click "Apply Now" to view the full job posting.</p>
                    </div>
                </section>''' if not job.get('description') else f'''<section class="job-description">
                    <h2>About the Position</h2>
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
            location_display = f"{location_info['city']}, {location_info['state']}"
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
                <img src="/careers/zonos-logo-black.png" alt="{COMPANY_NAME}" />
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
                            <h4>🏜️ St. George, Utah</h4>
                            <p>Welcome to Southern Utah where the sun is shining 255 days out of the year! Located at Tech Ridge, neighboring the stunning Zion National Park with endless options for hiking, biking, and outdoor recreation. Just 90 minutes from Las Vegas.</p>
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
