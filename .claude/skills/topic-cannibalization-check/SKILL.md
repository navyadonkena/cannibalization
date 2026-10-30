---
name: topic-cannibalization-check
description: Check whether a blog topic or keyword is already covered by a published post before writing it, to avoid keyword cannibalization. Use whenever the user is picking, proposing or shortlisting blog topics, asks "have we already written about X", "is this topic taken", "is this a duplicate", or wants to vet a list of topic ideas against existing content.
---

# Topic cannibalization check

Two posts cannibalize each other only when they would compete for the same query. Sharing a few words is not enough: "mobile proxies for AI data collection" and "mobile proxies vs residential proxies" both contain "mobile proxies" but are different topics with different keywords and intent.

So the analysis is a judgment on three dimensions, not a similarity score. `cannibalization.py` (repo root, standard library only) only builds the shortlist of candidates to judge.

## Steps

1. **Pin down the new post.** Unless the user gives a separate keyword, treat their topic as both the topic and the primary keyword. Infer the search intent from the keyword: informational (how/why/what), commercial (best/vs/review/pricing), transactional, or navigational. If the intent is genuinely ambiguous, state your assumption.

2. **Make sure the index is current.**
   - If `index.json` doesn't exist, or the user has published recently, run:
     ```bash
     python cannibalization.py sync <sitemap-url> --filter <blog-path>
     ```
   - If you don't know the sitemap URL or blog path, ask once. Don't guess.

3. **Shortlist candidates.**
   ```bash
   python cannibalization.py check "<topic>" --top 8 --details
   ```
   The score is word overlap only and can be wrong in both directions. Also search `index.json` for the topic's distinctive terms and synonyms (for example grep titles and headings) so a relevant post with different wording isn't missed. Ignore generic terms ("proxies", "data collection", "best", "guide") when deciding what counts as distinctive.

4. **Judge each plausible candidate on three dimensions.** Use its title, H1, headings and description; fetch the page if those aren't enough. Rate each dimension Match, Partial or No:
   - **Keyword:** Does the existing post target the same primary keyword, or a close variant or synonym? Infer its primary keyword from the slug, title and H1. Shared generic words don't count; the distinctive terms must line up (for example "mobile" + "AI data collection" together).
   - **Topic:** Is the existing post primarily about the same subject and angle, in depth? A section or passing mention inside a broader post does not make it the same topic.
   - **Intent:** Would the same searcher be satisfied by either post? A "best providers" roundup, a "vs" comparison, a how-to and a definition serve different intents even on related subjects.

5. **Give the verdict from the combination:**
   - **Cannibalization risk: High**: keyword, topic and intent all Match (or keyword + intent Match). Recommend not writing it; update the existing post instead.
   - **Partial overlap**: two dimensions Match or Partial but one clearly differs. Say which dimension differs and propose how to widen the gap (distinct primary keyword, narrower angle, different intent), or recommend refreshing the existing post if the gap is too small.
   - **No cannibalization**: at most one dimension overlaps. Green light; mention the candidates as internal-link targets.

## Output

- For the topic, list only the candidates you judged plausible, each as: URL, then Keyword / Topic / Intent with Match, Partial or No and a few words of reasoning.
- Dismiss the rest of the shortlist in one line, naming why (for example "different topic: comparison of proxy types").
- End with the overall verdict and the recommended action.
- For a list of topics, add a summary table: topic, verdict, closest existing post, action. Put clear topics first.

## Caveats

- Only published posts in the sitemap are covered, not drafts or planned topics, and only the folder you synced (for example `/blog/`). Say so if other sections (use cases, landing pages) could target the same keyword.
- Don't treat the script's score as a verdict. Never call a topic a duplicate on word overlap alone.
