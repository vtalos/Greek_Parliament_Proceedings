# -*- coding: utf-8 -*-
import re
from datetime import timedelta
import pandas as pd
import numpy as np

# the website writes the party names without spaces and in several
# inconsistent forms, mapped here to the name used in the dataset
party_names = {
    'ΑΝΕΞΑΡΤΗΤΟΙΕΛΛΗΝΕΣΕΘΝΙΚΗΠΑΤΡΙΩΤΙΚΗΔΗΜΟΚΡΑΤΙΚΗΣΥΜΜΑΧΙΑ':
        'ανεξαρτητοι ελληνες εθνικη πατριωτικη δημοκρατικη συμμαχια',
    'ΑΝΕΞΑΡΤΗΤΟΙΕΛΛΗΝΕΣ-ΠΑΝΟΣΚΑΜΜΕΝΟΣ':
        'ανεξαρτητοι ελληνες - πανος καμμενος',
    'ΑΝΕΞΑΡΤΗΤΟΙ':
        'ανεξαρτητοι (εκτος κομματος)',
    'ΣΥΝΑΣΠΙΣΜΟΣ':
        'συνασπισμος της αριστερας των κινηματων και της οικολογιας',
    'ΑΝΕΞΑΡΤΗΤΟΙΔΗΜΟΚΡΑΤΙΚΟΙΒΟΥΛΕΥΤΕΣ':
        'ανεξαρτητοι δημοκρατικοι βουλευτες',
    'ΠΟΛ.Α.':
        'πολιτικη ανοιξη',
    'ΟΟ.ΕΟ.':
        'οικολογοι εναλλακτικοι (ομοσπονδια οικολογικων εναλλακτικων οργανωσεων)',
    'ΔΗ.ΑΝΑ.':
        'δημοκρατικη ανανεωση',
    'ΔΗ.Κ.ΚΙ.':
        'δημοκρατικο κοινωνικο κινημα',
    'ΕΝΩΣΗΚΕΝΤΡΩΩΝ':
        'ενωση κεντρωων',
    'ΝΕΑΔΗΜΟΚΡΑΤΙΑ':
        'νεα δημοκρατια',
    'ΛΑ.Ο.Σ.':
        'λαικος ορθοδοξος συναγερμος',
    'ΛΑΪΚΟΣΣΥΝΔΕΣΜΟΣ-ΧΡΥΣΗΑΥΓΗ':
        'λαικος συνδεσμος - χρυση αυγη',
    'ΚΟΜΜΟΥΝΙΣΤΙΚΟΚΟΜΜΑΕΛΛΑΔΑΣ':
        'κομμουνιστικο κομμα ελλαδας',
    'Κ.Κ.Εσ':
        'κομμουνιστικο κομμα ελλαδας εσωτερικου',
    'ΣΥΝΑΣΠΙΣΜΟΣΡΙΖΟΣΠΑΣΤΙΚΗΣΑΡΙΣΤΕΡΑΣ':
        'συνασπισμος ριζοσπαστικης αριστερας',
    'ΛΑΪΚΗΕΝΟΤΗΤΑ':
        'λαικη ενοτητα',
    'ΠΑ.ΣΟ.Κ.':
        'πανελληνιο σοσιαλιστικο κινημα',
    'ΔΗΜΟΚΡΑΤΙΚΗΑΡΙΣΤΕΡΑ':
        'δημοκρατικη αριστερα',
    'ΔΗΜΟΚΡΑΤΙΚΗΣΥΜΠΑΡΑΤΑΞΗ(ΠΑΝΕΛΛΗΝΙΟΣΟΣΙΑΛΙΣΤΙΚΟΚΙΝΗΜΑ-ΔΗΜΟΚΡΑΤΙΚΗΑΡΙΣΤΕΡΑ)':
        'δημοκρατικη συμπαραταξη (πανελληνιο σοσιαλιστικο κινημα - δημοκρατικη αριστερα)',
    'ΤΟΠΟΤΑΜΙ':
        'το ποταμι',
    'ΕΝΩΣΗΚΕΝΤΡΟΥ-ΝΕΕΣΔΥΝΑΜΕΙΣΕΚ/ΝΔ':
        'ενωση κεντρου - νεες δυναμεις (ε.κ. - ν.δ.)',
    'ΕΔΗΚ':
        'ενωση δημοκρατικου κεντρου (εδηκ)',
    'ΕΘΝΙΚΗΠΑΡΑΤΑΞΙΣ':
        'εθνικη παραταξη',
    'ΝΕΟΦΙΛΕΛΕΥΘΕΡΩΝ':
        'κομμα νεοφιλελευθερων',
    'ΕΝΙΑΙΑΔΗΜΟΚΡΑΤΙΚΗΑΡΙΣΤΕΡΑ-Ε.Δ.Α.':
        'ενιαια δημοκρατικη αριστερα (ε.δ.α.)',
    'ΣΥΜ/ΧΙΑΠΡ':
        'συμμαχια προοδευτικων και αριστερων δυναμεων',
    'ΕΛΛΗΝΙΚΗΛΥΣΗ-ΚΥΡΙΑΚΟΣΒΕΛΟΠΟΥΛΟΣ':
        'ελληνικη λυση - κυριακος βελοπουλος',
    'ΚΙΝΗΜΑΑΛΛΑΓΗΣ':
        'κινημα αλλαγης',
    'ΜέΡΑ25':
        'μετωπο ευρωπαικης ρεαλιστικης ανυπακοης (μερα25)',
    'ΣΥΝΑΣΠΙΣΜΟΣΡΙΖΟΣΠΑΣΤΙΚΗΣΑΡΙΣΤΕΡΑΣ-ΠΡΟΟΔΕΥΤΙΚΗΣΥΜΜΑΧΙΑ':
        'συνασπισμος ριζοσπαστικης αριστερας - προοδευτικη συμμαχια',
    'ΠΑΣΟΚ-ΚΙΝΗΜΑΑΛΛΑΓΗΣ':
        'πασοκ - κινημα αλλαγης',
    'ΛΑ.ΟΣ':
        'λαικος ορθοδοξος συναγερμος',
    'ΣΠΑΡΤΙΑΤΕΣ':
        'σπαρτιατες',
    'ΔΗΜΟΚΡΑΤΙΚΟΠΑΤΡΙΩΤΙΚΟΚΙΝΗΜΑ"ΝΙΚΗ"':
        'δημοκρατικο πατριωτικο κινημα νικη',
    'ΝΕΑΑΡΙΣΤΕΡΑ':
        'νεα αριστερα',
    'ΠΛΕΥΣΗΕΛΕΥΘΕΡΙΑΣ-ΖΩΗΚΩΝΣΤΑΝΤΟΠΟΥΛΟΥ':
        'πλευση ελευθεριας - ζωη κωνσταντοπουλου',
    }


