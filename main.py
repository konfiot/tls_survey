#!/usr/bin/python3
# coding: utf-8

import zipfile
import requests
import io

import process

DISTRIBUTE = True # Distribute tasks using redis

PURGE_DB = True # Reset DB on startup
STORE = process.STORE
out_path = process.out_path # For CSV store

start_file = "https://s3.amazonaws.com/alexa-static/top-1m.csv.zip"

q = None

if DISTRIBUTE:
	from redis import Redis
	from rq import Queue
	q = Queue(connection=Redis())

zip_file = io.BytesIO(requests.get(start_file).content)

if PURGE_DB:
	if STORE == "MONGODB":
		import pymongo
		mongo_client = pymongo.MongoClient()
		mongo_db = mongo_client.tls_survey
		mongo_db.sites.drop()

	if STORE == "CSV":
		self.out_file = open(out_path, "a")
		out_file.write("site,http_version,answer_malformed,ssl_cipher\n")
		out_file.close()


with zipfile.ZipFile(zip_file) as zipopen:
	with zipopen.open("top-1m.csv") as f:
		# CSV file opened
		
		line = f.readline()
		while line:
			site = line.decode("utf-8").strip().split(",")[1]
			if DISTRIBUTE:
				result = q.enqueue(process.do_job, site)
			else:
				process.do_job(site)

			line = f.readline()
