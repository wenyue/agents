# Personal AI Skills

Personal skill configuration managed by [skillshare](https://github.com/runkids/skillshare).

## Setup (New Machine)

### 1. Install skillshare

```bash
npm install -g skillshare
# or
npx skillshare --version
```

### 2. Initialize with this repo

```bash
skillshare init --remote git@github.com:wenyue/skills.git --all-targets
skillshare pull
```

### 3. Restore tracked skills from registry

See `registry.yaml` for the list of tracked repos, then install each:

```bash
skillshare install vercel-labs/skills/skills/find-skills --track --force
skillshare install getsentry/sentry-for-ai/skills/sentry-fix-issues --track --force
skillshare sync
```

## Plugins

These are managed separately from skillshare — they include hooks, installers, and deeper agent integration.

### Superpowers

Complete software development workflow with composable skills (brainstorming, TDD, debugging, code review, etc).

```bash
# Clone to ~/.codex/superpowers (the conventional location)
git clone https://github.com/obra/superpowers.git ~/.codex/superpowers
```

Follow the repo's README for per-platform setup (Claude Code, Cursor, Copilot CLI, Gemini CLI).

### Caveman

Ultra-compressed communication mode — cuts token usage ~75% while keeping full technical accuracy.

```bash
# Install via Claude Code plugin system
claude plugin install caveman
# Or manually:
npx caveman-installer
```

Source: https://github.com/JuliusBrussee/caveman

## Daily Usage

```bash
# Update all tracked skills
skillshare update --all && skillshare sync

# Push local changes to remote
skillshare push -m "description"

# Pull from remote on another machine
skillshare pull && skillshare sync

# Update plugins
claude plugin update caveman
cd ~/.codex/superpowers && git pull
```

## Architecture

```
~/.config/skillshare/
├── config.yaml          # Target paths, sync mode
├── registry.yaml        # Tracked repo sources (local-only, copy in this repo for reference)
└── skills/              # Source of truth (this repo)
    ├── _vercel-labs-skills/       # tracked: find-skills
    ├── _getsentry-sentry-for-ai/  # tracked: sentry-fix-issues
    └── registry.yaml              # Reference copy for cross-machine setup

~/.agents/skills/        # Target: universal (cline, warp, witsy share this)
~/.claude/skills/        # Target: claude
~/.cursor/skills/        # Target: cursor
~/.codex/skills/         # Target: codex
~/.copilot/skills/       # Target: copilot

~/.codex/superpowers/    # Plugin: superpowers (git clone)
~/.claude/plugins/       # Plugin: caveman (claude plugin system)
```
