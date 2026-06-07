# Kiro Baseline Extractor Review Summary

Review date: 2026-06-07

Question: Does the Kiro no-tools baseline adapter reliably extract the final
submission JSON from transcript-wrapped Kiro output without accepting prompt
examples or unrelated JSON snippets?

## Trigger

A diagnostic 54-task Qwen run completed, but inspection showed multiple
invalid submissions caused by adapter parsing, not necessarily model behavior.
Several Kiro transcripts ended with a valid `{"findings": ...}` object after
earlier reasoning, tool-attempt text, or example JSON. The old extractor could
grab the wrong brace span and mark those outputs invalid.

The diagnostic run remains ignored local evidence only and is not promoted as a
current baseline.

## Accepted Fix

- `_extract_json` still accepts plain JSON and fenced JSON when they contain a
  `findings` key.
- If those fast paths do not produce a valid submission, it scans JSON object
  starts from the end of the transcript and returns the last valid object that
  contains `findings`.
- Plain/fenced malformed JSON now falls through instead of aborting before the
  reverse scan.
- Non-submission JSON examples such as request shapes are ignored because every
  path requires the `findings` key.

## Review Evidence

- Kiro `claude-opus-4.6`, medium effort, initial read-only audit found one low
  issue: malformed fenced JSON could raise before fallback.
- The low issue was fixed and covered by
  `test_malformed_fenced_json_falls_back_to_later_submission`.
- Kiro `claude-opus-4.6`, medium effort, post-fix read-only audit returned
  `CLEAN` and confirmed no remaining concrete parser blocker.

Raw Kiro output was retained in ignored local `/tmp` logs for this work session
and is not committed.

## Verification

- `python3 -m unittest discover -s tests -p 'test_kiro_baseline_adapter.py'`
  passed: 5 tests.
- `python3 -m compileall -q scripts tests` passed.
- `git diff --check` passed.
- A previously misparsed diagnostic transcript now extracts to
  `{"findings": []}` with the updated parser.
