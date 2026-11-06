# JSONL report
Write one JSON object per line, no Markdown fences. Every record has `reviewer`: "student".
For each note/card write:
{"type":"note","reviewer":"student","note_id":"n017","card":null,"verdict":"fix","codes":["V2"],"blocker":true,"evidence":"exact text or visible fault, with slide for fidelity","rewrite":{"Text":"full corrected Text","Extra":"unchanged"},"attempt":{"answer":"committed front answer","result":"alternative"}}
`verdict`: pass|fix|reject; `card`: c1 etc. or null. `rewrite`: object of note fields (Text, Extra) or null, never a string and never Tags or any non-field key; "unchanged" as a field value preserves that field. A rewrite must respect house-style lint (at most five cloze numbers, no comma inside a cloze, Extra within three lines): `cards apply` refuses a rewrite that adds a lint blocker, keeps the draft and sends the note to round 2. Split a long list into two notes instead of using more than five clozes. Use rubric codes, concrete evidence, and complete corrections. Student `attempt` is required with answer and result right|alternative|unknowable. V2 alternatives are A2 blockers.
Set/batch findings:
{"type":"set","reviewer":"student","code":"V9","notes":["n017"],"finding":"concrete evidence","fix":"correction"}
End with exactly one closing summary:
{"type":"summary","reviewer":"student","verdict":"PASS_WITH_FIXES","stats":{"notes":1,"pass":0,"fix":1,"reject":0,"blockers":1}}
Judge the verdict on the set after your rewrites are applied. FAIL = a blocker with no workable rewrite, a reject, or a set finding needing re-extraction (sections missing, wholesale drift). A blocker you fix with a complete rewrite, and polish-only findings, are PASS_WITH_FIXES. Otherwise PASS. Include tier mix and tier-3 share for maintainer; cards, attempts right and alternatives for student.
