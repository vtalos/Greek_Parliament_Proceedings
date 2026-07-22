# -*- coding: utf-8 -*-
import re
import time

'''Κοινές βοηθητικές συναρτήσεις των υπόλοιπων scripts.

Shared helpers that used to be copy-pasted across the scripts. Everything here
is byte-identical to the copies it replaces, so the pipeline output is
unchanged. Note that member_speech_matcher.py keeps its own text_formatting:
it is a different variant and must stay that way.
'''

# REGULAR EXPRESSIONS
#------------------------------------------
# speaker detection, shared by member_speech_matcher.py and record_event_extractor.py
speaker_regex = re.compile(
    r"((\s*[Α-ΩΆ-ΏΪΫΪ́Ϋ́-]+)(\s+\([Α-ΩΆ-Ώα-ωά-ώϊϋΐΰΪΫΪ́Ϋ́-]+\))?(\s+[Α-ΩΆ-ΏΪΫΪ́Ϋ́]+)?(\s+[Α-ΩΆ-ΏΪΫΪ́Ϋ́-]+)*\s*(\(.*?\))?\s*\:)")

# Regex for both proedros or proedreuon
proedr_regex = re.compile(
    r"(^(((Π+Ρ(Ο|Ό)+(Ε|Έ))|(Ρ(Ο|Ό)+(Ε|Έ)Δ)|(ΠΡ(Ε|Έ)(Ο|Ό))|(ΠΡ(Ο|Ό)Δ)|(Η ΠΡ(Ο|Ό)(Ε|Έ)ΔΡ)|(ΠΡ(Ε|Έ)Δ))|(ΠΡΟΣΩΡΙΝΗ ΠΡΟΕΔΡΟΣ)|(ΠΡΟΣΩΡΙΝΟΣ ΠΡΟΕΔΡΟΣ)))")


def make_session():

    # requests is imported here and not at the top, so that the scripts that
    # only need the regexes or text_formatting stay free of the dependency
    import requests

    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})

    return session


def get_with_retries(session, URL):

    import requests

    for attempt in range(5):
        try:
            response = session.get(URL, timeout=60)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print('Request failed (', e, '), retrying in 30 seconds...')
            time.sleep(30)

    raise Exception('Request keeps failing for ' + URL)


def text_formatting(text):

    text = re.sub(r"['’`΄‘́̈]",'', text)
    text = re.sub(r'\t+' , ' ', text)
    text = text.lstrip()
    text = text.rstrip()
    text = re.sub(r'\s\s+' , ' ', text)
    text = re.sub(r'\s*(-|–)\s*' , '-', text) #fix dashes
    text = text.lower()
    text = text.translate(str.maketrans('άέόώήίϊΐiύϋΰ','αεοωηιιιιυυυ')) #remove accents
    # convert english characters to greek
    text = text.translate(str.maketrans('akebyolruxtvhmnz','ακεβυολρυχτνημνζ'))

    return text
