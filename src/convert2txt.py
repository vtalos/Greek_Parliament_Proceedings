# -*- coding: utf-8 -*-
import os
import subprocess
import re
import shutil
from datetime import datetime as dt

def greek_numerals_to_numbers(numeral):

    number = 0

    greek_numerals = {"α": 1,"a":1, "β": 2, "b":2, "γ": 3,"δ": 4, "ε": 5, "έ":5, "e":5,
                      "στ": 6, "ζ": 7, "z":7,"η": 8, "ή":8, "h":8, "θ": 9,
                      "ι": 10, "i":10, "κ": 20, "k":20, "λ": 30, "μ": 40,
                      "m":40, "ν": 50, "n":50, "ξ": 60,"ο": 70, "o":70, "ό":70,
                      "π": 80, "ϙ": 90, "ϟ":90, "ρ": 100,"p":100, "σ": 200, "τ": 300,
                      "t":300, "υ": 400, "φ": 500, "χ": 600,"ψ": 700, "ω": 800,
                      "ϡ": 900}

    numeral = re.sub(r"[΄'`’(); r'\d']","", numeral)

    numeral_letters = list(numeral.lower())

    new_letters=[]

    for i in range(len(numeral_letters)):
        if numeral_letters[i] == 'σ':
            if i!=len(numeral_letters)-1: #if σ is not the last letter
                if numeral_letters[i+1]== 'τ': #if σ is followed by τ
                    new_letters.append('στ') #join σ and τ
            else:
                new_letters.append(numeral_letters[i])
        elif numeral_letters[i] == 'τ':
            pass
        else:
            new_letters.append(numeral_letters[i])

    for letter in new_letters:
        number+= greek_numerals[letter]

    return str(number)


def expand_two_digit_year(session, record_datetime):

    ''' The website abbreviates the year of the summer sessions as 'YY. The
        century is taken from the date of the record itself, so that '01 becomes
        2001 and not 1901. The year closest to the record date is chosen, so
        that a record at the turn of a century is still labelled correctly.'''

    def replace(match):
        two_digits = int(match.group(1))
        century = record_datetime.year // 100
        candidates = [(century - 1) * 100 + two_digits,
                      century * 100 + two_digits,
                      (century + 1) * 100 + two_digits]
        return str(min(candidates, key=lambda y: abs(y - record_datetime.year)))

    return re.sub(r"'(\d{2})(?!\d)", replace, session)


datapath = "../original_data/"
new_datapath = "../_data/"
if not os.path.exists(new_datapath):
    os.makedirs(new_datapath)

# ignore hidden files and the in-progress downloads of the crawler
filenames = [f for f in os.listdir(datapath)
             if not f.startswith('.') and not f.endswith('.part')]

