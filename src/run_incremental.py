# -*- coding: utf-8 -*-
"""Single entry point for the incremental refresh.

Runs the whole chain end to end, each step shelling out to the existing script
unchanged so the output stays identical to a manual run:

    crawl -> convert -> match -> fill chair names -> extract events
          -> enrich events -> QC

This is the entry point meant to be scheduled (e.g. daily) and to run inside
the container of the repo Dockerfile. It is the *incremental* path: the match,
extract, enrich and QC steps reprocess whatever record files are present in
_data/, so it is designed for a working directory that holds only the new
sittings (a fresh checkout plus --since). It is not the tool for the one-time
full rebuild of 1989-today, which still uses the per-batch scripts for memory
economy (see README, steps 6-9).

Lean / watermark mode:
    --since YYYY-MM-DD passes a watermark to the crawler, so only sittings
    newer than that date are downloaded. On a fresh working directory this lets
    the daily run touch only the new sittings, without the ~16 GB historical
    archive on disk. The watermark is normally the latest sitting_date already
    loaded in the platform database.

Exit codes:
    0  finished, no suspect sittings
    2  finished, but the QC report flagged one or more sittings as suspect. The
       data is still produced; the loader should hold these sittings out of the
       public aggregates and an operator should look (see event_stream_qc.py).
    1  a step failed
"""
import os
import sys
import csv
import subprocess
from argparse import ArgumentParser

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SRC_DIR, '..', 'out_files')

# paths are relative to SRC_DIR, matching how the individual scripts expect to
# be run (and how convert2txt.py invokes tika-app-1.20.jar by a relative name)
DATA = '../_data/'
EVENTS = '../events/'
EVENTS_ENRICHED = '../events_enriched/'
TELL_ALL = '../out_files/tell_all.csv'            # matcher raw output
TELL_ALL_CLEAN = '../out_files/tell_all_final.csv'  # matcher cleaned output
TELL_ALL_FILLED = '../out_files/tell_all_FILLED.csv'  # after chair-name fill
QC_CSV = '../out_files/event_stream_qc.csv'


def run(step, argv):
    print('\n=== ' + step + ' ===', flush=True)
    result = subprocess.run([sys.executable] + argv, cwd=SRC_DIR)
    if result.returncode != 0:
        print('STEP FAILED:', step, '(exit', result.returncode, ')', flush=True)
        raise SystemExit(1)


def main():
    parser = ArgumentParser(description="Run the incremental refresh chain.")
    parser.add_argument('--since', default=None,
                        help="watermark ISO date (YYYY-MM-DD): only download sittings "
                             "newer than this. Normally the latest sitting_date already "
                             "loaded downstream.")
    parser.add_argument('--skip-crawl', action='store_true',
                        help="do not download; process whatever is already in "
                             "original_data/ (useful for re-runs and tests)")
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    if not args.skip_crawl:
        crawl = ['web_crawler_for_proceeding_files.py']
        if args.since:
            crawl += ['--since', args.since]
        run('crawl', crawl)

    run('convert', ['convert2txt.py'])
    run('match', ['member_speech_matcher.py', '-f', DATA,
                  '-o', TELL_ALL, '-o2', TELL_ALL_CLEAN])
    run('fill chair names', ['fill_proedr_names.py', '-f', TELL_ALL_CLEAN,
                             '-o', TELL_ALL_FILLED])
    run('extract events', ['record_event_extractor.py', '-f', DATA, '-o', EVENTS])
    run('enrich events', ['enrich_event_speeches.py', '-e', EVENTS,
                          '-f', TELL_ALL_FILLED, '-o', EVENTS_ENRICHED])
    run('qc', ['event_stream_qc.py', '-f', EVENTS_ENRICHED, '-o', QC_CSV])

    # QC gate: read the report, surface suspects, choose the exit code. The
    # report is always written, so suspect sittings are still loadable; the
    # non-zero exit is the signal for the scheduler to alert.
    suspects = []
    with open(os.path.join(SRC_DIR, QC_CSV), encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['suspect']:
                suspects.append((row['source_file'], row['suspect']))

    print('\n=== summary ===', flush=True)
    if suspects:
        print(len(suspects), 'suspect sitting(s) - hold out of public aggregates, review:')
        for name, flags in suspects[:30]:
            print('  ', name, '->', flags)
        if len(suspects) > 30:
            print('  ...and', len(suspects) - 30, 'more, see', QC_CSV)
        raise SystemExit(2)
    print('no suspect sittings', flush=True)


if __name__ == '__main__':
    main()
