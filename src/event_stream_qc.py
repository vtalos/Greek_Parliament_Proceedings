# -*- coding: utf-8 -*-
import os
import json
import csv
from argparse import ArgumentParser

'''This script produces a quality control report for the event streams of
record_event_extractor.py: one row per sitting with the counts of each event
type, the stated times and a "suspect" column, so that silent parsing failures
stand out instead of passing as empty sittings. A sitting is marked suspect if
it has no speeches at all, suspiciously few speeches, no stage notes, or a
very high share of unclassified stage notes.

Example: python event_stream_qc.py -f '../events/' -o '../out_files/event_stream_qc.csv'
'''

parser = ArgumentParser()
parser.add_argument("-f", "--events_folder", help="folder with the jsonl event files")
parser.add_argument("-o", "--outfile", default='../out_files/event_stream_qc.csv',
                    help="path for the qc report csv")
args = parser.parse_args()

filenames = sorted(f for f in os.listdir(args.events_folder) if f.endswith('.jsonl'))

rows = []

for filename in filenames:

    counts = {'speech': 0, 'interjection': 0, 'stage_note': 0, 'other_note': 0,
              'header': 0, 'name_list': 0, 'chair_flags': 0}
    meta = {}

    with open(os.path.join(args.events_folder, filename), 'r', encoding='utf-8') as f:
        for line in f:
            event = json.loads(line)
            if event['type'] == 'sitting':
                meta = event
            elif event['type'] == 'speech':
                counts['speech'] += 1
                if event['interjection']:
                    counts['interjection'] += 1
                if event.get('chair_flags'):
                    counts['chair_flags'] += 1
            elif event['type'] == 'stage_note':
                counts['stage_note'] += 1
                if event['subtype'] == 'other':
                    counts['other_note'] += 1
            elif event['type'] == 'header':
                if event.get('subtype') == 'name_list':
                    counts['name_list'] += 1
                else:
                    counts['header'] += 1

    suspect = []
    if counts['speech'] == 0:
        suspect.append('no_speeches')
    elif counts['speech'] < 10:
        suspect.append('few_speeches')
    if counts['stage_note'] == 0:
        suspect.append('no_stage_notes')
    elif counts['other_note'] / counts['stage_note'] > 0.8:
        suspect.append('mostly_unclassified_notes')

    rows.append([meta.get('sitting_date', ''), meta.get('parliamentary_period', ''),
                 meta.get('parliamentary_session', ''), meta.get('parliamentary_sitting', ''),
                 filename, counts['speech'], counts['interjection'], counts['stage_note'],
                 counts['other_note'], counts['header'], counts['name_list'],
                 counts['chair_flags'], meta.get('start_time') or '', meta.get('end_time') or '',
                 ';'.join(suspect)])

with open(args.outfile, 'w', encoding='utf-8', newline='') as out:
    writer = csv.writer(out)
    writer.writerow(['sitting_date', 'parliamentary_period', 'parliamentary_session',
                     'parliamentary_sitting', 'source_file', 'speeches', 'interjections',
                     'stage_notes', 'unclassified_notes', 'headers', 'name_lists',
                     'chair_flags', 'start_time', 'end_time', 'suspect'])
    writer.writerows(rows)

suspects = [r for r in rows if r[-1]]
print('Sittings:', len(rows), '| suspect:', len(suspects))
for r in suspects[:30]:
    print(' ', r[4], '->', r[-1], '(speeches:', r[5], ', notes:', r[7], ')')
if len(suspects) > 30:
    print('  ...and', len(suspects) - 30, 'more, see', args.outfile)
