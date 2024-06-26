import csv
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import urllib.request
import sys
import re
from socket import timeout
from urllib.error import HTTPError, URLError
from time import sleep, strftime
import chardet
import argparse
import os.path

ua = "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0"
csvdict = {}
parser = argparse.ArgumentParser()
parser.add_argument("filepath")
args = parser.parse_args()
if not os.path.isfile(args.filepath):
    print("File not found, check your path and try again")
    sys.exit(1)


def extractEmail(url):
    try:
        print("Searching emails on ", url)
        count = 0
        listUrl = []

        req = urllib.request.Request(url, data=None, headers={"User-Agent": ua})

        try:
            conn = urllib.request.urlopen(req, timeout=10)

        except timeout:
            raise ValueError("Timeout ERROR")

        except (HTTPError, URLError):
            raise ValueError("Bad Url...")

        status = conn.getcode()
        contentType = conn.info().get_content_type()

        if status != 200 or contentType == "audio/mpeg":
            raise ValueError("Wrong type or status code not 200...")
        html = conn.read()
        # Some errors still occurs on decoding despite trying to detect charset. Need debugging
        html = html.decode(chardet.detect(html)["encoding"])
        emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}", html)

        for email in emails:
            if (email not in listUrl) and not re.search(r"@\d+x\.", email):
                # The regex here is used to avoid images named like image@1x.png wich is similar to an email
                count += 1
                listUrl.append(email)

    except KeyboardInterrupt:
        sys.exit(1)

    except Exception as e:
        print(e)
    return listUrl


with open(args.filepath, newline="") as csvfile:
    spamreader = csv.reader(csvfile, delimiter=",", quotechar="|")
    next(spamreader)
    for row in spamreader:
        results = DDGS().text(
            row[15],
            backend="html",
            region="fr-fr",
            safesearch="off",
            timelimit="n",
            max_results=10,
        )
        csvdict[row[15]] = []
        for result in results:
            result = extractEmail(result["href"])
            if result not in csvdict[row[15]]:
                for sublist in result:
                    csvdict[row[15]] += result
        sleep(1)
timestr = f'{strftime("%Y-%m-%d-%H%M%S")}.csv'
print(csvdict)

with open(timestr, "w", newline="") as csvoutputfile:
    for item in csvdict.keys():
        # Not using python csv module because i wasn't able to get the output i wanted
        csvoutputfile.write(item + ", " + ", ".join(csvdict[item]) + "`\n")
