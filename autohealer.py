"""Standalone healing-only runner for the SoulBound client.

Reuses the proven telemetry and native item-use backend from the Ragnarok project.
No hunting, walking, combat, equipping, or inventory management is imported.
"""
from __future__ import annotations

import argparse
import random
import signal
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "vendor" / "Ragnarok"
if not (BACKEND / "diagnostics" / "authenticated_client.py").is_file():
    raise SystemExit("Backend missing. Run setup.bat first.")
sys.path.insert(0, str(BACKEND))

from diagnostics.authenticated_client import authenticated_client_monitor
from diagnostics.native_action_bridge import native_action_bridge

MEAT_ID = 517


class AutoHealer:
    def __init__(self, item="Meat", minimum=13, maximum=16, cooldown=0.9,
                 burst_min=1, burst_max=3, delay=0.2, interval=0.25):
        if not 1 <= minimum <= maximum <= 99:
            raise ValueError("Invalid HP threshold range")
        if not 1 <= burst_min <= burst_max <= 10:
            raise ValueError("Invalid healing burst range")
        self.item = item
        self.minimum = minimum
        self.maximum = maximum
        self.cooldown = max(0.25, cooldown)
        self.burst_min = burst_min
        self.burst_max = burst_max
        self.delay = max(0, delay)
        self.interval = max(0.1, interval)
        self.threshold = random.randint(minimum, maximum)
        self.last_use = 0.0
        self.stop = threading.Event()
        self.total = 0
        self.last_status = None

    def status(self, message):
        if message != self.last_status:
            print(message, flush=True)
            self.last_status = message

    def choose_item(self, inventory):
        wanted = self.item.strip().casefold()
        for row in inventory:
            if int(row.get("amount") or 0) < 1:
                continue
            name = str(row.get("name") or "").strip().casefold()
            item_id = int(row.get("name_id") or -1)
            if name == wanted or (wanted == "meat" and item_id == MEAT_ID):
                return row
        return None

    def tick(self, live, inventory, use_item, now=None):
        """One healing decision. Injectable action for unit tests."""
        now = time.monotonic() if now is None else now
        world = live.get("world") or {}
        hp, hp_max = world.get("hp"), world.get("hp_max")
        if hp is None or hp_max is None or int(hp_max) <= 0 or int(hp) <= 0:
            return "HP unavailable (or character dead)"
        hp = int(hp)
        hp_max = int(hp_max)
        hp_pct = hp * 100.0 / hp_max
        if hp_pct > self.threshold:
            return "HP %.1f%% | next heal at %d%%" % (hp_pct, self.threshold)
        if now - self.last_use < self.cooldown:
            return None

        target_id = world.get("self_account_id") or world.get("self_char_id")
        if target_id is None:
            return "Waiting for character ID"
        if not self.choose_item(inventory):
            return "Healing item '%s' not in detected inventory" % self.item

        successful = 0
        for i in range(random.randint(self.burst_min, self.burst_max)):
            # Re-read inventory every time to prevent stale item slot usage.
            latest = authenticated_client_monitor.item_state_snapshot().get("inventory") or []
            item = self.choose_item(latest)
            if not item:
                break
            result = use_item(int(item["index"]), int(target_id))
            if not result.get("ok"):
                return "Item use failed: %s" % result.get("reason", result)
            successful += 1
            if i < self.burst_max - 1 and self.delay:
                self.stop.wait(self.delay)
                if self.stop.is_set():
                    break

        if successful:
            self.last_use = time.monotonic()
            self.total += successful
            previous = self.threshold
            self.threshold = random.randint(self.minimum, self.maximum)
            return "HEALED at %.1f%% (threshold %d%%): %d x %s | total %d" % (
                hp_pct, previous, successful, self.item, self.total)
        return "Healing item unavailable"

    def run(self, patcher):
        print("SoulBound Autohealer | ONLY HP monitoring + healing item use")
        print("Threshold: %d-%d%% | item: %s | burst: %d-%d" % (
            self.minimum, self.maximum, self.item, self.burst_min, self.burst_max))
        print("Launch through SoulBound.exe. Ctrl+C stops the healer.")
        authenticated_client_monitor.start(str(patcher))
        try:
            while not self.stop.is_set():
                snapshot = authenticated_client_monitor.snapshot()
                pid = snapshot.get("classic_pid")
                if not pid:
                    self.status("Waiting for SoulBound login / Classic.exe...")
                else:
                    if not native_action_bridge.snapshot().get("attached"):
                        try:
                            native_action_bridge.start()
                        except Exception as exc:
                            self.status("Waiting for native client attachment: %s" % exc)
                            self.stop.wait(1.0)
                            continue
                    bridge = native_action_bridge.snapshot()
                    if not bridge.get("agent", {}).get("socket_learned"):
                        self.status("Waiting for game traffic / authenticated map socket...")
                    else:
                        live = snapshot.get("live_state") or {}
                        inventory = live.get("inventory") or []
                        outcome = self.tick(live, inventory, native_action_bridge.item_use)
                        if outcome:
                            self.status(outcome)
                self.stop.wait(self.interval)
        finally:
            native_action_bridge.stop()
            authenticated_client_monitor.stop()


def main():
    parser = argparse.ArgumentParser(description="SoulBound healing-only companion")
    parser.add_argument("--patcher", required=True, help="Full path to SoulBound.exe")
    parser.add_argument("--item", default="Meat")
    parser.add_argument("--min-hp", type=int, default=13)
    parser.add_argument("--max-hp", type=int, default=16)
    parser.add_argument("--burst-min", type=int, default=1)
    parser.add_argument("--burst-max", type=int, default=3)
    parser.add_argument("--cooldown", type=float, default=0.9)
    args = parser.parse_args()
    healer = AutoHealer(item=args.item, minimum=args.min_hp, maximum=args.max_hp,
                        burst_min=args.burst_min, burst_max=args.burst_max,
                        cooldown=args.cooldown)
    def shutdown(*_):
        healer.stop.set()
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    healer.run(Path(args.patcher).expanduser())


if __name__ == "__main__":
    main()
