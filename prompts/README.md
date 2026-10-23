# Five complete Harness prompts (candidate V1)

These files are standalone, ready to replace the **entire** System prompt in Advanced Harness, NOT additions to the existing prompt.

| Existing role | File | Player ID |
|---|---|---|
| Goalkeeper | [gk.txt](harness/gk.txt) | 0 |
| Defender | [def.txt](harness/def.txt) | 1 |
| Midfielder | [mid.txt](harness/mid.txt) | 2 |
| Forward 1 | [fwd1.txt](harness/fwd1.txt) | 3 |
| Forward 2 | [fwd2.txt](harness/fwd2.txt) | 4 |

The existing live setup won two of three supplied matches. Do NOT replace all five prompts at once and attribute changes to a specific improvement. Make a private backup of real active prompts, test one role alteration, run repeated Fitness checks and matched Practice.

If live input only exposes repeated possessionAgentId without team discriminator, model-only Harness cannot prove ownership. The conservative UNKNOWN fallback intentionally delegates to built-in AI rather than allowing hallucinated shots/passes. Future Runtime adapter can reconcile state more robustly.

These prompts contain examples, not instructions to output the same action every time. Each file is below 20,000 characters.
