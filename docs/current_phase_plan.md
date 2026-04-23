# Current Phase Plan

Updated: 2026-04-23

This document records the current working plan so future sessions do not depend on chat context alone.

## Goal

Phase 1 prioritizes stable POU operations in existing CODESYS / SP20 projects.

The current success target is:

- MCP Server can be connected by the client
- POU operations can run reliably on a real existing project
- the project may be prepared manually by the user

## Priority Scope

Primary implementation scope:

1. `create_program`
2. `create_function_block`
3. `create_function`
4. `list_project_objects`
5. `read_textual_declaration`
6. `read_textual_implementation`
7. `replace_text_document`
8. `append_text_document`
9. `insert_text_document`

Supporting but not blocking Phase 1:

1. `create_project`
2. `open_project`
3. `save_project`
4. `add_controller_device`

Deferred:

1. `scan_ethercat_devices`

## Path And Object Rules

- filesystem paths must be absolute
- `project_path` must be absolute
- `container_path` is a logical object path such as `Application`
- text documents use:
  - `declaration`
  - `implementation`

## Text Tool Semantics

- `replace_text_document`: replace the whole target text
- `append_text_document`: append only to the end
- `insert_text_document`: insert at a fixed character offset

Phase 1 uses only one insertion strategy:

- `insertion_offset`

## Real Integration Strategy

### Stage A

Allowed now:

- user manually prepares a real SP20 project
- user provides the absolute project path
- integration tests operate on a copied temporary project, not the original source project

Focus:

- `open_project`
- POU creation
- declaration read
- implementation read
- replace text
- append text
- insert text

Validated on the current machine:

- a manual real project at `D:\工作资料\test\test_pou_create.project` was used as the source project
- the integration flow now copies the source project to a temporary test project before execution
- the root container of the validated project does not contain `Application`
- successful fallback to the root logical container `/` was verified
- the following real flow passed end-to-end:
  - `open_project`
  - `create_program`
  - `replace_text_document`
  - `append_text_document`
  - `insert_text_document`
  - `read_textual_implementation`

Current Stage A conclusion:

- the POU mainline is now proven on at least one real SP20 project layout
- Phase 1 can continue on top of this verified path without depending on automatic project creation
- the assembled local MCP server runtime is now also verified on the same manual-project path
- a first end-to-end runtime flow passed through:
  - `initialize`
  - `tools/list`
  - `tools/call(open_project)`
  - `tools/call(create_program)`
  - `tools/call(replace_text_document)`
  - `tools/call(append_text_document)`
  - `tools/call(insert_text_document)`
  - `tools/call(read_textual_implementation)`

### Stage B

Resume later after the automation chain is stable:

- automatic project creation
- automatic controller insertion
- full project bootstrap to POU flow

## Known Constraints

- SP20 main program startup alone does not prove the full automation chain is stable
- some automation paths previously triggered SP20 environment issues
- source projects can be locked by a running IDE session, so tests should use copied project files
- project layouts may differ and should not assume that `Application` exists as a top-level node

## 2026-04-23 Strategy Update

This repository should keep the agreed solution in this existing phase-plan file
instead of creating many new planning documents. That keeps context durable across
chat compression while keeping documentation lookup costs low.

The agreed implementation order is:

1. Add an explicit project-tree scan tool so clients can inspect the real device
   tree and nested `Application` structure before creating POU objects.
2. Keep the current server-side automatic `Application` fallback as a safety net,
   but treat scan-first as the recommended workflow.
3. Add end-to-end UTF-8 handling and read-after-write validation for textual
   document operations. Until that path is proven stable, keep the real IDE write
   path on ASCII-only source text.
4. Add declaration-plus-implementation source validation before writing generated
   POU code, so undeclared identifiers are rejected before the IDE project is
   modified.
5. Only after the validation path is stable, consider an automated repair flow
   that can propose or apply missing declarations.

### Immediate Next Slice

The next code slice should implement:

1. `list_project_objects` as a first-class MCP tool
2. tool registration and unit coverage for the new scan flow
3. client guidance updates so the recommended call order becomes:
   - `open_project`
   - `list_project_objects`
   - `create_*`
   - text read/write tools

### Implemented After This Update

The repository now also enforces these write-path rules for POU source text:

1. text write tools perform read-after-write round-trip verification
2. implementation writes are rejected before save if referenced identifiers are
   missing from the current declaration
3. declaration writes are rejected before save if they would break the current
   implementation
4. current real-IDE write path still stays on ASCII-only source text until
   end-to-end UTF-8 validation is proven stable

## Client Guidance

Codex can understand natural language and decompose tasks, but it still needs repository guidance.

Current client-facing guidance should come from:

- `docs/codex_client_handbook.md`
- `docs/api_specs/mcp_tools_phase1.md`
- this document

Current recommended tool order for new POU work is:

1. `open_project`
2. `list_project_objects`
3. `create_program` / `create_function_block` / `create_function`
4. textual read or write tools
