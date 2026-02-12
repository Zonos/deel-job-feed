# Zonos Career Page - Complete Guide

**Project Name:** "New Career Page"
**Purpose:** Auto-updating careers page integrated into zonos.com from GitHub Pages

---

## 📍 Repository Locations

### Local Development
- **Local Path:** `/Users/hannahhuegel/deel-job-feed-scraper`
- **Primary Files:**
  - `generate_careers_pages.py` - Page generator script
  - `careers.css` - Styling
  - `careers/` - Generated HTML pages (auto-generated, don't edit directly)

### GitHub Repositories
- **Source Repo:** `https://github.com/Zonos/deel-job-feed`
- **Integration Repo:** `https://github.com/Zonos/zonos.com` (PR #2754)

### Live URLs
- **GitHub Pages:** https://zonos.github.io/deel-job-feed/careers/
- **Production:** https://zonos.com/careers (after PR merge)
- **Dev:** https://dev.zonos.com/careers (after PR merge)

---

## 🏗️ Architecture Overview

```
Deel Job Feed (JSON)
        ↓
GitHub Actions (every 6 hours)
        ↓
generate_careers_pages.py
        ↓
Static HTML + CSS in careers/
        ↓
GitHub Pages (zonos.github.io/deel-job-feed/careers/)
        ↓
Next.js Rewrite (zonos.com → GitHub Pages)
        ↓
zonos.com/careers
```

### How It Works
1. **Job Data:** Scraped from Deel and saved as JSON
2. **Generation:** Python script converts JSON → HTML
3. **GitHub Actions:** Auto-runs every 6 hours
4. **GitHub Pages:** Hosts the static HTML
5. **Next.js Rewrite:** Serves GitHub Pages content at zonos.com/careers

**Key Benefit:** No manual updates needed - jobs auto-sync from Deel!

---

## 🎨 Making Changes to the Careers Page

### 1. **Update Styling (Colors, Fonts, Layout)**

**File:** `careers.css`

**Common Changes:**
```css
/* Colors - Lines 3-14 (CSS variables) */
:root {
  --primary-color: #your-color;
  --accent-color: #your-color;
}

/* Fonts - Line 25 */
body {
  font-family: 'Your Font', sans-serif;
}

/* Layout - Adjust grid settings */
.job-grid {
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}
```

**Workflow:**
```bash
cd /Users/hannahhuegel/deel-job-feed-scraper
# Edit careers.css
git add careers.css
git commit -m "Update careers page styling"
git push
```

---

### 2. **Update Company Info / "Why Work Here" Section**

**File:** `generate_careers_pages.py`
**Location:** Lines 284-305 in the `generate_index_page()` function

**Example:**
```python
# Around line 290
benefits_html = """
    <div class="benefits-grid">
        <div class="benefit-item">
            <h3>🌍 Remote First</h3>
            <p>Work from anywhere in the world.</p>
        </div>
        <!-- Add more benefits -->
    </div>
"""
```

**Workflow:**
```bash
cd /Users/hannahhuegel/deel-job-feed-scraper
# Edit generate_careers_pages.py
python generate_careers_pages.py  # Test locally
open careers/index.html  # Preview
git add generate_careers_pages.py
git commit -m "Update company benefits section"
git push
```

---

### 3. **Update Company Details (Name, Logo, URL)**

**File:** `generate_careers_pages.py`
**Location:** Lines 13-17 (top of file)

```python
FEED_URL = "https://zonos.github.io/deel-job-feed/feeds/jobs.json"
COMPANY_NAME = "Zonos"
COMPANY_URL = "https://www.zonos.com"
COMPANY_LOGO = "https://www.zonos.com/logo.png"  # Update with actual logo
COMPANY_DESCRIPTION = "Zonos is a leading provider of cross-border e-commerce solutions."
```

**Workflow:**
```bash
cd /Users/hannahhuegel/deel-job-feed-scraper
# Edit generate_careers_pages.py (lines 13-17)
git add generate_careers_pages.py
git commit -m "Update company details"
git push
```

---

### 4. **Change Page Structure / HTML Templates**

**File:** `generate_careers_pages.py`

**Key Functions:**
- `generate_job_page()` (lines 131-239) - Individual job pages
- `generate_index_page()` (lines 241-326) - Main careers landing page

**Example - Add a new section:**
```python
def generate_index_page(jobs):
    # ... existing code ...

    # Add your custom section
    custom_section = """
        <section class="custom-section">
            <h2>Your Custom Section</h2>
            <p>Custom content here</p>
        </section>
    """

    # Insert into the HTML template
    html_template = f"""
        <!DOCTYPE html>
        <html>
            <!-- ... -->
            {custom_section}
            <!-- ... -->
        </html>
    """
```

---

### 5. **Change Job Data Source**

**File:** `generate_careers_pages.py`
**Location:** Line 13

```python
# Current: Deel job feed
FEED_URL = "https://zonos.github.io/deel-job-feed/feeds/jobs.json"

# If you switch to a different source:
FEED_URL = "https://your-new-source.com/jobs.json"
```

**Note:** Make sure the new feed uses the same JSON structure!

---

## 🔄 Standard Update Workflow

### For ANY Change:

```bash
# 1. Navigate to the repo
cd /Users/hannahhuegel/deel-job-feed-scraper

# 2. Make your changes (edit files as needed)

# 3. Test locally (optional but recommended)
python generate_careers_pages.py
open careers/index.html

# 4. Commit and push
git add .
git commit -m "Brief description of changes"
git push

# 5. Wait 2-3 minutes
# GitHub Actions will automatically:
#   - Regenerate pages
#   - Deploy to GitHub Pages
#   - Changes appear at zonos.com/careers
```

---

## ⏱️ Update Timeline

| Type of Update | How Often | Delay |
|----------------|-----------|-------|
| **Job listings** | Auto (every 6 hours) | None |
| **Manual changes** | On-demand (when you push) | 2-3 minutes |
| **Style/content** | On-demand (when you push) | 2-3 minutes |

---

## 🔍 Testing Changes Locally

Before pushing changes, test them locally:

```bash
cd /Users/hannahhuegel/deel-job-feed-scraper

# Generate pages
python generate_careers_pages.py

# Preview in browser
open careers/index.html

# Or serve locally
cd careers
python -m http.server 8000
open http://localhost:8000
```

---

## 📋 Quick Reference Chart

| What to Change | File | Lines | Git Workflow |
|----------------|------|-------|--------------|
| **Colors/Fonts** | `careers.css` | 3-14, 25 | Edit → Push |
| **Layout/Grid** | `careers.css` | 178, 368 | Edit → Push |
| **Company Info** | `generate_careers_pages.py` | 13-17 | Edit → Push |
| **Benefits Section** | `generate_careers_pages.py` | 284-305 | Edit → Test → Push |
| **Job Page Template** | `generate_careers_pages.py` | 131-239 | Edit → Test → Push |
| **Landing Page Template** | `generate_careers_pages.py` | 241-326 | Edit → Test → Push |

---

## 🚨 Important Notes

### ✅ DO:
- Always test locally before pushing (`python generate_careers_pages.py`)
- Edit source files (`careers.css`, `generate_careers_pages.py`)
- Commit frequently with clear messages
- Check GitHub Pages after pushing (2-3 min wait)

### ❌ DON'T:
- Edit files in `careers/` folder directly (auto-generated!)
- Commit without testing locally
- Touch the `zonos.com` repo for career page content
- Forget to push after committing

---

## 🔗 Integration with zonos.com

The careers page is integrated via **Next.js rewrites** in `zonos.com`:

### Files Modified (in zonos.com repo):
1. `next.config.ts` - Rewrites `/careers` → GitHub Pages
2. `src/middleware.ts` - Locale redirects
3. `src/utils/footerColumns.tsx` - Footer link
4. `src/mdx-pages/docs/jobs/index.mdx` - Jobs page link
5. `utils/mdx/frontmatterIndex.ts` - Link validation
6. `scripts/format/src/createInternalPaths.ts` - Valid routes

**You don't need to touch these!** Changes to the career page happen in the `deel-job-feed` repo only.

---

## 🐛 Troubleshooting

### Changes Not Appearing?

1. **Check GitHub Actions:**
   - Go to https://github.com/Zonos/deel-job-feed/actions
   - Verify the workflow ran successfully
   - Check for errors in logs

2. **Clear Cache:**
   ```bash
   # Hard refresh browser
   Cmd + Shift + R (Mac)
   Ctrl + Shift + R (Windows)
   ```

3. **Verify GitHub Pages:**
   - Visit https://zonos.github.io/deel-job-feed/careers/
   - If this works but zonos.com/careers doesn't, it's a rewrite issue

### Jobs Not Updating?

1. **Check the feed URL:**
   ```bash
   curl https://zonos.github.io/deel-job-feed/feeds/jobs.json
   ```

2. **Verify GitHub Actions schedule:**
   - Check `.github/workflows/generate-careers-pages.yml`
   - Should run every 6 hours

3. **Manual trigger:**
   - Go to Actions tab → "Generate Careers Pages" → "Run workflow"

### Styling Looks Wrong?

1. **Verify CSS file location:**
   - `careers.css` should be in `careers/` folder after generation
   - Script copies it automatically

2. **Check browser console:**
   - F12 → Console → Look for CSS loading errors

3. **Clear browser cache**

### Job Detail Pages Return 404?

**Symptom:** Job listing page works, but clicking on individual jobs returns 404.

**Root Cause:** Next.js client-side router intercepts relative link clicks. Since `.html` files aren't in Next.js's `pageExtensions` configuration, the router doesn't know how to handle them and returns 404.

**How We Fixed It (PR #5):**
1. Changed all career page links from **relative** to **absolute** paths
2. Job cards: `href="filename.html"` → `href="/careers/filename.html"`
3. Back button: `href="index.html"` → `href="/careers/"`

This forces full-page navigation (bypassing Next.js's client-side router), allowing the server-side rewrites in `next.config.ts` to execute properly.

**Testing the Fix:**
```bash
# This should work (server-side)
curl -I https://zonos.com/careers/corporate-broker-...html
# Should return 200

# Browser clicks now also work because they trigger full-page navigation
```

**Technical Details:**
- Server-side rewrites in `next.config.ts` work correctly with curl/direct navigation
- Client-side router was the issue, not middleware or rewrites
- Absolute paths force full-page navigation, which triggers rewrites
- No middleware changes needed (previous PR #2756 approach was ineffective)

---

## 📞 Getting Help

### Resources:
- **Main README:** `/Users/hannahhuegel/deel-job-feed-scraper/README.md`
- **Quickstart:** `/Users/hannahhuegel/deel-job-feed-scraper/QUICKSTART.md`
- **PR #2754:** https://github.com/Zonos/zonos.com/pull/2754

### Common Issues:
- GitHub Actions not running → Check repo settings
- 404 errors → Verify GitHub Pages is enabled
- Styling issues → Check `careers.css` is copied to `careers/` folder

---

## 🎯 Project Status

- ✅ **Repo:** Transferred to Zonos organization
- ✅ **GitHub Pages:** Enabled and public
- ✅ **Integration:** PR #2754 ready to merge
- ✅ **Security:** Using org account (not personal)
- ✅ **Locale Support:** All languages redirect properly
- ✅ **Auto-Updates:** Every 6 hours from Deel

---

## 📝 Version History

| Date | Change | Author |
|------|--------|--------|
| 2026-02-12 | Initial setup & integration with zonos.com | Hannah/Claude |
| 2026-02-12 | Transferred to Zonos org, enabled GitHub Pages | Hannah/Claude |
| 2026-02-12 | Fixed CSS & logo paths (PR #3) | Hannah/Claude |
| 2026-02-12 | Fixed job page 404s with absolute paths (PR #5) | Hannah/Claude |
| 2026-02-12 | Documentation created & updated | Claude |

---

**Last Updated:** 2026-02-12 (Fixed job detail page 404s)
**Maintained By:** Hannah Huegel
**Project:** "New Career Page"
