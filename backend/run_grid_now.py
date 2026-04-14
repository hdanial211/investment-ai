"""
run_grid_now.py — Force trigger satu Grid Sniper cycle sekarang.
Sama dengan apa bot buat setiap 3 minit.
"""
import sys, os
sys.path.insert(0, os.path.abspath('.'))

from scheduler.daily_job import run_rebalance_job

print("Triggering Grid Sniper cycle now...")
run_rebalance_job()
print("Done.")
