# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

'''This script produces the final extension of the published 1989-2020 dataset,
in the exact same schema. It takes the output of fill_proedr_names.py, keeps the
sittings that follow the last sitting of the published dataset (24/07/2020) and
drops the speaker_info column, which the published dataset does not include.
The input is streamed in chunks to keep the memory usage low.'''

last_published_sitting_date = '2020-07-24'

total = 0

with open('../Greek_Parliament_Proceedings_2020_2026.csv', 'w+', encoding='utf-8', newline='') as outfile:

    header_written = False

    for df in pd.read_csv('../out_files/tell_all_FILLED.csv', encoding='utf-8', chunksize=50000):

        df = df[pd.to_datetime(df['sitting_date'], format='%d/%m/%Y') > last_published_sitting_date]

        # the website no longer mentions the revisionary parliament in the period name
        df['parliamentary_period'] = df['parliamentary_period'].replace(
            {r'^period 18$': 'period 18 review 9'}, regex=True)

        del df['speaker_info']

        df.to_csv(outfile, index=False, header=not header_written, na_rep=np.nan)
        header_written = True
        total += df.shape[0]

print('Created file Greek_Parliament_Proceedings_2020_2026.csv with', total, 'speeches')
