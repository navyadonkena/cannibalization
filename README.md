# cannibalization

Check a blog topic against your already-published posts before you write it, so you don't cannibalize your own rankings.

Python 3, standard library only.

## Usage

1. Build the index from your sitemap (re-run whenever you publish):

   ```bash
   python cannibalization.py sync https://yoursite.com/sitemap.xml --filter /blog/
   ```

2. Check a topic idea:

   ```bash
   python cannibalization.py check "how to reduce churn in saas"
   ```

Output is a verdict plus the closest existing posts with a 0-1 similarity score:

| Score | Verdict |
|-------|---------|
| >= 0.65 | DUPLICATE - don't write it |
| >= 0.40 | OVERLAPPING - change the angle or update the existing post |
| < 0.40 | SAFE |

## How it scores

Each post is represented by its slug and `<title>` (weighted highest), `h1`-`h3` headings, and meta description. The score is half TF-IDF cosine similarity and half the share of the topic's words already present in the post's title/URL. Thresholds are at the top of `cannibalization.py`.
