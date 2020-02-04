#!/usr/bin/python3
# coding: utf-8

import zipfile
import requests
import io
from hyper.contrib import HTTP20Adapter
import hyper
import random
import string

from M2Crypto import SSL

# For error handling
import socket

start_file = "https://s3.amazonaws.com/alexa-static/top-1m.csv.zip"
out_path = 'out.csv'

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
	except:
		return "ERROR"
	try:
		return str(r.status_code) + "IN" if random in r.content.decode(r.encoding) else str(r.status_code)
	except UnicodeDecodeError:
		return str(r.status_code)

def ssl_cipher(site):
	ctx = SSL.Context()
	s = SSL.Connection(ctx)

	s.postConnectionCheck = None
	try:
		s.connect((site, 443))
	except TimeoutError:
		return "TIMEOUT"
	except:
		return "ERROR"

	if s.get_state() == "SSLOK ":
		c = s.get_cipher()
		cp = c.name()
		return cp
	s.close()




def process(site, out_file):
	print(f"Processing site : {site}")
	out = [site]

	out.append(http_version(site))
	out.append(answer_malformed(site))
	out.append(ssl_cipher(site))

	line = ",".join(out) + "\n"

	print(line)

	out_file.write(line)


with open(out_path, "a") as out_file:
	with zipfile.ZipFile(zip_file) as zipopen:
		with zipopen.open("top-1m.csv") as f:
			# CSV file opened
			
			line = f.readline()
			while line:
				site = line.decode("utf-8").strip().split(",")[1]
				process(site, out_file)

				line = f.readline()
