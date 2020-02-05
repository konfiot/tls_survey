#!/usr/bin/python3
# coding: utf-8

import zipfile
import requests
import io
from hyper.contrib import HTTP20Adapter
import hyper
import random
import string
import time

from M2Crypto import SSL

# For error handling
import socket

STORE = "CSV" #CSV, MONGO

PURGE_DB = True # Reset DB on startup

start_file = "https://s3.amazonaws.com/alexa-static/top-1m.csv.zip"
out_path = 'out.csv' # For CSV store

mongo_client = None

if STORE == "MONGODB":
	import pymongo
	mongo_client = pymongo.MongoClient()
	mongo_db = mongo_client.tls_survey
	if PURGE_DB:
		mongo_db.sites.drop()


zip_file = io.BytesIO(requests.get(start_file).content)

def randomString(stringLength=10):
	letters = string.ascii_lowercase
	return ''.join(random.choice(letters) for i in range(stringLength))

def http_version(site):
	s = requests.Session()
	s.mount("https://" + site, HTTP20Adapter())
	try:
		r = s.get("https://" + site)
	except (socket.timeout, requests.exceptions.ConnectionError, TimeoutError):
		return "TIMEOUT"
	except KeyboardInterrupt:
		exit(-1)
	except:
		return "ERROR"

	if isinstance(r.raw,  hyper.HTTP20Response):
		return "2"
	elif isinstance(r.raw,  hyper.HTTP11Response):
		return "1.1"
	else:
		return "FAIL"

def answer_malformed(site):
	random = randomString(50)
	try:
		r = requests.get("https://" + site + "/" + random)
	except (TimeoutError, requests.exceptions.ConnectionError):
		return "TIMEOUT"
	except KeyboardInterrupt:
		exit(-1)
	except:
		return "ERROR"
	try:
		return str(r.status_code) + "IN" if random in r.content.decode(r.encoding) else str(r.status_code)
	except (TypeError, UnicodeDecodeError):
		return str(r.status_code)

def ssl_cipher(site):
	ctx = SSL.Context()
	s = SSL.Connection(ctx)

	s.postConnectionCheck = None
	try:
		s.connect((site, 443))
	except TimeoutError:
		return "TIMEOUT"
	except KeyboardInterrupt:
		exit(-1)
	except:
		return "ERROR"

	if s.get_state() == "SSLOK ":
		c = s.get_cipher()
		cp = c.name()
		return cp
	s.close()




def process(site):
	print(f"Processing site : {site} ; ", end="")
	out = {"site": site}

	t0 = time.time()
	out["http_version"] = http_version(site)
	print(f"http_version : {out['http_version']}, {time.time()-t0:.2f} s; ", end="")

	t0 = time.time()
	out["answer_malformed"] = answer_malformed(site)
	print(f"answer_malformed : {out['answer_malformed']}, {time.time()-t0:.2f} s; ", end="")

	t0 = time.time()
	out["ssl_cipher"] = ssl_cipher(site)
	print(f"ssl_cipher : {out['ssl_cipher']}, {time.time()-t0:.2f} s")

	print(out)

	if STORE == "CSV":
		out_file = open(out_path, "a")
		line = f"{out['site']},{out['http_version']},{out['answer_malformed']},{out['ssl_cipher']}\n"
		out_file.write(line)
		out_file.close()

	elif STORE == "MONGODB":
		mongo_db.sites.insert_one(out)

if STORE == "CSV" and PURGE_DB:
	out_file = open(out_path, "w")
	out_file.write("site,http_version,answer_malformed,ssl_cipher\n")
	out_file.close()


with zipfile.ZipFile(zip_file) as zipopen:
	with zipopen.open("top-1m.csv") as f:
		# CSV file opened
		
		line = f.readline()
		while line:
			site = line.decode("utf-8").strip().split(",")[1]
			process(site)

			line = f.readline()