def party_formatting(party):

    if party not in party_names:
        print('Party not matched to existing list ', party)
        return party

    return party_names[party]

def name_formatting(name):

    name = re.sub(r"(\S)\(", r'\1 (', name) #add missing whitespace before parenthesis
    # when people have two surnames or two names, we glue them together with '-' in the middle
    name = re.sub(r"(\s*-\s*)|(\sή\s)",'-', name)
    name = name.translate(str.maketrans('άΆέΈόΌώΏήΉίΊϊΐύΎϋΰ','αΑεΕοΟωΩηΗιΙιιυΥυυ')) #remove accents
    name = re.sub(r"\t+" , " ", name) #replace tabs with space
    name = re.sub(r"΄", "", name)  # replace accents with empty string
    name = re.sub(r"\s\s+" , " ", name) #replace more than one spaces with one space
    name = re.sub(r"(συζ.\s)",'συζ.', name) #remove space between συζ. and the name of the husband
    name = re.sub(r"μαρια γλυκερια",'μαρια-γλυκερια', name)
    name = re.sub(r"σουκουλη-βιλιαλη δημητριου μαρια ελενη \(μαριλενα\)",'σουκουλη-βιλιαλη δημητριου μαρια-ελενη (μαριλενα)', name)
    name = re.sub(r"χατζη χαβουζ γκαληπ",'χατζη-χαβουζ-γκαληπ', name)
    name = re.sub(r"μακρη θεοδωρου",'μακρη-θεοδωρου', name)
    name = re.sub(r"καρα γιουσουφ",'καρα-γιουσουφ', name)
    name = re.sub(r'χατζη οσμαν','χατζη-οσμαν', name)
    name = re.sub(r"σαδικ αμετ αμετ σαδηκ",'σαδικ αμετ αμετ', name)
    name = re.sub(r'ακριτα χα λουκη συλβα-καιτη','ακριτα συζ.λουκη συλβα-καιτη', name)
    name = re.sub(r'ιωανννης','ιωαννης', name)

    # specific correction missing father's name
    if name == 'βαγενα-κηλαηδονη αννα':
        name = 'βαγενα-κηλαηδονη γεωργιου αννα'
    if name == 'μονογυιου αικατερινη':
        name = 'μονογυιου χχχχχχχ αικατερινη'
    if name == 'ληναιος-μητυλιναιος γεωργιου (στεφανος)-διονυσιος':
        name = 'ληναιος-μητυληναιος γεωργιου στεφανος (διονυσιος)'
    if name == 'βεττα καλλιοπη':
        name = 'βεττα χχχχχχχ καλλιοπη'

    name = name.rstrip() #remove trailing space from string

    # name forms that the website changed since the 1989-2020 dataset was
    # published, normalized back to the published forms for continuity
    d = {'αγατσα αριστειδη αριαδνη (αρια)': 'αγατσα αριστειδη αριαδνη',
         'αυγερινοπουλου ζησιμου διονυσια': 'αυγερινοπουλου ζησιμου διονυσια-θεοδωρα',
         'αχτσιογλου θεμιστοκλη ευτυχια (εφη)': 'αχτσιογλου θεμιστοκλη ευτυχια',
         'βεττα δημητριου καλλιοπη': 'βεττα χχχχχχχ καλλιοπη',
         'δενδιας σπυριδωνα νικολαος-γεωργιος': 'δενδιας σπυριδωνος νικολαος-γεωργιος',
         'ελευθεριαδου παυλου σουλτανα (τανια)': 'ελευθεριαδου παυλου σουλτανα',
         'κονσολας νικια εμμανουηλ': 'κονσολας νικια εμμανουηλ (μανος)',
         'κωνσταντοπουλου νικολαου ζωη': 'κωνσταντοπουλου ν. ζωη',
         'ξενογιαννακοπουλου διονυσιου μαρια ελιζα (μαριλιζα)': 'ξενογιαννακοπουλου διονυσιου μαρια-ελιζα (μαριλιζα)',
         'παρασυρης γεωργιου φραγκισκος (φρεντυ)': 'παρασυρης γεωργιου φραγκισκος',
         'παφιλης σπυριδωνα αθανασιος': 'παφιλης σπυριδωνος αθανασιος',
         'ρουσοπουλος βασιλειου θεοδωρος (θοδωρος)': 'ρουσοπουλος βασιλειου θεοδωρος',
         'τασουλας αν. κωνσταντινος': 'τασουλας αναστασιου κωνσταντινος',
         'φωτηλας ασημακη ιασωνας': 'φωτηλας ασημακη ιασων',
         }
    if name in d:
        name = d[name]

    return name

