# Claude Code Project Context

## Project: Deel Job Feed Scraper for Zonos

**Date Created:** February 11-12, 2026
**GitHub Repository:** https://github.com/Hanzo2401/deel-job-feed
**Live Feeds:** https://hanzo2401.github.io/deel-job-feed/

---

## Project Overview

Built a custom job feed scraper to solve Deel HR's missing XML feed functionality. Deel's ATS doesn't provide native feeds for job aggregators (Indeed, Google Jobs, etc.), making it impossible for jobs to be discovered on these platforms.

### Problem Solved
- **Issue:** Zonos moved from BambooHR to Deel and couldn't get job postings to appear on Indeed and other job aggregators
- **Root Cause:** Deel doesn't provide XML/RSS feeds for their job boards
- **Impact:** Zero applicants for weeks because jobs weren't searchable

### Solution Built
Custom Python scraper using Playwright that:
1. Scrapes jobs from Deel's JavaScript-rendered job board
2. Generates multiple feed formats (RSS, Indeed XML, Google Jobs JSON)
3. Auto-updates every 6 hours via GitHub Actions
4. Hosts feeds publicly on GitHub Pages (free)

---

## Technical Architecture

### Components

**1. Scraper (`scrape_jobs.py`)**
- Uses Playwright for browser automation (handles JavaScript rendering)
- Waits 15 seconds for Deel's loading screens to complete
- Parses job listings from HTML using BeautifulSoup
- Generates 4 feed formats
- Creates debug screenshot and HTML dump for troubleshooting

**2. Feed Formats Generated**
- `feeds/jobs.rss` - RSS 2.0 (universal format)
- `feeds/indeed.xml` - Indeed's proprietary XML format
- `feeds/google-jobs.json` - Google Jobs JSON-LD structured data
- `feeds/jobs.json` - Raw JSON for debugging/custom integrations

**3. Automation (GitHub Actions)**
- Runs on Ubuntu 22.04 (not 24.04 due to Playwright dependency issues)
- Schedule: Every 6 hours (`0 */6 * * *`)
- Auto-commits and pushes updated feeds
- Can be triggered manually via Actions tab

**4. Hosting (GitHub Pages)**
- Serves feeds from `main` branch
- Landing page (`index.html`) with all feed URLs
- Free, permanent URLs

---

## Repository Structure

```
deel-job-feed/
├── scrape_jobs.py              # Main scraper script
├── requirements.txt            # Python dependencies
├── index.html                  # Landing page
├── README.md                   # Setup documentation
├── .github/
│   └── workflows/
│       └── scrape-jobs.yml     # GitHub Actions workflow
└── feeds/
    ├── jobs.rss                # Generated RSS feed
    ├── indeed.xml              # Generated Indeed XML
    ├── google-jobs.json        # Generated Google Jobs JSON
    ├── jobs.json               # Generated raw JSON
    ├── debug-screenshot.png    # Debug screenshot
    └── debug-page.html         # Debug HTML dump
```

---

## Key Configuration

### Company Details
```python
DEEL_JOB_BOARD_URL = "https://jobs.deel.com/job-boards/zonos"
COMPANY_NAME = "Zonos"
COMPANY_URL = "https://zonos.com"
```

### Current Jobs Scraped
- Corporate Broker (Licensed Customs Broker)
- Location: St. George, UT
- Type: Full-time

---

## Feed URLs

### Production Feed URLs
```
RSS Feed:
https://hanzo2401.github.io/deel-job-feed/feeds/jobs.rss

Indeed XML Feed:
https://hanzo2401.github.io/deel-job-feed/feeds/indeed.xml

Google Jobs JSON:
https://hanzo2401.github.io/deel-job-feed/feeds/google-jobs.json

Landing Page:
https://hanzo2401.github.io/deel-job-feed/
```

### Indeed Submission
Submit this URL to Indeed Employer Dashboard → Job Feed:
```
https://hanzo2401.github.io/deel-job-feed/feeds/indeed.xml
```

---

## Technical Challenges Solved

### 1. JavaScript Rendering
**Problem:** Deel's job board is fully JavaScript-rendered; simple HTTP requests returned empty pages.
**Solution:** Implemented Playwright browser automation to render JavaScript before scraping.

### 2. Loading Screens
**Problem:** Deel shows multiple "flash screens" during loading; scraper was capturing before content loaded.
**Solution:** Added 15-second wait time (10s initial + 5s buffer) to ensure full rendering.

### 3. Ubuntu 24.04 Dependency Issues
**Problem:** Playwright installation failed on ubuntu-latest (24.04) due to `libasound2` package name change.
**Solution:** Pinned GitHub Actions runner to `ubuntu-22.04`.

### 4. GitHub Workflow Permissions
**Problem:** Git credentials lacked `workflow` scope; couldn't push workflow files programmatically.
**Solution:** Created workflow files manually through GitHub web interface.

### 5. Git Push Conflicts
**Problem:** Workflow sometimes fails pushing feeds due to concurrent updates.
**Solution:** Known issue; non-critical (feeds still generate successfully). Could add `git pull --rebase` before push if needed.

---

## Maintenance & Updates

### Update Scraping Frequency
Edit `.github/workflows/scrape-jobs.yml`:
```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
  # Change to:
  - cron: '0 */3 * * *'  # Every 3 hours
  - cron: '0 0 * * *'    # Daily at midnight
```

