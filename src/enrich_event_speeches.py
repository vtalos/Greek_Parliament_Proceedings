# -*- coding: utf-8 -*-
import os
import re
import json
import csv
import difflib
import pandas as pd
from collections import Counter
from argparse import ArgumentParser

'''This script writes the member matching of the existing pipeline onto the
event streams of record_event_extractor.py: every speech event whose text was
matched to a member by member_speech_matcher.py (after fill_proedr_names.py)
gets the member_name and speaker_info of the corresponding row. The speeches
are aligned per sitting on their text, ignoring whitespace (the two pipelines
treat newlines differently), with a sequence matcher so that repeated short
texts are aligned by their context and not to the first occurrence.

Speeches that the matcher dropped (unrecognised or non-member speakers) keep
only their speaker_raw; they are counted per speaker in a report file, so that
missing name alternatives become visible instead of disappearing silently.

Example: python enrich_event_speeches.py -e '../events/' -f '../out_files/tell_all_FILLED.csv' -o '../events_enriched/'
'''

parser = ArgumentParser()
parser.add_argument("-e", "--events_folder", help="folder with the jsonl event files")
parser.add_argument("-f", "--infile", default='../out_files/tell_all_FILLED.csv',
                    help="the output of fill_proedr_names.py")
parser.add_argument("-o", "--outfolder", default='../events_enriched/',
                    help="folder for the enriched jsonl event files")
args = parser.parse_args()

if not os.path.exists(args.outfolder):
    os.makedirs(args.outfolder)


def norm_all(text):
    return re.sub(r'\s+', '', str(text))


def sitting_key(date_ddmmyyyy, session, sitting):
    return (date_ddmmyyyy, session.strip(), sitting.strip())


def label_from_filename_part(part):
    # same cleanup as the matcher: parentheses and dashes become spaces
    return re.sub(r'\s\s+', ' ', re.sub(r'[()-]', ' ', part)).strip()


# index the event files by (date, session, sitting), as the matcher labels them
event_files = {}
for filename in os.listdir(args.events_folder):
    if not filename.endswith('.jsonl'):
        continue
    parts = os.path.splitext(filename)[0].split('_')
    date = parts[0]
    date_ddmmyyyy = date[8:10] + '/' + date[5:7] + '/' + date[0:4]
    key = sitting_key(date_ddmmyyyy, label_from_filename_part(parts[3]),
                      label_from_filename_part(parts[4]))
    event_files[key] = filename

unmatched = Counter()
enriched_sittings = 0
total_speeches = 0
enriched_speeches = 0


def process_sitting(key, rows):
    global enriched_sittings, total_speeches, enriched_speeches

    if key not in event_files:
        print('No event file for sitting', key)
        return

    filename = event_files.pop(key)
    events = [json.loads(line) for line in
              open(os.path.join(args.events_folder, filename), 'r', encoding='utf-8')]

    speeches = [e for e in events if e.get('type') == 'speech']
    ev_texts = [norm_all(e['text']) for e in speeches]
    row_texts = [norm_all(r['speech']) for r in rows]

    blocks = difflib.SequenceMatcher(None, ev_texts, row_texts,
                                     autojunk=False).get_matching_blocks()
    for block in blocks:
        for k in range(block.size):
            row = rows[block.b + k]
            if str(row['member_name']) != 'nan':
                speeches[block.a + k]['member_name'] = row['member_name']
            if str(row['speaker_info']) != 'nan':
                speeches[block.a + k]['speaker_info'] = row['speaker_info']

    total_speeches += len(speeches)
    for e in speeches:
        if 'member_name' in e:
            enriched_speeches += 1
        elif 'speaker_info' not in e: # collective speakers are known, not missing
            unmatched[e['speaker_raw']] += 1

    with open(os.path.join(args.outfolder, filename), 'w', encoding='utf-8') as out:
        for e in events:
            out.write(json.dumps(e, ensure_ascii=False) + '\n')
    enriched_sittings += 1


# the matcher output lists the speeches of each sitting contiguously,
# so the file can be streamed and processed one sitting at a time
current_key = None
current_rows = []
for chunk in pd.read_csv(args.infile, encoding='utf-8', chunksize=50000):
    for row in chunk.to_dict('records'):
        key = sitting_key(str(row['sitting_date']),
                          str(row['parliamentary_session']),
                          str(row['parliamentary_sitting']))
        if key != current_key:
            if current_key is not None:
                process_sitting(current_key, current_rows)
            current_key = key
            current_rows = []
        current_rows.append(row)
if current_key is not None:
    process_sitting(current_key, current_rows)

# event files with no matcher rows at all are copied as they are
for key, filename in event_files.items():
    print('No matcher rows for', filename)
    with open(os.path.join(args.events_folder, filename), 'r', encoding='utf-8') as f:
        events = f.read()
    with open(os.path.join(args.outfolder, filename), 'w', encoding='utf-8') as out:
        out.write(events)

with open('../out_files/unmatched_event_speakers.csv', 'w', encoding='utf-8', newline='') as out:
    writer = csv.writer(out)
    writer.writerow(['speaker_raw', 'speeches'])
    writer.writerows(unmatched.most_common())

print('Sittings enriched:', enriched_sittings)
print('Speeches with member_name:', enriched_speeches, 'from', total_speeches,
      '(', round(100 * enriched_speeches / total_speeches, 1), '% )')
print('Distinct unmatched speakers:', len(unmatched),
      '- see ../out_files/unmatched_event_speakers.csv')
