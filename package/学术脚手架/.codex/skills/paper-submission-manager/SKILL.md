---
name: paper-submission-manager
description: End-to-end manuscript-to-submission workflow management for academic papers. Use when preparing a manuscript for journal submission, assembling submission packages, aligning with journal instructions, creating cover letters/forms, validating figures/tables, or coordinating post-submission tracking in this repository.
---

# Paper Submission Manager

## Overview

Guide the full handoff from manuscript finalization to journal submission, keeping files organized, requirements satisfied, and acceptance odds improved through a structured, quality-first workflow.

## Workflow Decision Tree

Choose the shortest path that matches the request:
1. **New submission target**: run Intake -> Plan -> Package -> QA.
2. **Existing submission folder**: jump to QA -> Package -> Tracking.
3. **Single artifact update** (cover letter/figures/forms): update the artifact, then run QA.

## Step 1: Intake & Target Selection

Identify the target journal and the most current submission bundle:
- Prefer the newest dated folder (e.g., `20260210_CSBJ/`) if it matches the target.
- If no folder exists, plan to create a new dated folder like `YYYYMMDD_Journal/`.
- Locate journal instructions inside the target folder if present (e.g., `Instructions for Authors.md`).

## Step 2: Build the Submission Plan

Create a checklist that maps requirements to files:
- Manuscript: `manuscript-full.docx` and/or `Somatic Mechanotherapy Activates a Spatiotemporally Synchronized CPTC.md`
- Figures: `figs/` or `figs_for_cellreports/`
- Cover letter and forms: in the target folder (e.g., `01_Cover_Letter_*.md`)
- Suggested reviewers, declarations, questionnaires: target folder

Use `references/submission-checklist.md` as the baseline checklist, then customize.

## Step 3: Prepare & Normalize Files

Ensure consistent naming and content alignment:
- Keep figure filenames consistent with manuscript references (e.g., `Fig.1.pdf`, `Supplementary Figure 1.ai`).
- Keep cover letters aligned with the target journal name and submission type.
- When duplicating bundles, copy from the latest folder and update dates and journal-specific sections.

## Step 4: Quality Assurance

Run a short QA pass before submission:
- Manuscript: title, abstract, keywords, references, and figure callouts match.
- Figures: resolution, labeling, and legend consistency; check for missing panels.
- Forms: conflicts-of-interest, funding statements, author info, and required checkboxes.

## Step 5: Submission Package & Tracking

Assemble the final package in the target folder and log submission metadata:
- Include a brief submission summary (date, journal, version tag).
- Record any confirmations or submission IDs in a short note file.

## References

Use the reference files when needed:
- `references/submission-checklist.md`: baseline checklist and QA items.
- `references/journal-intake.md`: intake questions and bundle naming rules.
