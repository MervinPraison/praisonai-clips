# Connect Codex to your editor

Ask Codex to make a change and watch it appear in your open video editor. The live integrations have different setup requirements and tested version constraints. Start with a disposable project copy, and review changes before saving or sharing.

## What is included?

- **A Codex skill for Resolve on macOS:** instructions for setup, troubleshooting, and verified live editing. Codex can discover it when you open this repository as your workspace.
- **Resolve MCP server:** local tools that use the shared Resolve SDK to inspect and edit a running project. This is included in the optional `live` install.
- **Kdenlive MCP bridge:** a separate Mac bridge with seven live tools. It requires a specially prepared copy of Kdenlive; the standard app alone is not enough.
- **CLI and Python SDK:** other ways to use the workflows without Codex. See the [CLI reference](../reference/cli.md) and [Resolve SDK](../reference/resolve-sdk.md).

MCP gives Codex tools to call; the skill gives it the tested workflow. Listing a server confirms registration, not a working editor connection.

## Resolve on macOS

1. Clone this repository and open its folder in Codex. In Terminal, from that folder, install the project and register the MCP server:

    ```sh
    python3 -m venv .venv
    .venv/bin/python -m pip install -e '.[live]'
    codex mcp add praisonai-resolve -- "$PWD/.venv/bin/praisonai-resolve-mcp"
    codex mcp list
    ```

2. Open DaVinci Resolve and a project, and keep your Mac unlocked. macOS may ask you to grant Accessibility access to the app running the commands. Resolve's Lua Console may briefly take focus; the tested route uses keyboard and clipboard automation without moving the mouse.
3. Start a new Codex chat in this repository and ask:

    > Use the resolve-mac-live skill. Check my open Resolve project, then show me the timeline and help me adjust the framing of a clip.

4. Confirm Codex reports the real project and timeline before asking it to change a clip. Review the result in Resolve. For quiet-pause removal, ask for a **review timeline** and listen to the cuts. Current limitations are in the [Resolve guide](../reference/resolve-sdk.md#prepare-a-quiet-pause-review-timeline).

If the skill is not visible, restart Codex. If the server does not connect, see the [Mac runbook](../editors/resolve-runbook.md). The tested setup uses DaVinci Resolve Free 21.1 on macOS; other versions need revalidation.

## Kdenlive on macOS

The Kdenlive bridge is separate from the Resolve server and does not currently have a bundled Codex skill. Follow the [Kdenlive Mac setup](../KDENLIVE_LIVE_CONTROL.md#native-mac-live-bridge) to install its prerequisites, build the bridge and launch a **project copy** in the isolated editor. Then, from the repository root:

```sh
codex mcp add praisonai-kdenlive -- "$PWD/scripts/kdenlive-mac-live" mcp
codex mcp list
```

Start a new Codex chat and ask: “Check the live Kdenlive status, select the intended clip, and help me adjust its framing.” The tested bridge supports status, sequence selection, seeking, framing, undo, redo, and saving. Framing requires the expected native Transform effect; see the guide for version requirements and limitations. Resolve's quiet-pause workflow is not a Kdenlive feature.

## How the pieces fit

```text
Your request in Codex → skill instructions + MCP tools → editor bridge → open editor
                                                                      ↓
                                                         You review the change
```

These are local integrations, not hosted services or one-click plugins. Do not paste your API keys into chat. For Codex's MCP configuration, see the [official OpenAI guide](https://learn.chatgpt.com/docs/extend/mcp?surface=cli); for skill discovery, see [Build skills](https://learn.chatgpt.com/docs/build-skills).
