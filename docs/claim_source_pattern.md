# Claim–source mapping (CCA-F Domain 5)

## Rule

Every non-trivial factual claim in agent output should carry a source reference.

## When sources conflict

1. Do not silently average or invent a compromise.
2. Keep both claims with their `source_id`s.
3. Lower confidence / set `needs_human_review`.
4. State the disagreement explicitly in the synthesis.

## Shape

- `claim`: string
- `source_id`: string
- `confidence`: 0–1
- `conflicts_with`: optional list of claim ids

## Example

```python
claims = [
  {
    "claim": "Short 'a' is the vowel sound in 'cat'.",
    "source_id": "src_phonics_guide_1",
    "confidence": 0.9,
  },
  {
    "claim": "Some curricula treat 'a' in 'cat' as a different label.",
    "source_id": "src_alt_curriculum",
    "confidence": 0.6,
  },
]

# Conflict detected when two claims about the same topic disagree
# → annotate: "Sources disagree on labeling; present both or escalate."
```

## Relation to this project

Project Gem content generation is mostly single-source creative output,
so full provenance plumbing is optional here. For research agents, this
pattern is required.

## Exam one-liner

Preserve claim–source links; on conflict, attribute both sides and escalate
or lower confidence — never silently reconcile.