def region_formatting(region):

    region = (region.lower()).translate(str.maketrans('άέόώήίϊΐiύϋΰ','αεοωηιιιιυυυ'))
    region = re.sub(r"\t+" , " ", region)
    region = re.sub(r"΄", " ", region)
    region = re.sub(r"\s\s+" , " ", region)
    region = region.rstrip()

    if region=="α'θεσσαλονικης":
        region= "α' θεσσαλονικης"
    elif region=="α'αθηνων":
        region="α' αθηνων"
    elif region == "β'θεσσαλονικης":
        region = "β' θεσσαλονικης"
    elif region == "β'αθηνων":
        region = "β' αθηνων"
    elif region == "β2'δυτικουτομεααθηνων":
        region = "β2' δυτικου τομεα αθηνων"
    elif region == "α ανατολικησαττικης":
        region = "α' ανατολικης αττικης"
    elif region == "α'πειραιως":
        region = "α' πειραιως"
    elif region == "β'πειραιως":
        region = "β' πειραιως"
    elif region == "β3 νοτιουτομεααθηνων":
        region = "β3' νοτιου τομεα αθηνων"
    elif region == "β δυτικησαττικης":
        region = "β' δυτικης αττικης"
    elif region == "β1'βορειουτομεααθηνων":
        region = "β1' βορειου τομεα αθηνων"

    return region

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

df = pd.read_csv('../out_files/original_parl_members_data.csv', encoding='utf-8', header=None,
                 names = ['no', 'member_name', 'period_date_range', 'event_date',
         'administrative_region', 'political_party',  'event_description'])

