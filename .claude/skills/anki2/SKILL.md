---
name: anki2
description: Use when asked to "card this", "make cards", /anki or /anki2 with a lecture PDF, resume a card build, HARVEST a study session, or repair cards. Not for general Anki questions.
model: claude-sonnet-5-5
effort: medium
---

# Anki2

## Purpose

Make AnKing-quality cards from one lecture's own terms. Use the `cards` CLI for files and checks, judgement for drafting, and independent reviewers before writing.

## Job router

- **BUILD:** one lecture PDF or a slide range; initialize one build. If the user supplies multiple PDFs, a merged/combined PDF, or asks to combine lectures, stop: v1 makes one build per lecture. Never merge PDFs or hand-edit the build.
- **Resume:** the same source already has a `build.json`; follow the resume rule before any phase file.
- **HARVEST / REPAIR:** not supported in v1.0; deferred to v1.1. Use the separate `/anki` skill if it is installed.

## Invariants

- Runtime: packaged copies call `cards` from PATH; if missing, stop and give the install command. `mcp__anki__X` means the Anki MCP tool ending in `X` (Claude Code `mcp__anki__X`; OpenCode `tools.anki.<tool>`, or `anki_X` with code mode off). Launch `anki-maintainer`/`anki-student` as subagents (Claude Code Task, OpenCode `subagent`) with only each packet's `PROMPT.md` path. The pre-write hook is Claude Code-only; everywhere, `cards gate` must pass first and `cards write` refuses without it.

- Writes happen without asking once `cards gate` passes (ADR-9), except in runtimes without the write hook, where the plan is confirmed once. Both reviews must pass and the drafts hash must match; never bypass a refusal or a hook.
- Preserve the source's terms, hedges and scope. Add nothing from general knowledge; never invent unreadable source content.
- Every tag is under `#ColdRecall::`. Never write into AnKing's tags or note types. Reconcile existing own notes and propose AnKing unsuspends instead of duplicates.
- Suspend/unsuspend take **card** ids from `notes_info`.
- Never claim a failed write succeeded. Never delete notes without an explicit request.
- Use pinned `anki-maintainer` (high effort) and `anki-student` (medium effort), with only packet paths as input. Never fork; never send the conversation, author rationale or your summary.
- Never Read a PDF. View only generated PNGs for map-flagged slides or figures being occluded. The main agent does not open contact sheets or reviewer briefs, rubrics or report-format templates.
- Never Edit drafts note by note. Initial drafting is batched; review rewrites go through `cards apply`.
- Never edit the installed skill, the `cards` package, `build.json` or `target.json` to get past an error. If a `cards` command errors, stop and report the exact command and error; do not patch the tool.
- On a hard Anki error, stop and explain the failure; no curl, alternate ports, AppleScript or other workarounds.
- Keep all working files inside this build. Sources, the lecture folder and the vault are read-only.

## Token discipline

- Run `source --all` once at P2; do not re-read it on resume past P2.
- Look up only needed slides through the map and `source --slides N` or `source --grep "term"`.
- Keep large artefacts in files; send paths, never drafts or rubric text, in prompts or chat.
- Read command summaries and named findings; never echo files or dump `drafts.jsonl`.
- Batch independent calls; launch both reviewers in one message.

## Phase map

Run from the Cards project root. `<build>` is the path init returns; other angle-bracket values come from this build, never guesses. All phase paths are relative to this skill. Before work in Pn run `.venv/bin/cards state phase --build <build> Pn start`; after its exit condition run `... Pn done`. Never skip forward.

