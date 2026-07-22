# -*- coding: utf-8 -*-
"""Reconstruct the unpublished wiki_data/*_cases_populated.json inputs of
gov_members_data_cleaner.py from the published members files.
Structure expected by the cleaner: {nominative: {"ενικος": {"γενικη": [forms]}}}
"""
import json
import os
import sys
import pandas as pd

repo = sys.argv[1] if len(sys.argv) > 1 else '..'

def male_first_genitives(name):
    if name.endswith('ος'):
        return [name[:-2]+'ου']
    if name.endswith('ης'):
        return [name[:-1]]
    if name.endswith('ας'):
        return [name[:-1]]
    if name.endswith('ων'):
        return [name[:-2]+'ωνα', name[:-2]+'ωνος', name[:-2]+'ονος', name]
    if name.endswith('ευς'):
        return [name[:-3]+'εως']
    return [name]  # indeclinable, e.g. μιχαηλ, δανιηλ, συμεων

def female_first_genitives(name):
    if name.endswith('α') or name.endswith('ω'):
        return [name+'ς']
    if name.endswith('η'):
        return [name+'ς']
    if name.endswith('ις'):
        return [name[:-1]+'δος']
    return [name]  # indeclinable, e.g. ελισαβετ

def male_surname_genitives(name):
    if name.endswith('ος'):
        return [name[:-2]+'ου']
    if name.endswith('ης'):
        return [name[:-1]]
    if name.endswith('ας'):
        return [name[:-1]]
    return []

male_names, female_names, male_surnames = {}, {}, {}

def add(d, name, gens):
    if not gens:
        return
    entry = d.setdefault(name, {'ενικος': {'γενικη': []}})
    for g in gens:
        if g not in entry['ενικος']['γενικη']:
            entry['ενικος']['γενικη'].append(g)

def add_person(first, surname, gender):
    for part in first.split('-'):
        part = part.strip('()')
        if len(part) < 3:
            continue
        if gender == 'male':
            add(male_names, part, male_first_genitives(part))
        elif gender == 'female':
            add(female_names, part, female_first_genitives(part))
    if gender == 'male' and surname:
        for part in surname.split('-'):
            if len(part) < 3:
                continue
            add(male_surnames, part, male_surname_genitives(part))

# first names of extra-parliamentary ministers, absent from the member files
add_person('δανιηλ', None, 'male')

# parliament members: "surname father firstname (nickname)"
df = pd.read_csv(os.path.join(repo, 'out_files/parl_members_activity_1989onwards_with_gender.csv'))
for _, row in df.iterrows():
    parts = str(row['member_name']).split(' ')
    if len(parts) < 3:
        continue
    add_person(parts[2], parts[0], row['gender'])
    # nickname in parenthesis, if present
    for p in parts[3:]:
        if p.startswith('('):
            add_person(p.strip('()'), None, row['gender'])

# government members: "firstname surname (nickname)"
df = pd.read_csv(os.path.join(repo, 'out_files/formatted_roles_gov_members_data.csv'))
for _, row in df.iterrows():
    parts = str(row['member_name']).split(' ')
    if len(parts) < 2:
        continue
    add_person(parts[0], parts[1], row['gender'])

outdir = os.path.join(repo, 'out_files/wiki_data')
os.makedirs(outdir, exist_ok=True)
for fname, d in [('male_name_cases_populated.json', male_names),
                 ('female_name_cases_populated.json', female_names),
                 ('male_surname_cases_populated.json', male_surnames)]:
    with open(os.path.join(outdir, fname), 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print(fname, len(d), 'entries')