### Update Company Info
Edit `scrape_jobs.py`:
```python
COMPANY_NAME = "Zonos"
COMPANY_URL = "https://zonos.com"
DEEL_JOB_BOARD_URL = "https://jobs.deel.com/job-boards/zonos"
```

### Manual Trigger
1. Go to https://github.com/Hanzo2401/deel-job-feed/actions
2. Click "Scrape Deel Jobs"
3. Click "Run workflow"

### Debugging
If jobs aren't appearing:
1. Check `feeds/debug-screenshot.png` - shows what scraper sees
2. Check `feeds/debug-page.html` - raw HTML for analysis
3. Check Actions logs for errors

---

## Dependencies

### Python Packages
```
playwright==1.41.2
beautifulsoup4==4.12.3
lxml==5.1.0
```

### System Requirements
- Ubuntu 22.04
- Python 3.11
- Chromium browser (installed by Playwright)

---

## Success Metrics

### Before
- ✗ No job feed available
- ✗ Zero applicants
- ✗ Jobs not discoverable on Indeed/Google

### After
- ✅ 4 feed formats generated
- ✅ Auto-updates every 6 hours
- ✅ Publicly accessible feeds
- ✅ Ready for Indeed submission
- ✅ Zero cost (GitHub free tier)

---

## Future Enhancements (Optional)

1. **Deduplication:** Currently generates 3 entries for same job (from different selectors); could deduplicate by URL
2. **Job Details:** Could scrape individual job detail pages for full descriptions
3. **Error Notifications:** Add Slack/email notifications if scraping fails
4. **Multiple Job Boards:** Could extend to scrape from multiple sources
5. **Git Pull Before Push:** Add `git pull --rebase` to workflow to prevent push failures

---

## Important Notes

- **Do not** change workflow files locally and push; GitHub credentials lack `workflow` scope
- Edit workflow files through GitHub web interface only
- Feeds may show duplicates (3x same job); non-critical but could be cleaned up
- Screenshot/HTML debug files commit to repo; useful for troubleshooting
- GitHub Pages takes 2-3 minutes to deploy after enabling

---

## Commands Reference

### Local Testing
```bash
cd deel-job-feed-scraper
pip install -r requirements.txt
python -m playwright install chromium
python scrape_jobs.py
```

### Git Operations
```bash
git add .
git commit -m "Update message"
git push origin main
```

### GitHub CLI
```bash
# Trigger workflow
gh workflow run "Scrape Deel Jobs" --repo Hanzo2401/deel-job-feed

# Check runs
gh run list --repo Hanzo2401/deel-job-feed --limit 5

# View run logs
gh run view RUN_ID --repo Hanzo2401/deel-job-feed --log
```

---

## Contact & Support

**Built for:** Zonos
**User:** hannahhuegel (GitHub: Hanzo2401)
**Built by:** Claude Code (Anthropic)
**Date:** February 2026

For issues or questions about this setup, refer to:
- Repository README: https://github.com/Hanzo2401/deel-job-feed/blob/main/README.md
- GitHub Actions logs: https://github.com/Hanzo2401/deel-job-feed/actions
- This context file: `CLAUDE.md`

---

## Job Description Formatting Pattern

**IMPORTANT:** This formatting pattern MUST be preserved for all future job postings.

### Sections to Extract (in order)
The scraper extracts ONLY these sections from the Deel job posting Overview tab:

1. **Intro Paragraph** - Starts with "At Zonos..." through "This position is based in [Location]. Relocation assistance provided."
2. **About the Role** - Paragraph format
3. **What You'll Work On** - Bullet list format (5 items typically)
4. **Why This Role is Different** - Paragraph format
5. **What We're Looking For** - Paragraph format
6. **Required** - Bullet list format (requirements)
7. **What We Offer** - Bullet list format (benefits)

### Sections to EXCLUDE
- ❌ Life at Zonos
- ❌ Application form fields
- ❌ Navigation/boilerplate text

### HTML Structure
```html
<!-- Intro paragraphs (2-3 <p> tags) -->
<p>At Zonos we provide scalable technology...</p>
<p>This position is based in St. George, Utah. Relocation assistance is provided.</p>

<!-- Each section has <h3> header + content -->
<h3>About the Role</h3>
<p>Description paragraph...</p>

<h3>What You'll Work On</h3>
<ul>
  <li>Bullet point 1</li>
  <li>Bullet point 2</li>
  ...
</ul>

<h3>Why This Role is Different</h3>
<p>Description paragraph...</p>

<!-- Continue pattern for remaining sections -->
```

### Formatting Rules
1. ✅ **Preserve bullet points** - Use `<ul>` and `<li>` tags for lists
2. ✅ **Section headers** - Use `<h3>` tags (NOT `<h2>`)
3. ✅ **Paragraphs** - Use `<p>` tags for text blocks
4. ✅ **NO "About the Position" heading** - Start directly with content
5. ✅ **St. George, Utah** - Protect from sentence splitting
6. ✅ **Clean structure** - 6 sections, 3 bullet lists, ~4,200 characters

### Implementation Location
- **Scraper:** `/scrape_jobs.py` - `fetch_job_details()` function (lines ~100-200)
- **Generator:** `/generate_careers_pages.py` - Job page template (lines ~340-360)

### Validation
Expected output for each job:
- 6 `<h3>` section headers
- 6 `<p>` paragraph blocks minimum
- 3 `<ul>` bullet lists
- 15-20 `<li>` items total
- ~4,000-4,500 characters

---

**Status:** ✅ Production Ready - Feeds Live and Updating with Proper Formatting
