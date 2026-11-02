# BlenderMCP

A fork of [mcp-for-blender](https://github.com/ahujasid/blender-mcp) (MIT) with our own tools and agents, so Claude can model, shade and animate in Blender 5.2 from a reference image, a drawing, or an idea.

**First goal (proposed, not yet confirmed by the user):** Claude models one prop from a reference image, gives it materials and lighting, renders a turntable animation, and the user accepts the result from the renders.

Current status lives in the vault note `План разработки`, not in this file.

## Language

- Talk to the user in Russian.
- Everything in the repository is in English: code, comments, MCP tool descriptions, commit messages, documentation, and all Claude configuration (`CLAUDE.md`, agents, settings).
- Names we create inside Blender (objects, materials, collections, actions) are in English.
- Designs in `designs/` are project output for the user, so their labels are in Russian.
- Obsidian vault notes are in Russian.

## The user

The user has never used Blender. Every time they must do something in Blender themselves, give click-by-click instructions: the menu path, the exact button or checkbox name as the English UI shows it, and the hotkey. Show results as renders through `look`, not as Blender terms. Never ask the user to do in Blender what a tool can do.

## Architecture

```
Claude ⇄ MCP server (uv, this checkout, src/blender_mcp) ⇄ TCP socket localhost:9876, JSON ⇄ addon (inside Blender, addon.py) ⇄ bpy
```

The addon runs a socket server in a thread and hands each command to Blender's main thread through a timer. The MCP server holds one connection and sends one command at a time. `execute_blender_code` runs arbitrary Python in the live Blender, which is how all modelling happens.

## Decisions

- We fork, we do not write from scratch. The remote `upstream` is `ahujasid/blender-mcp`. Keep our changes small and in separate modules, so merging upstream stays cheap.
- The MCP server runs from this checkout through `uv run --frozen mcp-for-blender`, not from PyPI, so our changes are live.
- Telemetry is off entirely: `DISABLE_TELEMETRY=true` in `.mcp.json`. The telemetry consent checkbox in the addon stays off.
- Safe mode (`BLENDER_MCP_SAFE_MODE`) stays off: modelling needs the whole of `bpy`. In exchange, scripts touch only files under `%USERPROFILE%\Documents\BlenderMCP` and the repository.
- The addon is installed as a copy named `blender_mcp.py` in Blender's user addons folder by `scripts\restart-blender.ps1`. `addon.py` in the repository is the source, the copy is the deployed build.
- Third-party generators (Tripo, Meshy, Hyper3D, Hunyuan3D) and asset libraries (Poly Haven, Sketchfab, Poly Pizza) stay switched off until the user asks for one. They call external services.
- Socket authentication: upstream has none. This is an open question in the vault, not decided.

Full history: the `Журнал решений` note in the vault. Open questions: the `Открытые вопросы` note. Do not decide open questions alone, discuss them with the user.

## Hard rules

1. **The user decides.** Confirm anything meaningful, and ask before actions that are hard to undo.
2. **Never invent context.** If you do not know a file, API or signature, look it up or ask. Check `bpy` members against the Blender 5.2 Python API docs (`https://docs.blender.org/api/5.2/`) or introspect them in the live Blender with `bl_rna`, as `src/blender_mcp/guides/bpy.md` shows.
3. **Never expand scope.** One task is one patch. Report other problems separately and wait for a go-ahead.
4. **The core is protected.** Do not change socket, threading or protocol code without an explicit request. The protected code:
   - `addon.py`, class `BlenderMCPServer`: `start`, `stop`, `_server_loop`, `_handle_client`, `execute_command`, `_execute_command_internal`
   - `src/blender_mcp/server.py`, class `BlenderConnection`: `connect`, `disconnect`, `receive_full_response`, `send_command`, `_send_command_locked`
   - `src/blender_mcp/safe_mode.py`

   A protocol change bumps `ADDON_PROTOCOL_VERSION` in `addon.py` and `EXPECTED_ADDON_PROTOCOL_VERSION` in `src/blender_mcp/addon_manager.py` together, and `tests/test_compat_matrix.py` must still pass.
5. **Verify after changes.** Run `uv run --with pytest pytest`, and exercise addon or tool changes in live Blender. If you cannot verify something, say so. Claude may restart Blender for this through `scripts\restart-blender.ps1`, which refuses to close a Blender with unsaved changes, and never by killing the process.
6. **Install nothing without consent.** Keep dependencies to a minimum and prefer what Python and Blender already provide. Before adding a package, check the GitHub Advisory Database and make sure the version is at least 14 days old unless it is a security fix. Pin exact versions and commit `uv.lock`. Verify downloaded programs by hash from two official sources and by digital signature before running them.
7. **Do not copy code from other projects.** Ideas only, and only with a checked license. Upstream is the one exception: it is this repository.

## Blender traps

- `execute_blender_code` runs from a timer, not from a UI area. Operators that need a viewport need `bpy.context.temp_override(area=..., region=...)`. Prefer `bpy.data` and object properties over `bpy.ops`.
- Blender runs one command at a time. A blocking call, such as `bpy.ops.render.render()` without `'INVOKE_DEFAULT'` or a long bake, freezes the UI and the socket. The server gives up after 180 s and the reply is lost. Keep calls short, render small, or render in a separate background Blender process.
- Headless Blender (`blender -b`) never runs the timer, so commands never execute. Blender must run with a GUI.
- Node names are localized. Find nodes by `type`, never by name. Principled BSDF inputs were renamed in 4.0, so get a socket with `inputs.get(...)` and a fallback. `material.use_nodes` is always on in 5.0+.
- `Action.fcurves` was removed in 5.0 (slotted actions). Insert keys with `obj.keyframe_insert(...)`, and reach fcurves through `bpy_extras.anim_utils.action_get_channelbag_for_slot`.
- `scene.render.engine` is a dynamic enum. Read its items rather than hardcoding them. EEVEE is `BLENDER_EEVEE` in 5.x.
- Always return to `OBJECT` mode at the end of a script. Edit mode left on blocks other operations and confuses the user.
- Hand-built geometry needs `mesh.validate()` and `mesh.update()`. After `bmesh`, call `bm.to_mesh(mesh)` and `bm.free()`.
- Blender's unit is the metre by default. Convert reference dimensions in millimetres and centimetres, and read `scene.unit_settings` before trusting a number.
- Object and material names must be unique. Blender silently appends `.001`, so read the name back after creation and use the returned name.
- `bpy.data.is_dirty` stays `False` after a script creates objects and materials through `bpy.data` (seen on 5.2.3). So the restart script's dirty check protects the user's own edits, not the script's: save with `bpy.ops.wm.save_mainfile()` before any restart. Whether such a script makes an undo step is not verified yet.
- The `Auto-Start Server` checkbox is a scene property, so a file saved with it off starts no server when opened.
- When port 9876 is already taken, for example by a second Blender, auto-start is skipped with only a console message.
- Closing Blender with unsaved changes opens a dialog that waits for a person. `scripts\restart-blender.ps1` asks `bpy.data.is_dirty` over the socket and refuses to close while it is true.
- Blender comes from Steam, which can update it between sessions. Check the version with `get_addon_status` at the start of a session.

## Environment

- Blender 5.2.3 LTS, installed by Steam: `D:\SteamLibrary\steamapps\common\Blender\blender.exe`. Starting the executable directly works without Steam. Its bundled Python is 3.13 and includes `requests`, which the addon needs.
- Blender user folder: `%APPDATA%\Blender Foundation\Blender\5.2`. Legacy addons go to `scripts\addons` inside it, which the restart script creates.
- Python 3.13 and uv 0.11 are on `PATH`. `.python-version` pins 3.11 for the server, which uv downloads on the first `uv sync`.
- Working files, that is `.blend` files and renders, live in `%USERPROFILE%\Documents\BlenderMCP`. References and briefs live in `designs/<slug>/`.

## Build and run

Run `uv` from the repository root.

- After a fresh clone: `uv sync --frozen`.
- Unit tests: `uv run --with pytest pytest`. pytest is not in upstream's lock file, so `--with` adds it for the run. `tests/test_compat_matrix.py` reads old addons from git history, so it needs the full clone.
- The MCP server is started by Claude Code from `.mcp.json`: `uv run --frozen mcp-for-blender` with telemetry off. After a server change, reconnect it through `/mcp` or start a new session.
- Deploy the addon and restart Blender: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\restart-blender.ps1`. It checks `bpy.data.is_dirty` over the socket, closes Blender with `CloseMainWindow`, copies `addon.py` to the user addons folder as `blender_mcp.py`, starts Blender with `scripts\enable-addon.py`, which enables the addon and saves preferences, and waits for the socket. When no addon answers in a running Blender, it stops and asks the user to close Blender by hand, unless `-SkipDirtyCheck` is passed after the user confirmed nothing is unsaved.
- Health check from Claude: `get_addon_status` returns the Blender version, the addon version and which libraries are on.

## Subagents

Defined in `.claude/agents/`. The main session orchestrates them. Suggest them when useful, and do not spawn them unprompted for trivial work.

**Development**

| Agent | Model | Role | Writes |
|---|---|---|---|
| `sniper` | Opus | Architecture, 3+ files, protected core, new MCP tools | Code |
| `debugger` | Sonnet | Errors, Blender console, fixes in 1-2 files | Code |
| `reviewer` | Opus | Audits patches before commit | Nothing |
| `tester` | Sonnet | Runs tools in live Blender on a disposable scene | Nothing |
| `documenter` | Sonnet | Maintains the vault | Vault only |

**Asset production**

| Agent | Model | Role | Writes |
|---|---|---|---|
| `art-director` | Opus | Turns a reference into an exact brief: parts, proportions, dimensions, materials, camera | `designs/<slug>/brief.md` |
| `modeler` | Opus | Builds the geometry from the brief | **The Blender scene, and it alone** |
| `lookdev` | Sonnet | Materials, lighting, camera, render settings | The Blender scene |
| `animator` | Sonnet | Rig and animation | The Blender scene |
| `inspector` | Opus | Compares renders and scene data with the brief and the reference | Nothing |

Order: the main session saves the reference into `designs/<slug>/reference/`, asks the user the few questions a beginner can answer (what it is, how big, what style, what matters most), then `art-director`, then the user approves the brief from its drawing, then `modeler`, `inspector`, `lookdev`, `inspector`, `animator`, `inspector`. `modeler` never starts before that approval. The user does not know Blender, so show renders (`designs/<slug>/renders/`) rather than Blender terms.

Blender runs one command at a time and the agents share one scene, so only one scene-writing agent runs at a time, and `tester` writes only to its own disposable `.blend` files.

## Workflow

Spec, then plan with tasks, then a `feat/...` branch. Each task goes to a subagent, followed by `reviewer`, and by `tester` when it touches Blender behaviour. Specs and plans live in the vault under `Архитектура/`. Run ledgers live in `.superpowers/`, which is not committed.

## Git

- Branches: `feat/...`, `fix/...`. Keep history linear. `main` tracks `upstream/main` so that `git fetch upstream` and a rebase or merge bring upstream changes in.
- Commit messages follow Conventional Commits, in English.
- Local commits need no confirmation. **Never push without explicit confirmation from the user.**
- No `Co-Authored-By` lines. The user is the sole author, and this applies to all subagents and plugins.

## Vault

- The project Obsidian vault is the directory listed in `permissions.additionalDirectories` in `.claude/settings.local.json`.
- Record every decision in `Журнал решений`: date, decision, reason.
- Add new questions to `Открытые вопросы`, and move closed ones to the decision log.
- Record verified Blender facts in `Справочник Blender API` with their source.
- Session summaries go to `Сессии/` as `YYYY-MM-DD-topic.md`.
