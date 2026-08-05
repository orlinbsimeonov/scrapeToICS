# Apify → .ics → iOS Calendar

Scrapes event listings via Apify, converts them to an `.ics` feed, and keeps
it updated automatically via GitHub Actions. iOS Calendar subscribes to the
feed URL and refreshes itself — no manual re-import needed.

## 1. Set up the Apify actor

- Build or reuse an Apify actor that scrapes your target event site(s) and
  writes each event to the actor's default dataset, with at least:
  `title`, `start` (ISO datetime). Optional: `end`, `location`,
  `description`, `url`.
- Note your **Apify API token** (Apify Console → Settings → Integrations)
  and the **dataset ID** the actor writes to.

## 2. Set up this repo

- Push this folder to a **public** GitHub repo (needs to be public so iOS
  can fetch the raw `.ics` file without auth — or use GitHub Pages, see
  below).
- In the repo: **Settings → Secrets and variables → Actions**, add:
  - `APIFY_TOKEN`
  - `APIFY_DATASET_ID`

## 3. Enable GitHub Pages (recommended over raw.githubusercontent.com)

- **Settings → Pages** → set source to the `docs/` folder on your default
  branch. This gives you a stable URL like:
  `https://<username>.github.io/<repo>/events.ics`
  GitHub Pages is more reliable for calendar subscriptions than the raw
  content URL, which is sometimes rate-limited or cached oddly by clients.

## 4. Let the workflow run

- The Action in `.github/workflows/update-calendar.yml` runs every 6 hours
  and on manual trigger. It runs `scrape_to_ics.py`, which reads the Apify
  dataset and regenerates `docs/events.ics`, then commits it if changed.
- You can trigger it manually from the **Actions** tab to test before
  waiting for the schedule.

## 5. Subscribe on iOS

- On iPhone: **Settings → Calendar → Accounts → Add Account → Other →
  Add Subscribed Calendar**.
- Enter the URL, but use `webcal://` instead of `https://`, e.g.:
  `webcal://<username>.github.io/<repo>/events.ics`
- iOS will periodically re-fetch this in the background (it doesn't let you
  set the exact interval — it's system-managed, typically every few hours).
- The events will show up in the Calendar app as a separate, read-only
  calendar you can toggle on/off.

## Notes

- `scrape_to_ics.py` generates a stable UID per event (hash of
  title+start+location), so re-running it updates existing events instead
  of duplicating them — as long as those fields don't change between runs.
- If your Apify actor already runs on a schedule independent of this repo,
  you can drop the "Run Apify actor" step in the workflow and just read
  the latest dataset contents.
- Adjust the `x-wr-timezone` in `scrape_to_ics.py` to your local timezone.