# remove lines that contain "NO DATA"
df = df[~df['period_date_range'].str.contains("NO DATA")]

# remove characters from period
df['period_date_range'] = df['period_date_range'].\
    str.replace(r"[a-zA-Zα-ωΑ-Ω΄':()]", '', regex=True)

# split dates of period start & end and create new columns
dates = df['period_date_range'].str.split('-', n=1, expand=True)

df['period_start_date'] = dates[0]
df['period_start_date'] = pd.to_datetime(df['period_start_date'],
                                         format='%d/%m/%Y')
df['period_end_date'] = dates[1]
df['period_end_date'] = pd.to_datetime(df['period_end_date'],
                                         format='%d/%m/%Y')

# drop old column
df.drop(columns=['period_date_range'], inplace=True)

# keep periods that end from 1989 onwards, matching the available proceedings
df = df[(df['period_end_date'].dt.year >= 1989)]

# replace not needed strings in data cells
df['member_name'] = df['member_name'].str.replace("Name:", '')
df['event_date'] = df['event_date'].str.replace("Date:", '')
df['administrative_region'] = df['administrative_region'].str.replace("Administrative-Region:", '')
df['event_date'] = pd.to_datetime(df['event_date'], format='%d/%m/%Y')
df['political_party'] = df['political_party'].str.replace(
    "Parliamentary-Party:", '')
df['event_description'] = df['event_description'].str.replace("Description:",'')

# Format political party information
df['political_party'] = df['political_party'].apply(party_formatting)

df['administrative_region'] = df['administrative_region'].apply(region_formatting)

new_dfrows_list = []


''' A member starts their parliamentary term with any of the following events,
    either by being elected or by replacing someone that left 
    Thus, start_cases can only be the first of the events for each member '''
start_cases = ['aντικατέστησε', #e.g. aντικατέστησε:δούρουειρήνη(ρένα)αθανασίου(λόγω:παραίτησηςαπότοβουλευτικόαξίωμα)
               'εκλογής',
               ]

''' A member ends their parliamentary term with any of the following events,
    resignation, passing away, by losing their position or by being murderded '''
end_cases = ['παραίτησηςαπότοβουλευτικόαξίωμα',
             'απεβίωσε',
             'έκπτωσηςβουλευτικούαξιώματος',
             'δολοφονήθηκε',
             ]

''' A member can change their parliamentary position/party with any of the following events,
    change of party or independence from all parties '''
change_party_cases = ['προσχώρησης/επανένταξης', # change of party
                      'προσχώρηση', # change of party
                      'ανεξαρτητοποίηση', # independent (outside a party)
                      'προσχωρησηστηνκ.ο.τησνεασδημοκρατιας', # change of party
                      'ετέθηεκτός', # independent due to expulsion (outside a party)
                      'διεγράφη', # independent due to deletion (outside a party)
                      ]

error_cases = []

