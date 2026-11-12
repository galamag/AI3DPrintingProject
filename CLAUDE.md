# AI 3D Printing Project

The user gives an order in words, a picture or a ready model. Claude designs the part in Blender, picks the filament and settings, slices it, shows the result, and after the user's yes starts the print on the user's Bambu Lab P2S and watches it. The user answers questions and takes the part off the bed.

Two MCP servers live in this repository:

- `blender`: a fork of [mcp-for-blender](https://github.com/ahujasid/blender-mcp) (MIT) with our own tools and agents, so Claude can model, shade and animate in Blender 5.2 from a reference image, a drawing, or an idea. The project started as this fork under the name BlenderMCP; the working folder and some notes still carry that name.
- `print`: our own package `src/print_mcp`, which slices through the Bambu Studio command line and sees and clicks the Bambu Studio window in the background.

**Reached so far:** Hornet from Hollow Knight: Silksong, modelled, lit and animated, accepted by the user on 2026-11-02 (`designs/hornet/`). A 20 mm test cube printed on 2026-11-12, started by Claude through the Bambu Studio window with foreground clicks, before the background tools existed. **Current goal:** one single-colour part goes from Blender to a finished print with the user only answering questions. FreeCAD and multi-colour prints come later.

Current status lives in the vault note `План разработки`, not in this file.

## Language

- Talk to the user in Russian.
- Everything in the repository is in English: code, comments, MCP tool descriptions, commit messages, documentation, and all Claude configuration (`CLAUDE.md`, agents, settings).
- Names we create inside Blender (objects, materials, collections, actions) are in English.
- Designs in `designs/` (briefs, part diagrams, notes) are in English too. The user asked for this on 2026-11-02.
- Obsidian vault notes are in Russian.
- Labels of a localized program are quoted exactly as its UI shows them, followed by the English meaning in parentheses.

## The user

The user has never used Blender and is new to 3D printing. Every time they must do something in Blender or Bambu Studio themselves, give click-by-click instructions: the menu path, the exact button or checkbox name as the UI shows it (Blender's is English, Bambu Studio's is Russian), and the hotkey. Show results as renders through `look` and as plate pictures, not as Blender or slicer terms. Never ask the user to do by hand what a tool can do.

The user works at this PC while Claude works. Never take over the screen to drive an app: no computer-use control of Bambu Studio or other apps, no moving the mouse, no hiding windows. If a step truly needs the screen, ask first. Restarting Blender or opening a file with `studio_open` starts a window that may appear in front of the user's windows, so say so before doing it.

## Architecture

```
Claude ⇄ MCP server (uv, this checkout, src/blender_mcp) ⇄ TCP socket localhost:9876, JSON ⇄ addon (inside Blender, addon.py) ⇄ bpy
```

The addon runs a socket server in a thread and hands each command to Blender's main thread through a timer. The MCP server holds one connection and sends one command at a time. `execute_blender_code` runs arbitrary Python in the live Blender, which is how all modelling happens. `export_for_print` (our module `src/blender_mcp/print_export.py`) writes named or selected objects as one millimetre STL with a mesh report and does not change the scene.

```
Claude ⇄ MCP server print (uv, src/print_mcp) ─┬─ bambu-studio.exe command line (subprocess) → .gcode.3mf
                                               └─ Bambu Studio window (Win32: PrintWindow capture, PostMessage clicks) → Bambu Cloud → printer
```

The `print` server adds no dependencies: besides the `mcp` package the fork already uses, it needs only the standard library. Its tools: `list_print_profiles`, `slice_model`, `inspect_sliced`, `studio_windows`, `studio_capture`, `studio_open`, `studio_click`. There is no network link to the printer: Claude sees and drives it only through the Bambu Studio window, with the user's own cloud sign-in.

## Decisions

- We fork, we do not write from scratch. The remote `upstream` is `ahujasid/blender-mcp`. Keep our changes small and in separate modules, so merging upstream stays cheap.
- Both MCP servers run from this checkout through `uv run --frozen`, not from PyPI, so our changes are live.
- Telemetry is off entirely: `DISABLE_TELEMETRY=true` in `.mcp.json`. The telemetry consent checkbox in the addon stays off.
- Safe mode (`BLENDER_MCP_SAFE_MODE`) stays off: modelling needs the whole of `bpy`. In exchange, scripts touch only files under `%USERPROFILE%\Documents\BlenderMCP` and the repository.
- The addon is installed as a copy named `blender_mcp.py` in Blender's user addons folder by `scripts\restart-blender.ps1`. `addon.py` in the repository is the source, the copy is the deployed build.
- Third-party generators (Tripo, Meshy, Hyper3D, Hunyuan3D) and asset libraries (Poly Haven, Sketchfab, Poly Pizza) stay switched off until the user asks for one. They call external services.
- The print server is our own code, not a third-party MCP: the existing ones fail on licence, platform or trust.
- The printer is driven through the Bambu Studio window, not over the network. `LAN Only` and `Developer Mode` stay off, so the cloud and the Handy app keep working.
- Bambu Studio is controlled in the background only, through the `studio_*` tools, unless the user agrees to hand over the screen for one step.
- Print code lives in its own package beside the fork. In `src/blender_mcp` our additions are separate modules plus an import and a `register` call in `server.py`.
- Print export is STL only. Blender 5.2 has no built-in 3MF export.
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
5. **Verify after changes.** Run `uv run --with pytest pytest`, and exercise addon or tool changes in live Blender. Print-tool changes are exercised against a live Bambu Studio window with captures and harmless clicks only, never on print controls. If you cannot verify something, say so. Claude may restart Blender for this through `scripts\restart-blender.ps1`, which refuses to close a Blender with unsaved changes, and never by killing the process.
6. **Install nothing without consent.** Keep dependencies to a minimum and prefer what Python and Blender already provide. Before adding a package, check the GitHub Advisory Database and make sure the version is at least 14 days old unless it is a security fix. Pin exact versions and commit `uv.lock`. Verify downloaded programs by hash from two official sources and by digital signature before running them.
7. **Do not copy code from other projects.** Ideas only, and only with a checked license. Upstream is the one exception: it is this repository.

## Print rules

1. **A print starts only after the user's explicit yes, given for that one print.** Show the plate picture, time, weight, filament and AMS slot first. An earlier yes, a yes for another file, or a yes relayed by an agent does not count.
2. **Only the main session clicks `Отправить` (Send), pause or stop.** Subagents never do. Never resume or restart a print without the user.
3. **Before sending, look.** The camera on the `Устройство` (Device) tab must show a live picture of an empty bed on the right printer. In the send dialog, check the printer, the plate type, the AMS slot and colour, and the time and weight against the slice. Anything unclear means stop and ask.
4. **Stopping.** The main session may stop a print on its own only on an obvious failure seen in a capture (the part came off, a tangle of filament, an error on screen), after checking that the printer and job on screen are the ones it sent. Tell the user at once.
5. **Stay inside the shipped profiles.** Temperatures and speeds do not leave the filament profile's limits without the user's separate consent. `slice_model` refuses overrides of temperatures and G-code; do not look for another way. It does not refuse speed overrides and nothing checks them against the filament's maximum volumetric speed, so any speed change needs the user's consent.
6. **Hands off the account.** Do not read the Bambu account data, the printer's access code, or anything under `%APPDATA%\BambuStudio`.
7. **Never call `bambu-studio.exe` from the command line yourself; command-line slices go only through `slice_model`.** The Bambu Studio command line ignores `inherits` and `include` in profile files, so a direct call slices with built-in defaults (wrong bed temperature, generic start G-code). The server flattens the profiles first.
8. **Version print files** as `<part>-v<N>.stl` and `<part>-v<N>.gcode.3mf` and never overwrite them: Bambu Studio may still have the old file open under the same name.
9. **Watching a print works only while this session and the Bambu Studio window are open.** It does not replace the printer's own protection, and the user should know that before a long or overnight print.

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

## Bambu Studio traps

- The command line writes nothing to the console. The outcome is the exit code and `result.json` in the process's working folder. Without profiles it crashes with `0xC0000005`.
- A `.gcode.3mf` opened in the window comes up on the `Подготовка` (Prepare) tab and has to be sliced again there with `Нарезать пластину` (Slice plate). So the job the printer gets is the window's slice, not the command line's; compare the two before sending.
- The command-line slice takes the Standard nozzle values (flow ratio 1.01, lower speeds) although the printer has a high-flow nozzle, and the window's `Поток` (Flow) list also stands on `Стандартный` (Standard). How to select the high-flow variant is not known yet; see the spec's list of things to find out. No command-line slice has been printed directly yet.
- A computer-use screenshot shows the Bambu Studio window as a blank frame and hides the user's windows. Use `studio_capture`.
- The model's image is shrunk above 1568 px or 1.15 MP, so `studio_capture` caps its output and reports the real scale. Compute click positions with the formula in its reply, and pass `expected_width` and `expected_height` to `studio_click`.
- A modal dialog, such as the send dialog, is a separate window: find it with `studio_windows`. Clicks on the main window are refused while it is open.
- `studio_open` matches an open window by file name only and then starts nothing. Hover popups and tooltips are separate windows of the process.
- Buttons are drawn by the program itself. Their positions depend on window size and version, so never keep coordinates in code or instructions.
- The camera view on the `Устройство` (Device) tab may be paused (seen on 2026-11-12 after the printer sat idle); its play button gives a fresh frame.
- An image captured by a subagent stays with the subagent; only its text report comes back. To see a window, the main session captures it itself.
- Not verified in the background yet: `Печатать пластину` (Print plate), the send dialog, a minimized window, display scaling other than 100 %, and whether a window started by `studio_open` covers the user's windows.

## Environment

- Blender 5.2.3 LTS, installed by Steam: `D:\SteamLibrary\steamapps\common\Blender\blender.exe`. Starting the executable directly works without Steam. Its bundled Python is 3.13 and includes `requests`, which the addon needs.
- Blender user folder: `%APPDATA%\Blender Foundation\Blender\5.2`. Legacy addons go to `scripts\addons` inside it, which the restart script creates.
- Python 3.13 and uv 0.11 are on `PATH`. `.python-version` pins 3.11 for the server, which uv downloads on the first `uv sync`.
- Working files, that is `.blend` files and renders, live in `%USERPROFILE%\Documents\BlenderMCP`. References and briefs live in `designs/<slug>/`, print files in `designs/<slug>/print/`. Model, output and picture paths given to the print tools and to `export_for_print` must lie under the repository or that folder. `PRINT_MCP_WORK_DIR` adds one more folder; it is unset, and renaming the working folder is an open question.
- Bambu Studio 02.09.01.70: `C:\Program Files\Bambu Studio\bambu-studio.exe`, system profiles in `resources\profiles\BBL`. `BAMBU_STUDIO_DIR` overrides the folder. The interface is in Russian. An update can move buttons and change profiles, so check the version when something looks different: `(Get-Item 'C:\Program Files\Bambu Studio\bambu-studio.exe').VersionInfo.FileVersion`.
- Printer: Bambu Lab P2S with AMS 2 Pro, hardened steel high-flow 0.4 mm nozzle, textured PEI plate, build volume 256 x 256 x 256 mm, reached through Bambu Cloud. Profiles: machine `Bambu Lab P2S 0.4 nozzle`, bed type `Textured PEI Plate`. What is loaded in the AMS changes: ask the user or read it from the `Устройство` tab, and see the vault note `Принтер Bambu Lab P2S`.

## Build and run

Run `uv` from the repository root.

- After a fresh clone: `uv sync --frozen`.
- Unit tests: `uv run --with pytest pytest`. pytest is not in upstream's lock file, so `--with` adds it for the run. `tests/test_compat_matrix.py` reads old addons from git history, so it needs the full clone.
- The print server is also started from `.mcp.json`: `uv run --frozen python -m print_mcp.server`. It needs no Blender, and the sign that it is up is `list_print_profiles` answering. `tests/test_print_live.py` and `tests/test_print_studio_live.py` run real slices and window captures when Bambu Studio is installed or open, and skip otherwise; they never click and never print. `tests/test_print_export_math.py` needs numpy, which is not a project dependency, so it skips in the normal run; add `--with numpy` to run it.
- The Blender MCP server is started by Claude Code from `.mcp.json`: `uv run --frozen mcp-for-blender` with telemetry off. The desktop app loads it silently in a trusted folder, with no approval dialog, so the sign that it is up is `get_addon_status` answering, not a message. After a server change, reconnect it through `/mcp` or start a new session.
- Deploy the addon and restart Blender: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\restart-blender.ps1`. It checks `bpy.data.is_dirty` over the socket, closes Blender with `CloseMainWindow`, copies `addon.py` to the user addons folder as `blender_mcp.py`, starts Blender with `scripts\enable-addon.py`, which enables the addon and saves preferences, and waits for the socket. When no addon answers in a running Blender, it stops and asks the user to close Blender by hand, unless `-SkipDirtyCheck` is passed after the user confirmed nothing is unsaved.
- Health check from Claude: `get_addon_status` returns the Blender version, the addon version and which libraries are on.
- Final renders never go through the socket, because a Cycles render blocks the addon. Save the file, then run a background Blender from the repository root: `scripts\render-views.py` renders the brief's five views through `Cam_02_Hero` by rotating `Rig_Pivot`, plus the close-up camera; `scripts\render-animation.py` bakes every point cache (cloth), renders optional PNG stills and then the frame range to an H.264 MP4. Both take their arguments after `--`; see the docstrings. Example: `"D:\SteamLibrary\steamapps\common\Blender\blender.exe" -b "%USERPROFILE%\Documents\BlenderMCP\hornet.blend" -P scripts\render-animation.py -- designs\hornet\renders\out.mp4 128 1 stills:1,96,192`. Blender 5.x needs `image_settings.media_type = 'VIDEO'` before `file_format = 'FFMPEG'`; the scripts handle it. A saved file keeps the cloth setup but not the bake, so every animation render starts with a bake (about a minute for Hornet).

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

**Printing**

| Agent | Model | Role | Writes |
|---|---|---|---|
| `print-engineer` | Opus | Printability, filament and settings, export and slice | `designs/<slug>/print/` |
| `print-operator` | Sonnet | Opens the file in Bambu Studio, brings it to the checked send dialog, reports printer status | Nothing, only background clicks and captures |

Print order, after the inspector passed the geometry: `print-engineer` checks, exports and slices; the main session shows the plate picture, time, weight, filament and slot and asks the user; on a yes, `print-operator` prepares the window and runs the pre-send check; the main session then captures the send dialog itself (the `hwnd` is in the operator's report), checks the printer, plate type, AMS slot and colour, time and weight, and clicks `Отправить`; it takes a status right after sending to confirm the right printer started the right job, then after the first layer, then every 10 minutes for prints under an hour or every 30 for longer ones, and at the end. Between checks the session waits with a scheduled wake-up or a background timer; if it has no way to wait, it tells the user that the print is not being watched. A brief for a printed part carries a Print section, and the modeler builds at real size. A part that is only printed skips `lookdev` and `animator`: brief, approval, `modeler`, `inspector`, then the print order.

Order: the main session saves the reference into `designs/<slug>/reference/`, asks the user the few questions a beginner can answer (what it is, how big, what style, what matters most), then `art-director`, then the user approves the brief from its drawing, then `modeler`, `inspector`, `lookdev`, `inspector`, `animator`, `inspector`. `modeler` never starts before that approval. The user does not know Blender, so show renders (`designs/<slug>/renders/`) rather than Blender terms.

Blender runs one command at a time and the agents share one scene, so only one scene-writing agent runs at a time, and `tester` writes only to its own disposable `.blend` files. There is one printer, so only one of the main session and `print-operator` clicks in Bambu Studio at a time.

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
