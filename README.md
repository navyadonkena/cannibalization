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

Output is a shortlist of the closest existing posts with a 0-1 word-overlap score. The score is not a cannibalization verdict: it only finds candidates. Add `--details` to see each candidate's description and headings.

Whether a candidate actually cannibalizes depends on three things, judged per candidate (the Claude skill in `.claude/skills/topic-cannibalization-check` does this):

- **Keyword:** same primary keyword or a close variant
- **Topic:** same core subject and angle, not a passing mention
- **Intent:** the same searcher would be satisfied by either post

## How it scores

Each post is represented by its slug and `<title>` (weighted highest), `h1`-`h3` headings, and meta description. The shortlist score is half TF-IDF cosine similarity and half the share of the topic's words already present in the post's title/URL. Thresholds are at the top of `cannibalization.py`.
