# 🚀 Deel Job Feed Scraper for Zonos

Automated job feed generator that scrapes your Deel job board and creates XML/RSS feeds for job aggregators like Indeed, Google Jobs, and more.

## 📋 Problem Solved

Deel's ATS doesn't provide native XML feeds for job aggregators, making it difficult for jobs to be discovered on Indeed, Google Jobs, and other platforms. This tool automatically:

- ✅ Scrapes your Deel job board every 6 hours
- ✅ Generates multiple feed formats (RSS, Indeed XML, Google Jobs JSON)
- ✅ Hosts feeds publicly via GitHub Pages
- ✅ Requires zero maintenance after setup

## 🎯 Feed Formats

This scraper generates 4 different feed formats:

1. **RSS 2.0** (`feeds/jobs.rss`) - Universal RSS format
2. **Indeed XML** (`feeds/indeed.xml`) - Indeed's proprietary format
3. **Google Jobs JSON-LD** (`feeds/google-jobs.json`) - Google Jobs structured data
4. **Raw JSON** (`feeds/jobs.json`) - For custom integrations

## 🚀 Quick Setup (5 minutes)

### Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Create a new **public** repository named `deel-job-feed` (or any name you prefer)
3. **Do NOT** initialize with README, .gitignore, or license

### Step 2: Push This Code

```bash
cd deel-job-feed-scraper
git init
git add .
git commit -m "Initial commit: Deel job feed scraper"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/deel-job-feed.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username.

### Step 3: Enable GitHub Actions

1. Go to your repository on GitHub
2. Click **Actions** tab
3. If prompted, click "I understand my workflows, go ahead and enable them"
4. The scraper will run automatically every 6 hours

### Step 4: Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Under "Source", select **Deploy from a branch**
3. Select branch: **main** and folder: **/ (root)**
4. Click **Save**
5. Wait 2-3 minutes for deployment

### Step 5: Run First Scrape (Optional)

To generate feeds immediately instead of waiting:

1. Go to **Actions** tab
2. Click "Scrape Deel Jobs" workflow
3. Click **Run workflow** → **Run workflow**
4. Wait 1-2 minutes for completion

### Step 6: Get Your Feed URLs

Your feeds will be available at:

```
https://YOUR-USERNAME.github.io/deel-job-feed/feeds/jobs.rss
https://YOUR-USERNAME.github.io/deel-job-feed/feeds/indeed.xml
https://YOUR-USERNAME.github.io/deel-job-feed/feeds/google-jobs.json
```

Or visit:
```
https://YOUR-USERNAME.github.io/deel-job-feed/
```

for a nice landing page with all feed URLs.

## 📤 Submitting to Job Boards

### Indeed

1. Log into [Indeed Employer](https://employers.indeed.com/)
2. Go to **Job Management** → **Job Feed**
3. Click **Add Feed** or **XML Feed**
4. Enter your Indeed XML feed URL:
   ```
   https://YOUR-USERNAME.github.io/deel-job-feed/feeds/indeed.xml
   ```
5. Indeed will validate and sync jobs every 24 hours

### Google Jobs

Google Jobs pulls from your website's structured data:

1. Add the JSON-LD from `feeds/google-jobs.json` to your website's job pages
2. Or use Google's [Job Posting Schema](https://developers.google.com/search/docs/appearance/structured-data/job-posting)
3. Test with [Rich Results Test](https://search.google.com/test/rich-results)

### LinkedIn

1. Go to [LinkedIn Jobs](https://www.linkedin.com/jobs/)
2. Click **Post a job**
3. LinkedIn doesn't accept feeds - you'll need to post manually or use their API

### ZipRecruiter / Glassdoor / Monster

Most other job boards accept RSS feeds:

1. Find their "XML Feed" or "Job Feed" integration
2. Submit your RSS feed URL:
   ```
   https://YOUR-USERNAME.github.io/deel-job-feed/feeds/jobs.rss
   ```

## 🔧 Customization

### Change Scraping Frequency

Edit `.github/workflows/scrape-jobs.yml`:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
  # Change to:
  - cron: '0 */3 * * *'  # Every 3 hours
  - cron: '0 0 * * *'    # Once daily at midnight
  - cron: '0 8,17 * * *' # 8am and 5pm daily
```

### Update Company Info

Edit `scrape_jobs.py`:

```python
COMPANY_NAME = "Zonos"
COMPANY_URL = "https://zonos.com"
DEEL_JOB_BOARD_URL = "https://jobs.deel.com/job-boards/zonos"
```

### Test Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run scraper
python scrape_jobs.py

# Check generated feeds
ls -la feeds/
```

## 📊 How It Works

1. **GitHub Actions** runs Python script every 6 hours
2. **Python script** fetches your Deel job board page
3. **BeautifulSoup** parses HTML and extracts job listings
4. **XML/JSON generators** create feed files in multiple formats
5. **GitHub Pages** hosts feeds publicly at a permanent URL
6. **Job aggregators** fetch your feeds automatically

## 🐛 Troubleshooting

### No jobs appearing in feeds?

1. Check that jobs are published on your Deel board: https://jobs.deel.com/job-boards/zonos
2. Run the workflow manually to see errors: **Actions** → **Run workflow**
3. Check `feeds/jobs.json` to see what data was scraped

### Deel changed their HTML structure?

The scraper uses flexible selectors but may need updates if Deel changes their page structure significantly. Check the Actions logs for errors.

### Feeds not updating?

1. Check that GitHub Actions is enabled
2. Go to **Actions** tab and verify workflows are running
3. Check for any error messages in workflow logs

### GitHub Pages not working?

1. Ensure repository is **public** (GitHub Pages is free for public repos only)
2. Wait 2-3 minutes after enabling Pages
3. Check **Settings** → **Pages** for deployment status

## 📝 License

MIT License - feel free to use and modify as needed.

## 🆘 Support

- **Deel Structure Changed?** Update the parsing logic in `scrape_jobs.py`
- **Need Different Format?** Add a new generator function
- **Custom Requirements?** Fork and modify as needed

---

**Built with ❤️ to solve Deel's missing job feed feature**

Made by Claude Code