# For each parliamentary period, for each member in a period
for id, subdf in df.groupby(['no','period_start_date']): #no is a unique id given to each member

    # Remove specific error in data for 'πλακιωτάκης ιωσήφ ιωάννης'
    if subdf.member_name.iloc[0] == 'Πλακιωτάκης Ιωσήφ Ιωάννης' and \
            id[-1] == pd.Timestamp('2015-09-20 00:00:00'):
        subdf = subdf[subdf['event_date'] != pd.to_datetime('2019-07-07')]

    # The website misses the 'Εκλογής' event of 'Βαρβιτσιώτης Ιωάννη Μιλτιάδης'
    # for period Κ΄, where only his resignation of 25/01/2024 is listed
    if 'Βαρβιτσιώτης' in subdf.member_name.iloc[0] and \
            id[-1] == pd.Timestamp('2023-07-03 00:00:00'):
        missing_row = subdf.iloc[0].copy()
        missing_row['event_date'] = pd.Timestamp('2023-06-25')
        missing_row['event_description'] = 'Εκλογής'
        subdf = pd.concat([missing_row.to_frame().T, subdf], ignore_index=True)

    rows_num = subdf.shape[0]

    member_name = name_formatting((subdf.iloc[0]['member_name']).lower())
    end_follows = False # refers to change of political party or any of the end cases
    change_follows = False # refers to change of political party

    ''' If member has only one event in this period, it should be a start case. In this case,
        the parliamentary term rolled smoothly with no interruptions or changes of political party'''
    if rows_num==1:

        if any((subdf.iloc[0]['event_description'].lower()).startswith(s) for s in start_cases):

            member_start_date = subdf.iloc[0]['event_date']
            member_end_date = subdf.iloc[0]['period_end_date']
            political_party = subdf.iloc[0]['political_party']
            administrative_region = subdf.iloc[0]['administrative_region']

            new_dfrows_list.append({'member_name': member_name,
                                    'member_start_date': member_start_date,
                                    'member_end_date': member_end_date,
                                    'political_party': political_party,
                                    'administrative_region': administrative_region,
                                    })
        else:
            print('Probably missing data of case '+str(id)+', '+
                  str(subdf.iloc[0]['member_name']))
            print()

    else:
        ''' If the parliamentary term of the member involves changes of party or end events,
            we iterate through rows inversely over time'''
        for i in range(rows_num-1,-1,-1): # e.g. 4 rows iterates from index 3 to 0

            ''' End events. In this case a start or change event must precede,
                from which we will take the start date of the term'''
            if any((subdf.iloc[i]['event_description'].lower()).startswith(e) for e in end_cases):

                member_end_date = subdf.iloc[i]['event_date']
                last_event_date = subdf.iloc[i]['event_date']
                last_political_party = subdf.iloc[i]['political_party']
                end_follows = True
                change_follows = False

            # Change events
            elif any(p in subdf.iloc[i]['event_description'].lower() for p in change_party_cases):

                if end_follows:
                    member_end_date = last_event_date
                elif change_follows:
                    member_end_date = last_event_date - timedelta(days=1)
                else:
                    member_end_date = subdf.iloc[i]['period_end_date']

                member_start_date = subdf.iloc[i]['event_date']
                political_party = subdf.iloc[i]['political_party']
                administrative_region = subdf.iloc[i]['administrative_region']

                new_dfrows_list.append({'member_name': member_name,
                                     'member_start_date': member_start_date,
                                     'member_end_date': member_end_date,
                                     'political_party': political_party,
                                    'administrative_region': administrative_region,
                                      })

                if end_follows:
                    if last_political_party != political_party:
                        error_cases.append(subdf.iloc[i]['event_description'].lower())
                        print(subdf.iloc[i]['no'].lower())

                # Update last event
                last_event_date = subdf.iloc[i]['event_date']
                last_political_party = subdf.iloc[i]['political_party']
                end_follows = False
                change_follows = True

            # Start events
            elif any((subdf.iloc[i]['event_description'].lower()).startswith(s) for s in start_cases):
                member_start_date = subdf.iloc[i]['event_date']
                administrative_region = subdf.iloc[i]['administrative_region']


                if end_follows:
                    ''' political party and member_end_date have been declared
                        member_end_date is filled if end event follows '''
                    new_dfrows_list.append({'member_name': member_name,
                                          'member_start_date': member_start_date,
                                          'member_end_date': member_end_date,
                                          'political_party': last_political_party,
                                            'administrative_region': administrative_region,
                                          })
                elif change_follows:
                    member_end_date = last_event_date - timedelta(days=1)
                    political_party = subdf.iloc[i]['political_party']
                    new_dfrows_list.append({'member_name': member_name,
                                          'member_start_date': member_start_date,
                                          'member_end_date': member_end_date,
                                          'political_party': political_party,
                                            'administrative_region': administrative_region,
                                          })

                # if nothing follows like the case of Διαμαντίδης Δημήτριος
                else:
                    member_end_date = subdf.iloc[i]['period_end_date']
                    political_party = subdf.iloc[i]['political_party']
                    new_dfrows_list.append({'member_name': member_name,
                                          'member_start_date': member_start_date,
                                          'member_end_date': member_end_date,
                                          'political_party': political_party,
                                          'administrative_region': administrative_region,
                                          })

                    print('Check case for '+str(subdf.iloc[i]['member_name'])+
                          ' around date '+str(subdf.iloc[i]['period_end_date']))


''' The website member page of Σαλμάς Μάριος returns no data anymore, so his
    terms of office are added manually, as they appear in the published
    1989-2020 dataset (with the corrupted start date of the first term fixed
    and the last term extended to the end of period ΙΗ΄).'''
