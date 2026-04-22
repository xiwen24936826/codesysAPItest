# Current Phase Plan

Updated: 2026-04-22

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
4. `read_textual_declaration`
5. `read_textual_implementation`
6. `replace_text_document`
7. `append_text_document`
8. `insert_text_document`

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

## Client Guidance

Codex can understand natural language and decompose tasks, but it still needs repository guidance.

Current client-facing guidance should come from:

- `docs/codex_client_handbook.md`
- `docs/api_specs/mcp_tools_phase1.md`
- this document
