# -*- coding: utf-8 -*-
import pandas as pd
import os

'''This script concatenates the outputs of member_speech_matcher.py in case
the latter ran in parallel on multiple different batches of the record files.
The batches are streamed in chunks, so that the full dataset is never loaded
in memory at once.'''
batches_dir = '../tell_all_batches/'

with open('../out_files/tell_all_final.csv', 'w+', encoding='utf-8', newline = '') as outfile:

    header_written = False

    for filepath in sorted([os.path.join(os.path.abspath(batches_dir), name)
                            for name in os.listdir(batches_dir)
                            if not name.startswith('.')]):
        print(filepath)
        for chunk in pd.read_csv(filepath, encoding='utf-8', chunksize=50000):
            chunk.to_csv(outfile, index=False, header=not header_written)
            header_written = True
