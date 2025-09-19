#!/usr/bin/env python3
"""
Repair NIFTY 500 symbols: try NSE (.NS) then BSE (.BO) fallback and remove irrecoverable symbols.
Produces output/failed_nifty500_report.csv and updates nifty500_symbols.py (creates a backup).
"""
import argparse
import csv
import shutil
import logging
import time
from pathlib import Path

import yfinance as yf

REPO_ROOT = Path(__file__).resolve().parents[1]
SYMBOLS_FILE = REPO_ROOT / 'nifty500_symbols.py'
BACKUP_FILE = REPO_ROOT / 'nifty500_symbols.py.bak'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('repair')


def load_symbols():
    # Import the file as a module by executing it safely
    ns = {}
    with open(SYMBOLS_FILE, 'r', encoding='utf-8') as f:
        code = f.read()
    exec(code, ns)
    # return the full namespace so caller can pick the list they want
    return ns


def validate_symbol(symbol: str, period: str = '5d') -> bool:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist is None:
            return False
        return not hist.empty
    except Exception:
        return False


def run(target: str = 'nifty500'):
    ns = load_symbols()

    # Determine which symbol list to target
    target_map = {
        'nifty500': 'NIFTY_500_SYMBOLS',
        'nifty100': 'NIFTY_100_SYMBOLS',
        'nifty50': 'NIFTY_50_SYMBOLS',
    }

    if target not in target_map:
        logger.error('Unknown target %s; choose from nifty50/nifty100/nifty500', target)
        return

    list_name = target_map[target]
    symbols = ns.get(list_name, [])
    logger.info(f"Loaded {len(symbols)} symbols for {list_name}")

    results = []
    updated_symbols = []

    for s in symbols:
        logger.info(f"Checking {s}")
        ok = validate_symbol(s)
        if ok:
            updated_symbols.append(s)
            results.append((s, 'ok', 'n/a'))
            time.sleep(0.05)
            continue

        # Try BSE fallback: replace .NS with .BO if applicable
        if s.endswith('.NS'):
            bse = s[:-3] + '.BO'
            logger.info(f"{s} failed, trying BSE {bse}")
            ok_bse = validate_symbol(bse)
            if ok_bse:
                updated_symbols.append(bse)
                results.append((s, 'replaced', bse))
                time.sleep(0.05)
                continue

        # If we reach here, symbol is irrecoverable
        logger.warning(f"{s} failed on both NSE and BSE (or not applicable)")
        results.append((s, 'removed', 'n/a'))
        # don't append to updated_symbols

        # Small delay to be nice to Yahoo
        time.sleep(0.1)

    # Write report (per target)
    report_file = REPO_ROOT / 'output' / f'failed_{target}_report.csv'
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['original_symbol', 'action', 'replacement'])
        for r in results:
            writer.writerow(r)

    # Backup original symbols file
    shutil.copy2(SYMBOLS_FILE, BACKUP_FILE)
    logger.info(f"Backup of symbols file created at {BACKUP_FILE}")

    # Build new content replacing the chosen list literal
    with open(SYMBOLS_FILE, 'r', encoding='utf-8') as f:
        src = f.read()

    start_marker = f'{list_name} = ['
    start_idx = src.find(start_marker)
    if start_idx == -1:
        logger.error('Could not find %s marker in file; aborting update', list_name)
        return

    before = src[:start_idx]
    after_start = src[start_idx:]
    # Find the end of the list (the closing bracket)
    end_idx = after_start.find(']\n')
    if end_idx == -1:
        end_idx = after_start.find(']')
        if end_idx == -1:
            logger.error('Could not find end of %s list; aborting update', list_name)
            return

    end_idx += len(']')
    after = after_start[end_idx:]

    # Build the new list string
    list_lines = [f'    "{sym}",' for sym in updated_symbols]
    new_list = f'{list_name} = [\n' + '\n'.join(list_lines) + '\n]\n\n'

    new_src = before + new_list + after

    with open(SYMBOLS_FILE, 'w', encoding='utf-8') as f:
        f.write(new_src)

    logger.info(f"Updated symbols file written. Report at {report_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Repair NIFTY symbols (NSE -> BSE fallback)')
    parser.add_argument('--target', choices=['nifty50', 'nifty100', 'nifty500'], default='nifty500',
                        help='Which list to repair in nifty500_symbols.py')
    args = parser.parse_args()
    run(target=args.target)