for start, end in [('1996-09-22', '2000-03-14'), ('2000-04-09', '2004-02-11'),
                   ('2004-03-07', '2007-08-18'), ('2007-09-16', '2009-09-07'),
                   ('2009-10-04', '2012-04-11'), ('2012-05-06', '2012-05-19'),
                   ('2012-06-17', '2014-12-31'), ('2015-01-25', '2015-08-28'),
                   ('2015-09-20', '2019-06-11'), ('2019-07-07', '2023-04-22')]:
    new_dfrows_list.append({'member_name': 'σαλμας γεωργιου μαριος',
                            'member_start_date': pd.Timestamp(start),
                            'member_end_date': pd.Timestamp(end),
                            'political_party': 'νεα δημοκρατια',
                            'administrative_region': 'αιτωλοακαρνανιας',
                            })

''' The member pages date several events of period Κ΄ (resignations,
    independencies, deaths) with the election date 25/06/2023 instead of the
    date the event took place, which corrupts the terms of the members below
    (zero-length, overlapping or impossible terms). Their period Κ΄ terms are
    rebuilt here with the dates of the parliamentary record and the press
    (see NOTES.md). None is used for the terms that are still running.'''
period_k_corrections = {
    'κωνσταντινοπουλος κωνσταντινου οδυσσεας': ('αρκαδιας', [
        ('2023-06-25', '2026-03-12', 'πασοκ - κινημα αλλαγης'),
        ('2026-03-12', '2026-03-13', 'ανεξαρτητοι (εκτος κομματος)')]),
    'αποστολακης στεφανου γεωργιος': ('επικρατειας', [
        ('2023-06-25', '2024-12-02', 'δημοκρατικο πατριωτικο κινημα νικη')]),
    'αποστολακης ευαγγελου ευαγγελος': ('επικρατειας', [
        ('2023-06-25', '2024-12-02', 'συνασπισμος ριζοσπαστικης αριστερας - προοδευτικη συμμαχια'),
        ('2024-12-02', None, 'ανεξαρτητοι (εκτος κομματος)')]),
    'αυγενακης κωνσταντινου ελευθεριος': ('ηρακλειου', [
        ('2023-06-25', '2024-07-04', 'νεα δημοκρατια'),
        ('2024-07-04', '2024-12-20', 'ανεξαρτητοι (εκτος κομματος)'),
        ('2024-12-20', None, 'νεα δημοκρατια')]),
    'ταγαρας χρηστου νικολαος': ('κορινθιας', [
        ('2023-06-25', '2026-05-29', 'νεα δημοκρατια')]),
    'τασουλας αναστασιου κωνσταντινος': ('ιωαννινων', [
        ('2023-06-25', '2025-01-16', 'νεα δημοκρατια')]),
    'χαλκιας ευαγγελου αθανασιος': ("α' αθηνων", [
        ('2023-06-25', '2025-06-10', 'σπαρτιατες'),
        ('2025-06-10', None, 'ανεξαρτητοι (εκτος κομματος)')]),
}
period_k_start = pd.Timestamp('2023-06-25')
# the open period ends on the crawl date, like the terms that are still running
ongoing_end = max(row['member_end_date'] for row in new_dfrows_list)
new_dfrows_list = [row for row in new_dfrows_list
                   if not (row['member_name'] in period_k_corrections
                           and row['member_start_date'] >= period_k_start)]
for member_name, (region, terms) in period_k_corrections.items():
    for start, end, party in terms:
        new_dfrows_list.append({'member_name': member_name,
                                'member_start_date': pd.Timestamp(start),
                                'member_end_date': pd.Timestamp(end) if end else ongoing_end,
                                'political_party': party,
                                'administrative_region': region,
                                })

new_df = pd.DataFrame(new_dfrows_list, columns=['member_name', 'member_start_date',
                                                'member_end_date', 'political_party',
                                                'administrative_region',
                                                ])

# drop activity that ends before 1/1/1989
new_df = new_df[(new_df['member_end_date'].dt.year >= 1989)]

# replace start dates before 1989 with 1/1/1989
new_df['member_start_date'] = np.where(new_df['member_start_date'] < '1989-01-01',
                                       pd.to_datetime(['1989-01-01']),
                                       new_df['member_start_date'])

new_df.to_csv('../out_files/parl_members_activity_1989onwards.csv', header=True, index=False, encoding='utf-8')