#Keep history of changes
with open('../out_files/renaming_log.txt', 'wb') as renaming_log:

    counter=0

    for filename in filenames:

        #If filesize is zero, delete the file and do not copy it
        if os.path.getsize(datapath+filename) == 0:
            renaming_log.write(
                b'0 size file : ' + filename.encode("utf-8") + b'\n\n')

            os.remove(os.path.join(datapath, filename))
            print('Filesize is zero. File removed.\n')


        #If filesize is not zero, rename, copy and convert it to text
        else:

            file_date = filename.split('_')[0]

            file_datetime_object = dt.strptime(file_date, '%Y-%m-%d')

            counter += 1
            print('File No. ', counter)

            segments = (re.sub(r"[΄'`’]", "'", os.path.splitext(filename)[0])).split('_') #segments of filename seperated with underscore
            part1 = '_'.join(segments[:2]) #Date and counter number

            ''' For two sittings the website leaves the period column empty and
                shifts the remaining columns to the left, also naming the wrong
                period. The neighbouring sittings give the correct values.'''
            if segments[2] == '' and 'περιοδος' in segments[3]:
                print('Shifted columns in website entry. Correcting.\n')
                segments = segments[:2] + \
                           ["ιη' περιοδος (προεδρευομενης κοινοβουλευτικης δημοκρατιας)",
                            "β' σύνοδος", segments[4]]

            #PERIOD

            period = segments[2]

            if period!='':
                period = re.sub(r'[\(-\)-]', '', period) #remove parentheses and dashes

                if "θ'περιοδος" in period:
                    period = period.replace("θ'","θ' ")

                if 'προεδρευομενης κοινοβουλευτικης δημοκρατιας' in period:
                    period = period.replace('προεδρευομενης κοινοβουλευτικης δημοκρατιας', 'presided-parliamentary-republic')

                period = period.split(' ')
                period_number = greek_numerals_to_numbers(period[0])

                if 'αναθεωρητική' in period:
                    review_number = greek_numerals_to_numbers(period[2])
                    new_period = 'period-'+period_number+'-review-'+review_number+'-'.join(period[4:])
                else:
                    new_period = 'period-'+period_number+'-'+'-'.join(period[2:])

            else:
                new_period = ''

            #SESSION

            session = segments[3]

            if session!='':
                session = session.replace("γ'τμήμα", "γ' τμήμα")
                # newer site entries miss the space e.g. γ'σύνοδος
                session = re.sub(r"'(?=[^\s\d])", "' ", session)
                session = expand_two_digit_year(session, file_datetime_object)

                ''' Reset per file. Both were previously left over from the
                    previous iteration when the current entry does not provide
                    them, which silently labelled the sitting with the session
                    number or year of another record.'''
                session_number = ''
                year = ''

                section = session.split(' ')
                if "'" in section[0]:
                    session_number = greek_numerals_to_numbers(section[0])

                if (re.search(r'\d', section[-1])):
                    year = re.sub(r"[()]", '', section[-1])

                if 'τμήμα διακοπής εργασιών βουλής θέρους' in session:
                    new_session = year+'-summer-recess-section-'+session_number
                elif 'θέρο' in session:
                    session = session.replace('θέρος', 'summer')
                    session = session.replace('συνέχιση θέρους', 'continuation-of-summer-recess')
                    new_session = session.replace(' ', '-')
                elif 'έκτακτη σύνοδος' in session:
                    new_session = session.replace('έκτακτη σύνοδος', 'parliament-recall-extraordinary-session')
                elif 'συνέχιση ολομέλειας' in session:
                    new_session = 'session-'+session_number+'-(continuation-of-plenary-session)'
                else:
                    new_session = 'session'+'-'+session_number

                # an empty piece leaves a dangling dash, so that a missing
                # session number or year is visible instead of looking valid
                if new_session.startswith('-') or new_session.endswith('-') \
                        or '--' in new_session:
                    print('WARNING: incomplete session name', new_session, '\n')
                    renaming_log.write(b'incomplete session name: '
                                       + filename.encode('utf-8') + b'\n\n')
            else:
                new_session = ''

            #SITTING

            sitting = segments[4]

            if sitting!='':
                if sitting=='ειδικη συνεδριαση ημερα της γυναικας':
                    new_sitting = "special-sitting-international-women-'s-day"
                elif sitting=='ειδικη ημερησια διαταξη της ολομελειας της βουλης':
                     new_sitting = 'a-special-agenda-for-the-plenary-session-of-the-parliament'
                elif sitting=='ειδικη εκδηλωση για την επετειο της γενοκτονιας των ποντιων στη βουλη':
                    new_sitting = 'special-event-anniversary-of-Pontic-Greek-genocide'
                elif sitting=='βουλη των εφηβων':
                    new_sitting = 'Youth-Parliament'
                else:
                    sitting_number = greek_numerals_to_numbers(sitting)
                    new_sitting = 'sitting-'+sitting_number
            else:
                new_sitting = ''

            ext = os.path.splitext(filename)[1] #initial file extension including dot

            #Compose new name without extension
            new_filename = part1+'_'+new_period+'_'+new_session+'_'+new_sitting+ext

            # skip files already converted in a previous run
            if os.path.exists(os.path.join(new_datapath, os.path.splitext(new_filename)[0]+'.txt')):
                print('Already converted.\n')
                continue

            # copy and rename file to new location
            shutil.copy(os.path.join(datapath, filename),
                        os.path.join(new_datapath, new_filename))

            if ext.lower()!='.txt':
                command = ['java', '-jar', 'tika-app-1.20.jar', '--text', '--encoding=utf-8',
                           os.path.join(new_datapath, new_filename)]
                txt_path = os.path.join(new_datapath, os.path.splitext(new_filename)[0])+'.txt'

                print(command)
                ''' The text goes first to a hidden temporary file, which every
                    script of the pipeline ignores, and is renamed only after a
                    successful conversion. So neither an interruption in the
                    middle of the writing nor a failed conversion (e.g. when
                    java is missing, which exits with an empty output) can
                    leave a file that the skip check would treat as converted.'''
                tmp_path = os.path.join(new_datapath,
                                        '.' + os.path.splitext(new_filename)[0] + '.txt.part')
                #no shell, so quotes/backticks in the greek filenames cannot break it
                with open(tmp_path, 'wb') as tika_out:
                    result = subprocess.run(command, stdout=tika_out)

                if result.returncode != 0 or os.path.getsize(tmp_path) == 0:
                    print('WARNING: conversion failed, removing output\n')
                    renaming_log.write(b'failed conversion: '
                                       + filename.encode('utf-8') + b'\n\n')
                    os.remove(tmp_path)
                else:
                    ''' The fonts of the older pdf records render Δ and μ with
                        the lookalikes ∆ (increment) and µ (micro), which would
                        break the speaker detection (e.g. ΠΡΟΕ∆ΡΕΥΩΝ). '''
                    with open(tmp_path, 'r', encoding='utf-8') as converted:
                        text = converted.read()
                    if '∆' in text or 'µ' in text:
                        with open(tmp_path, 'w', encoding='utf-8') as converted:
                            converted.write(text.replace('∆', 'Δ').replace('µ', 'μ'))
                    os.replace(tmp_path, txt_path)

                # delete initial non-txt files and keep only converted files
                os.remove(os.path.join(new_datapath, new_filename))
            else:
                print('File already in txt format.\n')
                ''' A few txt records of the website are in the legacy greek
                    8-bit encoding instead of utf-8, transcoded here so that
                    the whole corpus reads uniformly. '''
                txt_path = os.path.join(new_datapath, new_filename)
                data = open(txt_path, 'rb').read()
                try:
                    data.decode('utf-8')
                except UnicodeDecodeError:
                    print('Transcoding from greek 8-bit encoding.\n')
                    with open(txt_path, 'w', encoding='utf-8') as transcoded:
                        transcoded.write(data.decode('iso-8859-7'))

            renaming_log.write(b'Before: '+filename.encode("utf-8")+b'\nAfter: '+(os.path.splitext(new_filename)[0]+'.txt').encode("utf-8")+b'\n\n')
