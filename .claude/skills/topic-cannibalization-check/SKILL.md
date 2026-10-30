---
name: topic-cannibalization-check
description: Check whether a blog topic or keyword is already covered by a published post before writing it, to avoid keyword cannibalization. Use whenever the user is picking, proposing or shortlisting blog topics, asks "have we already written about X", "is this topic taken", "is this a duplicate", or wants to vet a list of topic ideas against existing content.
---

# Topic cannibalization check

Vets blog topic ideas against the site's already-published posts using `cannibalization.py` at the repo root (standard library only).

## Steps

1. **Make sure the index is current.**
   - If `index.json` does not exist, or the user says they have published recently, run:
     ```bash
     python cannibalization.py sync <sitemap-url> --filter <blog-path>
     ```
   - If you don't know the sitemap URL or blog path (for example `/blog/`), ask the user once. Do not guess them.

2. **Check each topic.** Run once per topic (for a list, run them all in parallel):
   ```bash
   python cannibalization.py check "<topic>" --top 5
   ```

3. **Interpret the verdict** and tell the user in plain language:
   - **DUPLICATE** (score >= 0.65): recommend against writing it. Name the existing post and link its URL. Suggest refreshing that post instead.
   - **OVERLAPPING** (0.40-0.65): read the matching post's title and headings. Either propose a clearly different angle (different audience, intent, or sub-topic) or recommend updating the existing post. Explain what differs.
   - **SAFE** (< 0.40): green light, but mention the closest post as a possible internal link.

4. **For a list of topics**, summarise as a table: topic, verdict, closest existing post, recommendation. Put safe topics first.

## Caveats to state when relevant

- Matching is based on shared words, not meaning. Synonyms (for example "churn" vs "customer attrition") can be missed, so use judgment on a SAFE result when a topic is obviously the same idea as a listed title.
- Only published posts in the sitemap are covered, not drafts or planned topics.
