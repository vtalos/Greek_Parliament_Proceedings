import pandas as pd
import re
import numpy as np
from datetime import timedelta


def remove_father_name(name):
    name_parts = name.split(' ')
    new_name = name_parts[0]+' ' + ' '.join(name_parts[2:])
    return new_name


def parl_name_formatting(df):

    d = {r'\bαντωνης\b': 'αντωνιος',
         r'\bαχιλλευς\b': 'αχιλλεας',
         r'\bγιωργος\b': 'γεωργιος',
         r'\bγιαννης\b': 'ιωαννης',
         }
    # regex = False exact full string match,
    # regex = True substrings replaced unless use \bstring\b in first parenthesis.
    # regex only in first parenthesis
    df['member_name_copy'] = df['member_name'].copy().replace(d, regex=True)

    return df


def gov_name_formatting(df):

    d = {r'\bβυρωνας\b': 'βυρων',
         r'\bεμμανουηλ λουκακης\b': 'μανωλης λουκακης',
         r'\bκιμωνας κουλουρης\b': 'κιμων κουλουρης',
         r'\bκωνσταντινος σημιτης\b': 'κωστας σημιτης',
         r'\bμιχαηλ παπαδοπουλος\b': 'μιχαλης παπαδοπουλος',
         r'\bμιχαηλ παπακωνσταντινου\b': 'μιχαλης παπακωνσταντινου',
         r'\bμιχαηλ-γεωργιος λιαπης\b': 'μιχαλης γεωργιος λιαπης',
         r'\bνικολαος χριστοδουλακης\b': 'νικος χριστοδουλακης'
         }
    # regex = False exact full string match,
    # regex = True substrings replaced unless use \bstring\b in first parenthesis.
    # regex only in first parenthesis
    df['member_name'] = df['member_name'].replace(d, regex=True)

    return df


def assert_filled_gender(df):

    if df['gender'].isnull().values.any()==True:
        print('Warning: some gender values ar NaN for the following member names...')
        print(df['member_name'][df['gender'].isnull()])
    else:
        print('All names have assigned gender.')

    return


def add_government_column(df, df_governments):

    # Convert to datetime type for best date comparisons
    df['government_name'] = [[] for _ in range(df.shape[0])]
    df['member_start_date'] = pd.to_datetime(df['member_start_date'])
    df['member_end_date'] = pd.to_datetime(df['member_end_date'])
    df_governments['date_from'] = pd.to_datetime(df_governments['date_from'])#.dt.date
    df_governments['date_to'] = pd.to_datetime(df_governments['date_to'])#.dt.date
    df_governments = df_governments.sort_values(by='date_from', ascending=True)

    # Drop rows before first government
    mask = (df['member_end_date'] >= df_governments.at[0,'date_from']) #1989-07-03
    df = df.loc[mask]

    for index1, row1 in df.iterrows():
        matched_to_government = False
        for index2, row2 in df_governments.iterrows():
            try:
                if (row1.member_start_date>=row2.date_from and
                    row1.member_start_date<row2.date_to #< and not <= because last gov date is given to next gov
                    ) or (
                    row1.member_end_date>=row2.date_from and
                    row1.member_end_date<row2.date_to #< and not <= because last gov date is given to next gov
                    ) or (
                    row1.member_start_date<=row2.date_from and
                    row1.member_end_date>=row2.date_to):

                    item = row2['gov_name']+'('+str(row2.date_from.strftime('%d/%m/%Y'))+'-'+\
                           str(row2.date_to.strftime('%d/%m/%Y'))+')'
                    df.at[index1,'government_name'].append(item)
                    matched_to_government = True
            except TypeError:
                print('PROBLEM: cannot compare government dates and member dates')
                print(row1.member_start_date, type(row1.member_start_date))
                print(row2.date_from, type(row2.date_from))

        if matched_to_government == False:
            print('PROBLEM: not matched to existing government')
            print(row1)

    return df


# FILE 1: elected parliament members from hellenicparliament.gr
df_parl = pd.read_csv('../out_files/parl_members_activity_1989onwards_with_gender.csv', encoding='utf-8')
df_parl = parl_name_formatting(df_parl) # add name copy column and proceed to adjustments
# Remove father name because not all input files have it
df_parl['member_name_copy'] = df_parl['member_name_copy'].apply(remove_father_name)
df_parl['roles'] = [[] for _ in range(df_parl.shape[0])]

# FILE 2: assigned government members with roles from gslegal.gov.gr
df_gov = pd.read_csv('../out_files/formatted_roles_gov_members_data.csv', encoding='utf-8')
df_gov = gov_name_formatting(df_gov)

