#!/usr/bin/env python3
"""
monitor.py


Sample host resource usage plus HTTP availability and write results to CSV.

Parameter summary
+-----------+---------+-----------------------------------------------+
| CLI flag  | type    | default / purpose                             |
+-----------+---------+-----------------------------------------------+
| -d, --dur | int     | 300  - total capture time (seconds)           |
| -i, --int | float   | 1.0 - sample period (seconds)                 |
| -n, --nic | str     | "eth0" - network interface to monitor         |
| -u, --url | str     | "http://localhost" - URL health-check target  |
| -o, --out | path    | auto-generated CSV file name                  |
+-----------+---------+-----------------------------------------------+

"""
from __future__ import annotations
import argparse, csv, time, datetime, pathlib, psutil, requests, os, sys
from collections import deque

# ─────────────── helpers ──────────────────────────────────────────────
def mbps(bytes_delta: int, seconds: float) -> float:
    return bytes_delta * 8 / 1024 / 1024 / seconds

def bot_count() -> int:
    try:
        text = pathlib.Path("bot_count.txt").read_text().strip()
        return int(text) if text else 0
    except FileNotFoundError:
        return 0
    except ValueError:
        return 0

# ─────────────── main routine ─────────────────────────────────────────
def monitor(args: argparse.Namespace) -> None:
    csv_path = args.out or pathlib.Path(
        f"data_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv"
    )

    # prime network counters
    net_prev = psutil.net_io_counters(pernic=True).get(args.nic)
    if net_prev is None:
        print(f"✖ Interface {args.nic!r} not found - abort.", file=sys.stderr)
        sys.exit(1)

    with csv_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["Datum", "Cas", "Boti", "CPU[%]", "RAM[%]", "Net[Mb/s]", "Stav"]
        )

        start = time.perf_counter()
        samples = deque()           # for summary

        while (elapsed := time.perf_counter() - start) < args.dur:
            now = datetime.datetime.now()
            datum, cas = now.date().isoformat(), now.time().strftime("%H:%M:%S")

            # CPU & RAM
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent

            # network delta
            net_now = psutil.net_io_counters(pernic=True)[args.nic]
            bytes_delta = (net_now.bytes_recv - net_prev.bytes_recv) + (
                net_now.bytes_sent - net_prev.bytes_sent
            )
            net_prev = net_now
            net = mbps(bytes_delta, args.int)

            # health check
            try:
                requests.get(args.url, timeout=2).raise_for_status()
                status = "Funkcni"
            except Exception:
                status = "Vypadek"

            row = [datum, cas, bot_count(), f"{cpu:.0f}", f"{ram:.0f}", f"{net:.2f}", status]
            writer.writerow(row)
            fh.flush()
            samples.append((cpu, ram, net))

            time.sleep(args.int)

    # ───── summary ─────
    if samples:
        cpu_avg = sum(s[0] for s in samples) / len(samples)
        ram_avg = sum(s[1] for s in samples) / len(samples)
        net_avg = sum(s[2] for s in samples) / len(samples)
        print(f"── {args.dur}s summary ──")
        print(f"Samples           : {len(samples)} (every {args.int}s)")
        print(f"Average CPU usage : {cpu_avg:.1f} %")
        print(f"Average RAM usage : {ram_avg:.1f} %")
        print(f"Average net xfer  : {net_avg:.2f} Mb/s")
    print(f"CSV saved → {csv_path}")

# ─────────────── CLI ──────────────────────────────────────────────────
def parse_cli() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Resource-monitor to CSV")
    p.add_argument("-d", "--dur",  type=int,   default=300,   help="duration seconds (default 300)")
    p.add_argument("-i", "--int",  type=float, default=1.0,   help="sample interval seconds (default 1)")
    p.add_argument("-n", "--nic",  default="eth0",            help="network interface (default eth0)")
    p.add_argument("-u", "--url",  default="http://localhost",help="URL for health probe")
    p.add_argument("-o", "--out",  type=pathlib.Path,         help="output CSV path")
    return p.parse_args()

if __name__ == "__main__":
    monitor(parse_cli())
