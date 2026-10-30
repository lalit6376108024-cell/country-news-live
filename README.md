# Country News Desk (live, free)

Free stack: GitHub (hosting + scheduler) + Google News RSS (no key). Nothing to pay for.

## Set up (about 10 minutes)
1. Create a free GitHub account and a new **public** repository (any name).
2. Upload everything in this folder, including the hidden `.github` folder, `data/news.json`, `fetch_news.py` and `index.html`.
3. Repository **Settings > Pages**: Source = "Deploy from a branch", Branch = `main`, folder = `/ (root)`. Save.
4. Repository **Actions** tab > "Update news" > **Run workflow**. This fetches the first real data (about a minute). It then re-runs every 6 hours on its own.
5. Open `https://<your-username>.github.io/<repo-name>/`.

## Add countries
Add a line to `COUNTRIES` in `fetch_news.py` (code, name, flag, hl, gl, ceid). Non-English editions work for fetching, but topic detection only understands English keywords.

## What is not automatic yet
- Photo and location evidence stay empty. Add a step that reads each article's og:image and place name.
- Cartoons are drawn animations matched to the topic, not generated video.
- Google News RSS is an unofficial feed, so keep use modest and always link back to the source.
