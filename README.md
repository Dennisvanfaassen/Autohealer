# SoulBound Autohealer

Healing-only companion for SoulBound Ragnarok Online, reusing the **authenticated live-HP/inventory monitor** and **native item-use bridge** from [Dennisvanfaassen/Ragnarok](https://github.com/Dennisvanfaassen/Ragnarok).

This standalone launcher **does not start or import the hunting AI, pathing, macros, or movement/combat controllers**. It launches the normal SoulBound patcher, waits for the logged-in Classic.exe game, monitors HP, and consumes healing items when needed.

## Install (Windows)

1. Install Python 3 and Git for Windows.
2. Download or clone this repository.
3. Run `setup.bat` (downloads the proven backend and installs Python dependencies).
4. Ensure Npcap is installed, as for the original Ragnarok bot; packet sniffing requires it and may require elevation.
5. Edit the `SOULBOUND_PATCHER` path in `run.bat` if your client is installed elsewhere.
6. Run `run.bat`. Log into SoulBound using the launched patcher. Keep the console open.

**Important:** Start the game via `run.bat` so the packet monitor sees the login, inventory, and HP state. If the game was already running, close and restart it via the launcher.

## Default behavior

- Pick one random HP threshold of **13%, 14%, 15%, or 16%**. Keep that threshold until a healing action succeeds.
- At or below the selected threshold, consume **1–3 Meat** with **0.2 s** between item uses and a **0.9 s** decision cooldown. Randomize the threshold after a successful healing action.
- Only consume an item when live HP, max HP, self character/account ID, inventory slot, and native action socket are available.
- Do not heal if HP is 0 or telemetry is missing. There are no navigation, attack, loot, gear-switch, or town actions.

## Settings

Edit `run.bat`, or run the script with `--item "White Potion"`, `--burst-min 1 --burst-max 1`, `--min-hp 13 --max-hp 16`, `--cooldown 0.9`. Item names must match inventory telemetry. Default is Meat (item ID 517 fallback).

Ctrl+C stops the autohealer and detaches the action bridge; the game remains running.

## Notes

- The setup retrieves the **current** Ragnarok main branch. To freeze the exact backend behavior, pin a tested commit in the clone command.
- Uses game-client process attachment and packet monitoring; this may conflict with server rules or anti-cheat software. Do not use it where prohibited.
- Not yet validated live against SoulBound on your machine; check console output and verify the first heal manually. If inventory isn't recognized, check that the client was started through this launcher and the map packets were captured.
