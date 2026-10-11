# -*- coding: utf-8 -*-
import re
import unicodedata

'''Which party (wing of the chamber) a stenographers' note refers to.

The reaction notes name the wing in many spellings, e.g.
    (Χειροκροτήματα από την πτέρυγα του ΠΑ.ΣΟ.Κ.)
    (Όρθιοι οι Βουλευτές της Νέας Δημοκρατίας χειροκροτούν ζωηρά και παρατεταμένα)
    (Χειροκροτήματα από τις πτέρυγες του ΣΥΡΙΖΑ και των ΑΝΕΛ)
    (Χειροκροτήματα απ' όλες τις πτέρυγες της Βουλής)
note_wings() returns a list of party keys, plus two special keys: 'all' (all
wings of the chamber), 'government' (government benches) and 'opposition'.

The same keys are given to the party names of the member registry
(all_members_activity.csv) by party_key(), so that the wing of a note can be
compared with the party of the speaker. A key stands for a party across its
renamings (e.g. ΠΑΣΟΚ, Δημοκρατική Συμπαράταξη, Κίνημα Αλλαγής are all 'pasok').
'''


def normalize(text):
    # lowercase without accents, final sigma as sigma, no dots (ΠΑ.ΣΟ.Κ. -> πασοκ)
    text = unicodedata.normalize('NFD', text.lower())
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace('ς', 'σ').replace('.', '')
    text = re.sub(r"[-–—/]", ' - ', text)
    return re.sub(r'\s+', ' ', text).strip()


# Order matters: longer names first, and every match blanks its span, so that
# e.g. "Δημοκρατικής Συμπαράταξης ΠΑΣΟΚ - ΔΗΜΑΡ" is only 'pasok' and
# "Συνασπισμού Ριζοσπαστικής Αριστεράς" is not also 'syn'.
WING_ALIASES = [
    ('all', r'(ολεσ|ολη) (τισ|τησ|την) (πτερυγ|πλευρ|αιθουσ)\w*|ολων των πτερυγων|ολοι οι βουλευτεσ'),
    ('government', r'κυβερνητικ\w* (πτερυγ|πλευρ|εδραν)\w*|(υπουργικ|κυβερνητικ)\w* εδραν\w*|συμπολιτευσ\w*'),
    ('opposition', r'αντιπολιτευσ\w*'),
    ('pasok', r'δημοκρατικ\w* συμπαραταξ\w*( πασοκ)?( - δημαρ)?'),
    ('pasok', r'πασοκ( - κινημ\w* αλλαγησ)?|πα ?σο ?κ|πανελληνι\w* σοσιαλιστικ\w* κινημ\w*|κινημ\w* αλλαγησ|κιναλ'),
    ('syriza', r'συνασπισμ\w* ριζοσπαστικ\w* αριστερ\w*|συριζα'),
    ('syn', r'συνασπισμ\w* τησ αριστερ\w*|συνασπισμ\w*|συν'),
    ('ana', r'ανεξαρτητ\w* δημοκρατικ\w* βουλευτ\w*'),
    ('nd', r'(νε\w*|ν) δημοκρατι\w*|νδ'),
    ('kke', r'κομμουνιστικ\w* κομμ\w*|κκε'),
    ('anel', r'ανεξαρτητ\w* ελλην\w*|ανελ'),
    ('dimar', r'δημοκρατικ\w* αριστερ\w*|δημαρ'),
    ('na', r'νε\w* αριστερ\w*'),
    ('laos', r'λαικ\w* ορθοδοξ\w* συναγερμ\w*|λαοσ'),
    ('xa', r'χρυσ\w* αυγ\w*|λαικ\w* συνδεσμ\w*'),
    ('lae', r'λαικ\w* ενοτητ\w*'),
    ('el', r'ελληνικ\w* λυσ\w*'),
    ('potami', r'ποταμ\w*'),
    ('ek', r'ενωσ\w* κεντρω\w*'),
    ('mera25', r'μερα ?25|μετωπ\w* ευρωπαικ\w* ρεαλιστικ\w* ανυπακο\w*'),
    ('plefsi', r'πλευσ\w* ελευθερι\w*'),
    ('niki', r'νικη\w*|δημοκρατικ\w* πατριωτικ\w* κινημ\w*'),
    ('spartiates', r'σπαρτιατ\w*'),
    ('pola', r'πολιτικ\w* ανοιξ\w*|πολα'),
    ('dikki', r'δημοκρατικ\w* κοινωνικ\w* κινημ\w*|δηκκι'),
    ('dimana', r'δημοκρατικ\w* ανανεωσ\w*|δηανα'),
    ('oikologoi', r'οικολογ\w* εναλλακτικ\w*'),
]
# every alias must start at a word boundary ("νε... δημοκρατι..." inside "ανεξαρτητοι δημοκρατικοι")
WING_ALIASES = [(key, re.compile(r'\b(' + pattern + r')\b')) for key, pattern in WING_ALIASES]


def note_wings(text):
    '''The party keys named in a note, in order of appearance, without repeats.'''
    text = normalize(text)
    found = []
    for key, pattern in WING_ALIASES:
        for m in pattern.finditer(text):
            found.append((m.start(), key))
        text = pattern.sub(lambda m: ' ' * len(m.group(0)), text)
    keys = []
    for _, key in sorted(found):
        if key not in keys:
            keys.append(key)
    return keys


def party_key(registry_party):
    '''The key of a party name of the member registry (None for independents
    and extra-parliamentary members).'''
    if not isinstance(registry_party, str) or 'ανεξαρτητοι (εκτοσ κομματοσ)' in normalize(registry_party) \
            or registry_party.startswith('εξωκοινοβουλευτικ'):
        return None
    keys = [k for k in note_wings(registry_party) if k not in ('all', 'government', 'opposition')]
    return keys[0] if keys else None
