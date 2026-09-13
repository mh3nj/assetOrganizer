# Affinity engine setup

Use the new unified **Affinity** (Canva-era, with `Affinity.exe` and a
`Settings → MCP Server` toggle) instead of Photoshop/Illustrator to
open PSD, AI, and EPS files — plus native `.afphoto`, `.afdesign`,
and `.afpub` files.

Classic Affinity V2 (separate Photo/Designer/Publisher apps) has no
scripting API and can only open files, not drive the pipeline. The
steps below apply to the unified app only.

---

## 1. Enable the scripting server

1. Open Affinity.
2. Go to **Settings → MCP Server** and turn it **on**.
3. Enable the **FileSystem** permission (scripts need it).
4. Keep Affinity open, or let Asset Organizer launch it — either works.
   Your own open Affinity is never quit by the app.

## 2. Switch the engine

1. Launch Asset Organizer.
2. Click **⚙ Settings → Engine → Affinity**.
3. Click **Test Affinity connection** — you want `reachable ✓`.
4. Click **Save**. The status bar now reads `Ready (Affinity)`.

No restart, no `config.py` editing. The choice is stored machine-local
in `data/settings.json` (gitignored, never pushed).

## 3. How each stage works under Affinity

| # | Stage | Adobe | Affinity |
|---|-------|-------|----------|
| 1 | Open | COM `Open()` | `Affinity.exe <file>` launch |
| 2 | Export PNG | ExtendScript render | MCP `render` of the live canvas |
| 3 | Convert AVIF | same | same |
| 4 | Name prompt | same | same |
| 5 | Hide layers | ExtendScript | SDK script, **best-effort** (warns + continues) |
| 6 | Save | COM `Save()` | SDK script, **best-effort** (warns + continues) |
| 7 | Close tab | COM `Close(2)` | SDK script, **best-effort** |
| 8–11 | Rename/Archive/Verify/Cleanup | same | same |

Best-effort means: if your Affinity build names the API
differently, the step logs a warning and the job continues with the
file as-is instead of failing. Rename, archive, verify, and cleanup
are byte-level operations and always behave identically.

---

## Known limitations

- **Adobe file fidelity.** Affinity opens PSD/AI but may rasterize or
  approximate exotic effects, smart objects, and artboards. Check the
  preview before confirming the name — that is what gets archived.
- **Hide/save/close are best-effort.** The scripts in
  `scripts/affinity_pipeline.js` probe several API shapes per build
  and report what worked into the log. If your build disagrees
  everywhere, those three steps become no-ops with warnings.
- **MCP must stay on.** If Affinity is closed or the server is off,
  startup warns and Affinity jobs fail with a message telling you
  exactly that. Adobe jobs are unaffected.
- **One document at a time**, same as Adobe. The controller closes
  the previous document before opening the next.

---

## Hardening the scripts for your exact build

The SDK reference lives inside your running Affinity. To pin the
scripts to your build's exact API:

1. Point an MCP inspector at `http://127.0.0.1:6767/sse`.
2. Call `read_sdk_documentation_topic` for the documents/layers
   topics and note the exact save/close/visibility calls.
3. Update the strategy lists in `scripts/affinity_pipeline.js`
   (`aoSave`, `aoClose`, `aoHideVisibleLayers`).
4. Rebuild the exe (scripts ship inside it — always build from
   `AssetOrganizer.spec`).

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `MCP server not reachable` at startup | Open Affinity, enable Settings → MCP Server |
| `NOT_ALLOWED` in the log | Enable the FileSystem permission under MCP Server settings |
| `Affinity document timeout` | File may need conversion on open — open it once manually first |
| Preview looks different from Adobe's | Expected — Affinity's PSD/AI import is an approximation |
| `Affinity hide-layers unsupported` warning | Cosmetic — archive keeps layers; see hardening above |
