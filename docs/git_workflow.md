# Git Workflow

This document defines the day-to-day Git workflow for this repository.

## Current Repository State

- Local Git repository initialized
- Default branch: `main`
- Remote:
  - `origin = https://github.com/xiwen24936826/codesysAPItest.git`

## When To Commit

Create a commit when:

- one service module is completed
- one small related group of modules is completed
- one bug is fixed and minimally verified
- one test batch is added and passes
- one important document/spec update is finished
- one real integration conclusion is confirmed
- the current change set is internally consistent before starting a larger task

## When Not To Commit Yet

Do not commit yet when:

- the feature is only half implemented
- tests are failing and the reason is not documented
- unrelated files are mixed into the same change set
- temporary scripts or outputs are still present
- one commit contains multiple unrelated topics

## Recommended Commit Size

Prefer small, self-contained commits:

- one feature point per commit
- one fix point per commit
- one conclusion or documentation point per commit

Example commit messages:

- `add create_program service`
- `add textual document services`
- `fix project in use handling`
- `update phase1 MCP tool spec`

## GitHub Desktop Basics

### Commit

1. Open the repository in GitHub Desktop
2. Review changed files in the left panel
3. Fill in `Summary`
4. Click `Commit to main`
5. Click `Push origin`

### Discard Uncommitted Changes

1. Right-click a changed file
2. Select `Discard changes`

### Undo Last Commit

1. Open `Repository`
2. Select `Undo Last Commit`

### View History

1. Open `History`
2. Review commits, changed files, and diffs

## Recommended Daily Rhythm

1. Start new work only when the working tree is understood
2. Finish one small goal
3. Run minimal verification
4. Commit
5. Push to remote

## Repository Memory Rule

Plans, constraints, blockers, and workflow rules must not live only in chat context.

Stable project facts should be written into repository documents, especially:

- `docs/current_phase_plan.md`
- `docs/api_specs/`
- `docs/research/`
- `docs/git_workflow.md`
- `AGENTS.md`