| Phase | Entry condition | Exact commands / actions | What to read | Exit condition | Phase file to load |
|---|---|---|---|---|---|
| P0 Preflight | Source supplied; resume rule checked | `.venv/bin/cards state init "<PDF>"`; `mcp__anki__model_names` and `mcp__anki__list_decks`; `.venv/bin/cards state set --build <build> facts.anki_reachable=true facts.note_type_exists=true` | `build.json` first; small MCP results | Anki available; ColdRecall Cloze exists; save deck names to `<build>/existing-decks.json` as a JSON array of name strings | None; core only |
| P1 Extract + target | P0 complete | `.venv/bin/cards extract --build <build>` (a cold run takes over 2 min: run it alone with Bash `timeout: 600000`, never in the background; add `--slides N-M` for requested range); `.venv/bin/cards target --build <build> --existing-decks <build>/existing-decks.json`; create missing target deck with `mcp__anki__create_deck`; `.venv/bin/cards state set --build <build> facts.deck_exists=true` | `source/map.md`, `source/objectives.json`, `target.json` | Confident flat target deck exists | None; core only |
| P2 Draft | Source and target ready | `.venv/bin/cards source --build <build> --all` once; for flagged slides `.venv/bin/cards source --build <build> --page-image N`; write `drafts.jsonl` and `skipped.jsonl` in one Write each; optional `.venv/bin/cards figures --build <build> --fig <fig_id>` | `phases/draft.md`; source text; only required flagged PNGs | Drafts cover objectives; deliberate omissions recorded; IO previews checked | `phases/draft.md`; `phases/occlusion.md` only for IO |
| P3 Check + render | Draft files ready | `.venv/bin/cards check --build <build>`; `.venv/bin/cards render --build <build>` | Findings summary only; specific check entries if needed | No schema/coverage blockers; renders exist | None; core only |
| P4 Review | Checks and renders ready | `.venv/bin/cards packets --build <build> --round 1`; launch `anki-maintainer` and `anki-student` in one message, each prompt = its `PROMPT.md` path only; `.venv/bin/cards apply --build <build> --round 1` | Apply summary and conflicts only; never reviewer templates | Both reports applied; changes rechecked/reviewed, at most 2 rounds | None; core and round rules below |
| P5 Automatic gate | Latest review round applied | `.venv/bin/cards gate --build <build>` | Gate summary | Gate passed on current drafts; continue without asking | `phases/write.md` |
| P6 Write + verify | Gate passed; hash unchanged | `.venv/bin/cards write --build <build>`; `mcp__anki__add_notes` straight from each batch file's content (stage 1 inline); updates, media, suspend and verify via MCP per `expected.json` | `write/expected.json`, `write/suspend.json`, `write/updates.json`; each batch once | Actual writes and suspend/verify searches match expected counts; evidence recorded with `.venv/bin/cards state record-write --build <build>` | `phases/write.md` |
| P7 Report | P6 done with verified counts | `.venv/bin/cards report --build <build>` | Report output once | Short report delivered with usage line and sync reminder; mark P7 done, then `.venv/bin/cards state phase --build <build> done start` | `phases/write.md` |

P0: record observed facts only. Missing ColdRecall Cloze: stop and ask the user to install `assets/coldrecall-cloze/`, then resume. Render uses those shipped assets; fetch live templates only if the user says the note type changed. If target is not confident, or the user names a deck/topic, or slide 1's title is not the topic, ask once for course, number and title and rerun `.venv/bin/cards target --build <build> --existing-decks <build>/existing-decks.json --course <course> --number <number> --title "<title>"`. Never hand-edit `target.json`.

P3: resolve initial schema/lint blockers in one batch using source already read; no note Edits or repeated `source --all`. Then render. Send judgement findings to the panel.

P4: launch an extra `anki-maintainer` for each emitted section's `PROMPT.md` path. Wait for all reports; never read packets yourself. Resolve conflicts in the next scoped review; use `.venv/bin/cards apply --build <build> --round 1 --decline <id>:<reason>` only before applying that round. Never overwrite an applied report or delete its log.

After round 1, mark P4 done, return to P3, run `check` and `render --only <changed_ids>`, then start P4 again. Run `packets --round 2 --only <changed_ids>`, launch both reviewers with paths only, then `apply --round 2`. Scope: conflicts, open blockers and affected groups; all notes if unclear. Fix shared template problems once in the build model and rerender affected notes. Recheck after apply. No third round; unresolved findings still face the gate.

## Resume rule

Read `build.json` first, before any phase file. For the same PDF, `state init` reuses its hash and restores the active-build pointer; `state get --build <build>` summarizes it. Inspect `phase`, the last `history` entry, `review`, `gate` and `write`; continue missing work or start the next legal phase. Never replay a completed build. Use this table, not `state next` filenames.

Never replay extraction, `source --all`, or `phases/draft.md` past P2. In interrupted P2, use existing drafts and targeted slices; do not repeat a recorded full-source read. In P4 reuse finished reports and launch only missing reviewers. In P6 reconcile recorded batch results before retrying: never resend a successful batch; stop if success is ambiguous.

## Stop conditions

- Exit 0: continue. Exit 1: fix findings within the round limit. Exit 2: stop at the named error and explain the remedy; no blind retries. Exit 3: run the named prerequisite; never bypass it.
- Failed gate: no writes. Return to P4 only if a round remains; otherwise report blockers and real artefact paths.
- Usage limit/interruption: preserve state, drafts, reports and write receipts; report the build path, last completed phase and next action. Resume with `/anki2` and the same PDF.
- Unreadable/cloud-only source: stop; ask the user to make it available offline. Permission error: report it and offer existing import files; never claim completion or switch transports.
