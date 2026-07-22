# -*- coding: utf-8 -*-
import os
import re
import json
from argparse import ArgumentParser
from common import speaker_regex, proedr_regex

'''This script converts each record file into a stream of events: one json
line per event, in the order they appear in the record. Event types:

- sitting:    one first line per record, with the sitting metadata, the source
              filename and the starting/ending time of the sitting when stated
- header:     an agenda/section heading of the record (e.g. ΕΠΙΚΑΙΡΕΣ ΕΡΩΤΗΣΕΙΣ)
- speech:     what a speaker said, with the parenthetical notes removed;
              the speaker matching to official members happens downstream
- stage_note: a parenthetical note of the stenographers, with its full text
              (e.g. which wing applauded or protested), classified by keywords,
              anchored to the speech it occurred in and its position in it

The speeches are segmented with the same speaker regular expression as
member_speech_matcher.py, so that the speech view of the stream stays
equivalent to the output of the existing pipeline.

Example: python record_event_extractor.py -f '../_data/' -o '../events/'
'''

parser = ArgumentParser()
parser.add_argument("-f", "--data_folder", help="folder with the converted record files")
parser.add_argument("-o", "--outfolder", help="folder for the jsonl event files")
args = parser.parse_args()

if not os.path.exists(args.outfolder):
    os.makedirs(args.outfolder)

# speaker detection and proedros detection come from common.py,
# so that this stays the same as member_speech_matcher.py

parenthetical_regex = re.compile(r"\((.{2,600}?)\)", re.DOTALL)
time_start_regex = re.compile(r"ώρα\s+(\d{1,2}[\.:]\d{2})")
time_end_regex = re.compile(r"ώρα\s+(\d{1,2}[\.:]\d{2})΄?\s*[^\d]{0,40}?(λ[υύ]εται|διακόπτεται)")
# newer records state the times explicitly
explicit_start_regex = re.compile(r"Ώρα έναρξης[:\s]+(\d{1,2}[\.:]\d{2})")
explicit_end_regex = re.compile(r"Ώρα λήξης[:\s]+(\d{1,2}[\.:]\d{2})")

# a header is a line in capitals, without the colon that speaker lines have
header_line_regex = re.compile(r"^[Α-ΩΆ-ΏΪΫ0-9\s«»\"'΄`’\-–.,()]{4,120}$")

stage_note_subtypes = [
    ('applause', r'χειροκροτ'),
    ('protest', r'διαμαρτυρ'),
    ('noise', r'θόρυβ|θορυβ'),
    ('laughter', r'γέλωτ|γελ[ωώ]τ'),
    ('time_bell', r'κουδούνι|κωδωνοκρουσ'),
    ('inaudible', r'δεν ακού|δεν ακουσ'), # remote speakers during the pandemic
    ('voting', r'καταμ[εέ]τρηση|ψηφοφορ[ιί]α'),
    ('tabling', r'καταθέτει|κατατίθενται|κατέθεσε'),
    ('record_insertion', r'να καταχωριστ|καταχωρίζεται στα [Ππ]ρακτικά'),
    ('deletion', r'διεγράφη|διαγράφηκε|δεν γράφ|να μη[ν]? γραφ'),
    # the capitals of "ΔΙΑΚΟΠΗ" lose their accents when lowercased
    ('procedure', r'στο σημείο αυτό|αποχωρ|προσέρχ|προσήλθ|εισέρχ|αναλαμβάνει την [Ππ]ροεδρία|λύεται η συνεδρίαση|διακόπτεται|διακοπ[ηή]|δ ι α κ ο π η'),
    ('pagination_artifact', r'αλλαγη σελιδας'), # tika conversion artifact
]

chair_flag_regexes = [
    ('call_to_order', r'ανακαλ(έσ|ειτ|εστ)|στην τάξη'),
    ('withdraw_request', r'αποσύρετε|να αποσύρ|ανακαλέστε'),
    ('strike_from_record', r'να μη[ν]? (γραφ|καταγραφ)|διαγραφ(εί|ούν)'),
]


def classify_note(text):
    low = text.lower()
    for subtype, pattern in stage_note_subtypes:
        if re.search(pattern, low):
            return subtype
    return 'other'


def normalize(text):
    return re.sub(r'\s\s+', ' ', text).strip()


filenames = sorted(f for f in os.listdir(args.data_folder) if not f.startswith('.'))

