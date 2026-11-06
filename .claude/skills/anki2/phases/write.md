# P5–P7: gate, write, verify and report

Load at P5 or on resume in P5–P7; do not load draft.md or reviewer templates.

## P5: automatic gate

Run `.venv/bin/cards gate --build <build>`. Passed means continue without asking
for approval. Failure means no writes: follow the findings and return to P4
if a review round remains; otherwise stop with blockers. Never bypass a
stale hash, edit gate evidence, or add a force flag.

## P6: stage 1 inline

Run `.venv/bin/cards write --build <build>` only after gate passes. It generates
plans/import files; it has **not written to Anki**. Q-1 has no successful direct
probe: the shipped CLI has no `--direct`. Do not attempt it or shell HTTP.

1. Read `write/expected.json`, `write/suspend.json`, `write/updates.json` and
   `write/provenance.json`. Enumerate `write/batches/*.json` paths without
   dumping their contents. Track actual per-call receipts in
   `<build>/write/receipts.json` (batch path/hash, returned note ids, success or
   failure). On resume, reconcile receipts with Anki; never resubmit a successful
   or ambiguously completed batch.
2. For IO, discover `media` entries with a local script that reads drafts and
   outputs only unique `{path,filename}` pairs to `<build>/write/media.json`.
   Read that small list, then use `mcp__anki__store_media_file` by absolute local
   path and matching filename before adding IO notes. Never send base64. Record
   success. If media upload/access is unavailable, stop and report.
3. Read each batch file once; pass **its content directly as the arguments to
   `mcp__anki__add_notes`**. Do not reconstruct notes, retype fields or re-echo
   payloads in Bash. Each batch already has one deck/type and at most 100 notes.
   Record actual returned ids and failures immediately; never count attempts as
   successful writes. For entries in `updates.json`, call
   `mcp__anki__update_note_fields` with the shipped `note_id` and `fields`.
4. Resolve draft ids from `suspend.json` to the actual note ids (batch order and
   receipts; existing nids for updates), using a local script that reads files
   and emits only the id mapping. `mcp__anki__notes_info` returns **card** ids.
   Suspend every card belonging to the listed tier-3/unresolved notes with
   `mcp__anki__card_suspend`. Do not assume a note has only one card. Verify all
   intended cards are suspended; count suspended notes separately from cards.
5. Run `mcp__anki__find_notes` with each search in `expected.json.verify` exactly,
   and inspect `notes_info` for ids/fields and suspension. The first search must
   yield the intended source notes (account for existing notes from preflight);
   the active-suspension search must yield no unintentionally suspended notes.
   An explicitly flagged unresolved note is an allowed suspended exception:
   confirm its identity through `suspend.json`, not by ignoring search results.
   Read back three actual notes, or all if fewer, comparing their fields to
   batch/update files with a local comparison, never a full drafts dump.
6. If explicitly carding ahead, suspend all source cards, record that extra
   action separately, and explain the expected nonempty active-suspension search.
   Do not silently unsuspend anything. AnKing matches remain proposals unless
   the user has explicitly requested their unsuspension; use their **card** ids.
7. Only after actual writes and read-back match `expected.json`, run
   `.venv/bin/cards state record-write --build <build>`. It reads `write/receipts.json`
   (never planned counts), refuses on any failed batch, records `created`, `updated`,
   `suspended` (notes in the planned suspension list), `errors` and `status: done`
   under `build.json.write`, and sets `review.independent` only if both reviewers'
   reports exist for the last round. Do not edit `build.json` by hand. Finish with
   `.venv/bin/cards state phase --build <build> P6 done`.

A hard MCP/Anki error or permission refusal stops the run. Say what failed,
which batches succeeded, and how to resume safely. Offer `write/import.txt`
(and further numbered import files if present) for manual import; updates stay
in `updates.json`, not import duplicates. Never report an import file as an
imported deck. Do not retry via ports, curl or another connector.

## P7: report

Start P7 and run `.venv/bin/cards report --build <build>`. It requires real write
counts and meters the current Claude session; retain the actual usage line.
If usage evidence is unavailable, report that error instead of fabricating cost.
Use its output once as the concise handoff: deck/search, counts, tiers,
suspension, figures/skips, review rounds and unresolved issues, then usage and
sync reminder. Link any proposals/receipts the user needs; do not paste files.
Mark P7 done, then `.venv/bin/cards state phase --build <build> done start`
as in the core map; the terminal phase accepts no further transitions. Report removes only this build's matching `builds/.current` pointer.
