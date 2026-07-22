# Greek Parliament Proceedings, 1989–2026

A complete, verifiable dataset of the plenary proceedings of the Hellenic Parliament:
**1,533,886 speeches from 6,443 sittings**, spanning every sitting from the 1st one of
July 3rd, 1989 up to today — plus a new **event-stream layer** that captures what
datasets of parliamentary speech usually throw away: applause (with the wing that
applauded), protests, laughter, chair interventions, agenda headers and sitting times.

This repository is a modernized fork of the
[iMEdD-Lab pipeline](https://github.com/iMEdD-Lab/Greek_Parliament_Proceedings) that
produced the published [1989–2020 dataset](https://zenodo.org/record/4311577)
(1,280,918 speeches). The fork brings the pipeline back to life on the current
parliament website, fixes a number of bugs found along the way (several of which
affect the published dataset — all documented), rebuilds the never-published input
files, and re-runs everything from scratch. The output was validated per year and per
sitting against the published dataset before extending beyond it: of its 5,224
sittings, 5,220 are reproduced here, several previously lost sittings and speakers
are recovered, and every divergence is explained in [NOTES.md](NOTES.md).

## The main dataset

`Greek_Parliament_Proceedings_1989_2026.csv` (3.0 GB, UTF-8 — not tracked in git; a
`_DataSample.csv` is provided instead). Exact same schema as the published dataset:

| column | description |
|---|---|
| member_name | official name of the member who spoke |
| sitting_date | date of the sitting |
| parliamentary_period | period name/number (a period includes multiple sessions) |
| parliamentary_session | session name/number (a session includes multiple sittings) |
| parliamentary_sitting | sitting name/number |
| political_party | party of the speaker **at the moment of the speech** |
| government | government in force at the moment of the speech |
| member_region | electoral district of the speaker |
| roles | parliamentary/government roles of the speaker at the moment of the speech |
| member_gender | gender of the speaker |
| speech | the speech text |

## The event streams

For every sitting, `events/` (and `events_enriched/`, with member matching applied)
holds one JSON-lines file: the first line carries the sitting metadata (including
start/end time where the record states them) and every following line is one event,
in record order, with a sequence number:

- `speech` — speaker (raw + matched member), chair flag, interjection flag (≤6 words),
  chair-action flags (calls to order, requests to withdraw, strike-from-record)
- `stage_note` — the stenographers' parentheticals with full text, classified
  (applause/protest/noise/laughter/time-bell/voting/inaudible/…) and anchored to the
  exact position inside the speech where they occurred
- `header` — agenda/section headings; roll-call name catalogues are collapsed into
  single `name_list` events

Across the corpus: ~1.63M speech events (90.7% matched to a member), ~360k stage
notes — including ~150k applause events with wing attribution — making this, to our
knowledge, the richest resource of parliamentary reactions available for Greek.

## Provenance and quality control

- `out_files/download_manifest.csv`: URL, download timestamp and sha256 for every
  record file; the original files are archived locally.
- `out_files/event_stream_qc.csv` (regenerated per run): one row per sitting with
  event counts and a `suspect` flag, so parsing failures scream instead of passing
  as silently empty.
- `out_files/unmatched_event_speakers.csv` (regenerated per run): every unmatched
  speaker with its speech count — nothing is dropped silently; unmatched speeches
  keep their raw speaker name in the event stream.
- [NOTES.md](NOTES.md): every code change, every upstream bug found (with evidence),
  every source gap (missing 1995, broken-font PDFs of 1996–2003, mis-dated events of
  the current period on the parliament site) and every manual correction.

## Pipeline

Record collection and conversion:

1. `web_crawler_for_proceeding_files.py` — download all record files from the
   [plenary sittings listing](https://www.hellenicparliament.gr/Praktika/Synedriaseis-Olomeleias)
   into `original_data/`, resumable, with atomic writes and the provenance manifest.
2. `convert2txt.py` — convert doc/docx/pdf/txt records to normalized UTF-8 text in
   `_data/` (tika-app-1.20.jar, the same converter as the published dataset), with
   per-file metadata encoded in the filename.

Member registries:

3. `web_crawler_for_parliament_members.py` → `parl_members_data_cleaner.py` →
   `add_gender_to_members.py` — elected members and their activity, cleaned, with gender.
4. `greek_name_cases_wiki_crawler.py` → `reconstruct_wiki_name_cases.py` →
   `web_crawler_for_government_members.py` → `gov_members_data_cleaner.py` —
   governments and government members (gslegal.gov.gr), with genitive→nominative
   name conversion.
5. `join_members_activity.py` — join everything (plus manually collected extra roles)
   into `all_members_activity.csv`, creating extra-parliamentary entries for the
   periods a minister served without being an MP.

Speech extraction and outputs:

6. `member_speech_matcher.py` — split records into speeches and match speakers to
   members via string similarity plus the curated name-variant lists
   (`greek_names_alts_only.txt`). Run per batch (`_batches/`) for memory economy.
7. `fill_proedr_names.py` — fill in unnamed chair speeches per sitting.
8. `csv_concat.py` → `make_full_dataset.py` — concatenate the batches and produce the
   final CSV. (`make_extension_dataset.py` produces the 2020+ extension only.)
9. `record_event_extractor.py` → `enrich_event_speeches.py` → `event_stream_qc.py` —
   produce the event streams, write the member matching onto them, and generate the
   per-sitting quality report.

Every step is idempotent and resumable: interrupted runs continue from where they
stopped, and a daily incremental run only fetches and processes what is new.

## Requirements

- Python 3.9+, libraries from `requirements.txt`
- Java runtime and `tika-app-1.20.jar` (in `src/`) for `convert2txt.py`

## Lineage and credits

The original dataset and pipeline were produced on behalf of
[iMEdD](https://www.imedd.org/) by [Konstantina Dritsa](https://github.com/Dritsa-Konstantina)
with the contribution of [Kelly Kiki](https://github.com/kellykiki)
([iMEdD Lab](https://lab.imedd.org/)), building on the Master thesis
"[Speech quality and sentiment analysis on the Hellenic Parliament proceedings](http://www.pyxida.aueb.gr/index.php?op=view_object&object_id=6387)"
(AUEB, 2018, supervised by Prof. Panagiotis Louridas). Their methodology is described
in the iMEdD Lab article
"[The creation of a dataset with the parliament proceedings within 31 years](https://devlab.imedd.org/i-dimiourgia-tou-dataset-me-ta-koinovouleftika-praktika/)",
and the published dataset lives on [Zenodo](https://zenodo.org/record/4311577). This
fork would not exist without their work.
