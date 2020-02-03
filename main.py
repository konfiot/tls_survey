#!/usr/bin/python3
# coding: utf-8

import zipfile
import requests
import io
from hyper.contrib import HTTP20Adapter
import hyper

# For error handling
import socket

start_file = "https://s3.amazonaws.com/alexa-static/top-1m.csv.zip"
out_path = 'out.csv'

zip_file = io.BytesIO(requests.get(start_file).content)

def http_version(site):
	s = requests.Session()
	s.mount("https://" + site, HTTP20Adapter())
	try:
		r = s.get("https://" + site)
	except socket.timeout:
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
	pass


def process(site, out_file):
	print(f"Processing site : {site}")
	out = [site]

	out.append(http_version(site))

	line = ",".join(out) + "\n"
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