for counter, filename in enumerate(filenames, 1):

    print('File', counter, 'from', len(filenames), filename)

    name_parts = os.path.splitext(filename)[0].split('_')
    try:
        raw = open(os.path.join(args.data_folder, filename), 'r', encoding='utf-8').read()
    except UnicodeDecodeError:
        # a record that is not valid utf-8 is logged instead of killing the run
        print('WARNING: invalid encoding, skipping', filename)
        continue

    # find the header lines on the line structure of the record;
    # consecutive header lines are merged, since titles often span lines
    headers = []
    offset = 0
    previous_was_header = False
    for line in raw.split('\n'):
        stripped = line.strip()
        if (4 <= len(stripped) <= 120 and not stripped.endswith(':')
                and not re.search(r'[α-ωά-ώ]', stripped)
                and re.search(r'[Α-ΩΆ-Ώ]', stripped)
                and header_line_regex.match(stripped)
                and 'ΑΛΛΑΓΗ ΣΕΛΙΔΑΣ' not in stripped): #pagination artifact
            if previous_was_header:
                headers[-1] = (headers[-1][0], headers[-1][1] + ' ' + stripped)
            else:
                headers.append((offset + line.find(stripped[0]), stripped))
            previous_was_header = True
        elif stripped != '':
            previous_was_header = False
        offset += len(line) + 1

    # newlines become spaces so that all offsets stay unchanged
    flat = raw.replace('\n', ' ')

    speaker_matches = list(speaker_regex.finditer(flat))

    events = []

    sitting_meta = {
        'type': 'sitting',
        'sitting_date': name_parts[0],
        'parliamentary_period': name_parts[2],
        'parliamentary_session': name_parts[3],
        'parliamentary_sitting': name_parts[4],
        'source_file': filename,
        'start_time': None,
        'end_time': None,
    }

    m = explicit_start_regex.search(flat)
    if not m:
        intro = flat[:speaker_matches[0].start()] if speaker_matches else flat
        m = time_start_regex.search(intro[-3000:] if len(intro) > 3000 else intro)
    if m:
        sitting_meta['start_time'] = m.group(1)

    m = explicit_end_regex.search(flat)
    if m:
        sitting_meta['end_time'] = m.group(1)
    else:
        for m in time_end_regex.finditer(flat):
            sitting_meta['end_time'] = m.group(1)

    # discard the table of contents of the record, like the existing pipeline;
    # only the headers that appear after the first speaker are kept
    if speaker_matches:
        headers = [h for h in headers if h[0] > speaker_matches[0].start()]

    ''' The name catalogues of roll call votes appear as long runs of adjacent
        capital lines (name, region, vote). Each run is collapsed to a single
        name_list event; the votes themselves are not parsed here.'''
    collapsed = []
    run = []
    for pos, text in headers + [(None, None)]:
        if run and pos is not None and pos - run[-1][0] < len(run[-1][1]) + 60:
            run.append((pos, text))
        else:
            if len(run) > 20:
                collapsed.append((run[0][0], ' · '.join(t for _, t in run), 'name_list'))
            else:
                collapsed.extend((p, t, None) for p, t in run)
            run = [(pos, text)] if pos is not None else []
    headers = collapsed

    header_index = 0

    for i, sm in enumerate(speaker_matches):

        # headers that appear before this speech
        while header_index < len(headers) and headers[header_index][0] < sm.start():
            pos, text, subtype = headers[header_index]
            event = {'type': 'header', 'text': text, 'offset': pos}
            if subtype:
                event['subtype'] = subtype
            events.append(event)
            header_index += 1

        speech_start = sm.end()
        speech_end = speaker_matches[i+1].start() if i+1 < len(speaker_matches) else len(flat)
        speech_raw = flat[speech_start:speech_end]
        speaker_raw = normalize(sm.group(0).rstrip(':').strip())
        # pagination artifacts of the conversion, glued before the speaker name
        speaker_raw = re.sub(r"^(ΑΛΛΑΓΗ ΣΕΛΙΔΑΣ( ΛΟΓΩ ΑΛΛΑΓΗΣ ΘΕΜΑΤΟΣ)?\s*(\(ΜΕΤΑ ΤΗ ΔΙΑΚΟΠΗ\))?\s*)+", "", speaker_raw)

        notes = []
        for pm in parenthetical_regex.finditer(speech_raw):
            notes.append({'type': 'stage_note',
                          'subtype': classify_note(pm.group(1)),
                          'text': normalize(pm.group(1)),
                          'offset_in_speech': pm.start()})

        speech_text = normalize(parenthetical_regex.sub(' ', speech_raw))

        speech_event = {'type': 'speech',
                        'speaker_raw': speaker_raw,
                        'chair': bool(proedr_regex.search(speaker_raw)),
                        'interjection': len(speech_text.split()) <= 6,
                        'text': speech_text,
                        'offset': sm.start()}

        if speech_event['chair']:
            flags = [flag for flag, pattern in chair_flag_regexes
                     if re.search(pattern, speech_text.lower())]
            if flags:
                speech_event['chair_flags'] = flags

        events.append(speech_event)
        events.extend(notes)

    # any headers after the last speech
    for pos, text, subtype in headers[header_index:]:
        event = {'type': 'header', 'text': text, 'offset': pos}
        if subtype:
            event['subtype'] = subtype
        events.append(event)

    outpath = os.path.join(args.outfolder, os.path.splitext(filename)[0] + '.jsonl')
    with open(outpath, 'w', encoding='utf-8') as out:
        out.write(json.dumps(sitting_meta, ensure_ascii=False) + '\n')
        seq = 0
        parent_seq = None
        for event in events:
            seq += 1
            event['seq'] = seq
            if event['type'] == 'speech':
                parent_seq = seq
            if event['type'] == 'stage_note':
                event['parent_seq'] = parent_seq
            out.write(json.dumps(event, ensure_ascii=False) + '\n')
