# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

'''This script produces the full 1989-2026 dataset in the exact schema of the
published 1989-2020 dataset. It takes the concatenated output of the batches
(already filled by fill_proedr_names.py), drops the speaker_info column, which
the published dataset does not include, and normalizes the period 18 label to
the published notation. The input is streamed in chunks to keep the memory
usage low.'''

total = 0

with open('../Greek_Parliament_Proceedings_1989_2026.csv', 'w+', encoding='utf-8', newline='') as outfile:

    header_written = False

    for df in pd.read_csv('../out_files/tell_all_final.csv', encoding='utf-8', chunksize=50000):

        # the website no longer mentions the revisionary parliament in the period name
        df['parliamentary_period'] = df['parliamentary_period'].replace(
            {'^period 18$': 'period 18 review 9'}, regex=True)

        del df['speaker_info']

        df.to_csv(outfile, index=False, header=not header_written, na_rep=np.nan)
        header_written = True
        total += df.shape[0]

print('Created file Greek_Parliament_Proceedings_1989_2026.csv with', total, 'speeches')
