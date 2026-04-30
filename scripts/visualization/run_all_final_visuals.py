"""
Run all visualization scripts that output to 'final visuals'.

Set MPLCONFIGDIR to a project-local writable dir so matplotlib works
in environments where ~/.matplotlib is read-only. Use Agg backend (set in each script).
Run from project root: python scripts/visualization/run_all_final_visuals.py
"""

import os
import sys
import subprocess

# Project root (parent of scripts/)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(ROOT)

# Writable matplotlib + fontconfig caches under project
mpl_dir = os.path.join(ROOT, '.mplconfig')
cache_dir = os.path.join(ROOT, '.cache')
fontconfig_cache = os.path.join(cache_dir, 'fontconfig')
os.makedirs(mpl_dir, exist_ok=True)
os.makedirs(fontconfig_cache, exist_ok=True)
env = os.environ.copy()
env['MPLCONFIGDIR'] = mpl_dir
env['XDG_CACHE_HOME'] = cache_dir
env['FONTCONFIG_USER_CACHE'] = fontconfig_cache

scripts = [
    'scripts/visualization/1_statization_of_network.py',
    'scripts/visualization/2_sectoral_repurposing.py',
    'scripts/visualization/3_personalization_individual_brokers.py',
    'scripts/visualization/4_network_consolidation_ratio.py',
    'scripts/visualization/5_strategic_narrowing.py',
    'scripts/visualization/6_finance_sector_statization.py',
    'scripts/visualization/7_network_size_evolution.py',
    'scripts/visualization/8_network_density_across_periods.py',
    'scripts/visualization/9_evolution_of_community_types.py',
    'scripts/visualization/sector_evolution_visualizations.py',
    'scripts/visualization/jurisdiction_evolution_no_russia.py',
    'scripts/visualization/network_evolution_no_labels.py',
    'scripts/visualization/create_conceptual_core_structure.py',
    'scripts/analysis/robustness_check_two_outlets.py',
]

def main():
    print("Regenerating all final visuals...")
    print("=" * 60)
    failed = []
    for s in scripts:
        name = os.path.basename(s)
        print(f"\n>>> {name}")
        sys.stdout.flush()
        r = subprocess.run(
            [sys.executable, s],
            cwd=ROOT,
            env=env,
            timeout=300,
        )
        if r.returncode != 0:
            failed.append(name)
            print(f"  FAILED: {name} (exit {r.returncode})")
        else:
            print(f"  OK: {name}")
    print("\n" + "=" * 60)
    if failed:
        print("FAILED:", ", ".join(failed))
        sys.exit(1)
    print("All visuals regenerated successfully.")

if __name__ == "__main__":
    main()
