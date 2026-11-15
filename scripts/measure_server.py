"""Isolated child-process high-water memory measurement for benchmarks."""
import argparse
import json
import resource
import signal
import subprocess
import sys
import time

p = argparse.ArgumentParser(); p.add_argument('--output', required=True); p.add_argument('command', nargs=argparse.REMAINDER); args = p.parse_args()
command = args.command[1:] if args.command and args.command[0] == '--' else args.command
child = subprocess.Popen(command)
def stop(*_):
    if child.poll() is None: child.terminate()
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
try:
    while child.poll() is None: time.sleep(.05)
finally:
    stop(); child.wait(timeout=15)
    high = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    divisor = 1024**2 if sys.platform == 'darwin' else 1024
    with open(args.output, 'w') as f: json.dump({'peak_rss_mib': high / divisor}, f)
