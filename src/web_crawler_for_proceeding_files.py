# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import time
import os
import re
import codecs
import csv
import hashlib
import urllib.parse
from argparse import ArgumentParser
from datetime import datetime as dt
from common import get_with_retries, make_session

def create_target_path(target_data_folder, tr, entry_counter, ext):

    td_columns = [td.getText().lower() for td in tr.find_all("td")[:4]] #get text from 4 first columns
    date = td_columns[0]
    period = td_columns[1]
    session = td_columns[2]
    sitting = td_columns[3]

    # For the selected table row return the value of the first column (date column)
    date = (date.replace("/", "-")).replace(" ", "")
    reversed_date = date[6:10]+date[5]+date[3:5]+date[2]+date[0:2]

    target_filename = reversed_date+'_'+ str(entry_counter)+"_"+period+"_"+session+"_"+sitting+"."+ext
    target_path = os.path.join(target_data_folder, target_filename)

    return(target_path)

def download_file(session, file_URL, target_path, manifest_writer):

    response = get_with_retries(session, file_URL)

    # write to a temporary name first, so that an interrupted download does
    # not leave a partial file that the resume check would take as complete
    with open(target_path + '.part', 'wb') as f:
        f.write(response.content)
    os.replace(target_path + '.part', target_path)

    # provenance record, so that every file can be verified against the source
    manifest_writer.writerow([os.path.basename(target_path), file_URL,
                              dt.now().strftime('%Y-%m-%d %H:%M:%S'),
                              hashlib.sha256(response.content).hexdigest()])

domain = "https://www.hellenicparliament.gr"
_URL = 'https://www.hellenicparliament.gr/Praktika/Synedriaseis-Olomeleias?pageNo='
url_part = "/UserFiles/"
entry_counter = 0 #counter number is included to the name of each file

parser = ArgumentParser(description=
    "Download the plenary proceeding record files from the Hellenic Parliament site.")
parser.add_argument("--since", default=None,
                    help="only download sittings whose date is strictly after this ISO "
                         "date (YYYY-MM-DD). Lets an incremental run skip the historical "
                         "archive without needing it on disk; normally set to the latest "
                         "sitting_date already stored downstream.")
parser.add_argument("-o", "--out", default='../original_data/',
                    help="folder to download the record files into")
parser.add_argument("--manifest", default='../out_files/download_manifest.csv',
                    help="provenance manifest csv (appended to)")
args = parser.parse_args()

target_data_folder = args.out
if not os.path.exists(target_data_folder):
    os.makedirs(target_data_folder)

session = make_session()

# keys of already downloaded files (ignoring the counter part), to allow resuming
downloaded = set()
for f in os.listdir(target_data_folder):
    parts = os.path.splitext(f)[0].split('_')
    if len(parts) >= 5:
        downloaded.add((parts[0],) + tuple(parts[2:]))

# Find the last page of the listing from the pagination links
html = get_with_retries(session, _URL+'1').text
soup = BeautifulSoup(html, "html.parser")
last_page = max(int(m.group(1)) for m in
                (re.search(r'pageNo=(\d+)', link['href'])
                 for link in soup.find_all('a', href=True)) if m)
print('The listing has', last_page, 'pages')

#Open a file in order to write down the rows with no files,
#and the download manifest with the provenance of every file
manifest_path = args.manifest
new_manifest = not os.path.exists(manifest_path)
with codecs.open('../out_files/rows_with_no_files.txt','w+', encoding='utf-8') as no_files, \
     open(manifest_path, 'a', encoding='utf-8', newline='') as manifest_file:

    manifest_writer = csv.writer(manifest_file)
    if new_manifest:
        manifest_writer.writerow(['filename', 'url', 'downloaded_at', 'sha256'])

    # Choose range of pages
    for pageNo in range (last_page,0,-1):

        page_URL = _URL+str(pageNo)
        print("Processing page",pageNo,"\n")
        html = get_with_retries(session, page_URL).text

        soup = BeautifulSoup(html, "html.parser")
        trs = soup.find("tbody").find_all("tr", {"class":["odd", "even"]})

        for tr in trs:

            entry_counter += 1
            print("No. ", entry_counter)

            files={} #dictionary with file extensions as keys and their links as values

            # From each table row return all the links
            for link in tr.findAll('a', href=True):

                href = link.get('href')

                # Keep the links that lead to the requested files and the
                # corresponding filetypes
                if url_part in href:
                    files.update({(href.split(".")[-1]).lower(): href})

            if len(files)==0:
                no_files.write('Page ' + str(pageNo) + " and date " + tr.find(
                    'td').getText() + " \n")
                print('File not found')
            else:
                # Download the file with the following preference order
                if "txt" in (ext.lower() for ext in files.keys()):
                    file_ext = 'txt'
                elif "docx" in (ext.lower() for ext in files.keys()):
                    file_ext = 'docx'
                elif "doc" in (ext.lower() for ext in files.keys()):
                    file_ext = 'doc'
                elif "pdf" in (ext.lower() for ext in files.keys()):
                    file_ext = 'pdf'
                else:
                    # links found, but none of them in a usable format
                    no_files.write('Page ' + str(pageNo) + " and date " + tr.find(
                        'td').getText() + " \n")
                    print('File not found')
                    continue

                file_URL = urllib.parse.urljoin(domain, files[file_ext])
                print("File url: ", file_URL)

                target_path = create_target_path(target_data_folder, tr, entry_counter, file_ext)

                parts = os.path.splitext(os.path.basename(target_path))[0].split('_')
                # incremental watermark: parts[0] is the sitting date (YYYY-MM-DD),
                # which sorts correctly as an ISO string. Skipping here, after the
                # entry counter has advanced, keeps filenames identical to a full crawl.
                if args.since and parts[0] <= args.since:
                    continue
                if (parts[0],) + tuple(parts[2:]) in downloaded:
                    print('Already downloaded')
                    continue

                download_file(session, file_URL, target_path, manifest_writer)

                time.sleep(1)

        time.sleep(1)
