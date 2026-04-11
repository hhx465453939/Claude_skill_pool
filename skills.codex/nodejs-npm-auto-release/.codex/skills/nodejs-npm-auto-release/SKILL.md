---
name: nodejs-npm-auto-release
description: Set up and run a standardized Node.js npm release workflow with auto version bump, npm publish via GitHub Actions, and local pre-push checks. Use when you want a repo to auto-bump version on push to main, publish to npm, and keep release steps consistent.
---

# Node.js NPM Auto Release

## Overview

Provide a repeatable workflow to prepare, verify, and ship npm packages with a combined auto-version-and-publish GitHub Action, plus local checks before push.

## Setup Checklist

1. Add release scripts in `package.json`

```json
{
  "scripts": {
    "release:patch": "npm version patch -m \"chore(release): v%s\"",
    "release:minor": "npm version minor -m \"chore(release): v%s\"",
    "release:major": "npm version major -m \"chore(release): v%s\""
  }
}
```

2. Add `.npmignore` to keep packages clean

Typical entries:
- `.github/`
- `.claude/`
- `docs/`
- `tests/`
- `.env`
- `node_modules/`

3. Add the combined workflow file

Create `.github/workflows/auto-version-publish.yml` with:

```yaml
name: auto version and publish

on:
  push:
    branches:
      - main

permissions:
  contents: write
  id-token: write

jobs:
  release:
    if: ${{ !contains(github.event.head_commit.message, 'chore(release):') }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "18"
          registry-url: "https://registry.npmjs.org"

      - name: Install dependencies
        run: |
          npm ci

      - name: Typecheck
        run: |
          npm run typecheck

      - name: Test
        run: |
          npm test

      - name: Configure git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

      - name: Bump patch version and tag
        run: |
          npm version patch -m "chore(release): v%s [skip ci]"

      - name: Push version bump and tag
        run: |
          git push origin HEAD:main --follow-tags

      - name: Publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
        run: |
          npm publish --access public
```

4. Set GitHub secret

Add `NPM_TOKEN` in repo Secrets with publish permission.

## Release Workflow

1. Local checks

```bash
npm run typecheck
npm test
npm pack --dry-run
```

2. Commit and push

```bash
git add -A
git commit -m "feat: update package"
git push origin main
```

3. Verify release

- Ensure `auto version and publish` workflow succeeds
- Confirm new tag created
- Confirm npm version:

```bash
npm view <package-name> version
```

## Notes

- Auto-release skips commits containing `chore(release):` to avoid loops.
- If you need manual bump, use `npm run release:patch` then push tags.