# FILE 3: manually extracted additional parliament roles
df_extra = pd.read_csv('../out_files/extra_roles_manually_collected.csv', encoding='utf-8')
# Remove father name because not all input files have it
df_extra['member_name'] = df_extra['member_name'].apply(remove_father_name)

# Concatenate members with roles
df_roles = pd.concat([df_gov, df_extra])

members_to_match = list(set(df_roles['member_name'].to_list())) # unique member names

# Match members from df_roles to df_parl BY NAME AND DATES and find extra parliamentary members
df_roles['role_start_date'] = pd.to_datetime(df_roles['role_start_date'], format='%d/%m/%Y').dt.date
df_roles['role_end_date'] = pd.to_datetime(df_roles['role_end_date'], format='%d/%m/%Y').dt.date
df_parl['member_start_date'] = pd.to_datetime(df_parl['member_start_date']).dt.date
df_parl['member_end_date'] = pd.to_datetime(df_parl['member_end_date']).dt.date

extra_parliamentary = []

# Normalize the parliament member names once, they do not change while matching
parl_match_data = []
for index_parl, row_parl in df_parl.iterrows():
    parl_name = row_parl['member_name_copy']
    parl_name = re.sub(r'[-()]', ' ', parl_name)
    parl_name = re.sub(r'\s\s+', ' ', parl_name)
    parl_parts = [i for i in parl_name.split(' ') if i != '']
    parl_match_data.append((index_parl, parl_parts,
                            row_parl['member_start_date'], row_parl['member_end_date']))

c = 0

# Match the member names from df_roles to df_parl, in order to transfer their roles
for index_gov, row_gov in df_roles.iterrows():

    c += 1
    if c % 100 == 0:
        print(c)

    covering_terms = [] # parliamentary terms of the member that cover the role
    gov_name = row_gov['member_name']
    gov_name = re.sub(r'[-()]', ' ', gov_name)
    gov_name = re.sub(r'\s\s+', ' ', gov_name)
    gov_parts = [i for i in gov_name.split(' ') if i != '']

    # if we find a match, we don't break. continue iteration because it might
    # match to more than one periods as formed in the gov files
    for index_parl, parl_parts, m_s, m_e in parl_match_data:

        # Check if gov_parts are all in parl_parts
        # meaning that full names match, regardless of word order
        check = all(item in parl_parts for item in gov_parts)

        # if names matched
        if check:
            r_s = row_gov['role_start_date']
            r_e = row_gov['role_end_date']

            # if any date of active role is in the member activity range
            # if role start in member activity, or role end in member activity
            # or activity in role of large range
            if (r_s>=m_s and r_s<=m_e) or (r_e>=m_s and r_e<=m_e) or (r_s<=m_s and r_e>=m_e):
                covering_terms.append((m_s, m_e))
                item = row_gov['role']+'('+str(row_gov['role_start_date'].strftime('%d/%m/%Y')
                                               )+'-'+str(row_gov['role_end_date'].strftime('%d/%m/%Y'))+')'
                df_parl.at[index_parl, 'roles'].append(item)

    ''' The parts of the role that no parliamentary term of the member covers
        correspond to extra parliamentary service (e.g. a minister assigned
        before or between his terms), so they get their own activity rows.
        A role of a member with no term at all is fully extra parliamentary. '''
    role_item = row_gov['role']+'('+str(row_gov['role_start_date'].strftime('%d/%m/%Y')
                                           )+'-'+str(row_gov['role_end_date'].strftime('%d/%m/%Y'))+')'

    gap_start = row_gov['role_start_date']
    for m_s, m_e in sorted(covering_terms):
        if m_s > gap_start:
            extra_parliamentary.append([row_gov['member_name'], gap_start,
                                        m_s - timedelta(days=1),
                                        'εξωκοινοβουλευτικός', np.nan,
                                        row_gov['gender'], [role_item]])
        gap_start = max(gap_start, m_e + timedelta(days=1))
    if gap_start <= row_gov['role_end_date']:
        extra_parliamentary.append([row_gov['member_name'], gap_start,
                                    row_gov['role_end_date'],
                                    'εξωκοινοβουλευτικός', np.nan,
                                    row_gov['gender'], [role_item]])

del df_parl['member_name_copy']

df_parl = pd.concat([df_parl, pd.DataFrame(data=extra_parliamentary,
                                           columns=df_parl.columns)], ignore_index=True)

df_governments = pd.read_csv('../out_files/governments_1989onwards.csv', encoding='utf-8')
df_parl = add_government_column(df_parl, df_governments)

assert_filled_gender(df_parl)

df_parl.to_csv('../out_files/all_members_activity.csv', encoding='utf-8', index=False)
print('Created file all_members_activity.csv with columns ', df_parl.columns)
