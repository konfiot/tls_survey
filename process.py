from hyper.contrib import HTTP20Adapter
import hyper
import random
import string
import time
import requests
import sys
import socket
import ssl
import traceback


STORE = "MONGODB" #CSV, MONGODB
out_path = 'out.csv' # For CSV store

if STORE == "MONGODB":
	import pymongo

def randomString(stringLength=10):
	letters = string.ascii_lowercase
	return ''.join(random.choice(letters) for i in range(stringLength))

def do_job(site):
	process = Process()
	process.process(site)


class Process:
	def __init__(self):
		if STORE == "MONGODB":
			mongo_client = pymongo.MongoClient()
			self.mongo_db = mongo_client.tls_survey

		if STORE == "CSV":
			self.out_file = open(out_path, "a")
			out_file.write("site,http_version,answer_malformed,ssl_cipher\n")

	def http_version(self, site):
		s = requests.Session()
		s.mount("https://" + site, HTTP20Adapter())
		try:
			r = s.get("https://" + site)
		except (socket.timeout, requests.exceptions.ConnectionError, TimeoutError):
			return "TIMEOUT"
		except KeyboardInterrupt:
			exit(-1)
		except:
			_,e,t = sys.exc_info()
			print("Unexpected error:", e, "Traceback : ")
			traceback.print_tb(t)
			return "ERROR"

		if isinstance(r.raw,  hyper.HTTP20Response):
			return "2"
		elif isinstance(r.raw,  hyper.HTTP11Response):
			return "1.1"
		else:
			return "FAIL"

	def answer_malformed(self, site):
		random = randomString(50)
		try:
			r = requests.get("https://" + site + "/" + random)
		except (TimeoutError, requests.exceptions.ConnectionError):
			return "TIMEOUT"
		except KeyboardInterrupt:
			exit(-1)
		except:
			_,e,t = sys.exc_info()
			print("Unexpected error:", e, "Traceback : ")
			traceback.print_tb(t)
			return "ERROR"

		try:
			return str(r.status_code) + "IN" if random in r.content.decode(r.encoding) else str(r.status_code)
		except (TypeError, UnicodeDecodeError):
			return str(r.status_code)

	def ssl_cipher(self, site):
		context = ssl.create_default_context()

		try:
			sock = socket.create_connection((site, 443))
			ssock = context.wrap_socket(sock, server_hostname=site)
		except TimeoutError:
			return "TIMEOUT"
		except KeyboardInterrupt:
			exit(-1)
		except:
			_,e,t = sys.exc_info()
			print("Unexpected error:", e, "Traceback : ")
			traceback.print_tb(t)
			return "ERROR"
		c, v, l = ssock.cipher()
		ssock.close()
		return c




	def process(self, site):
		print(f"Processing site : {site} ; ", end="")
		out = {"site": site}

		t0 = time.time()
		out["http_version"] = self.http_version(site)
		print(f"http_version : {out['http_version']}, {time.time()-t0:.2f} s; ", end="")

		t0 = time.time()
		out["answer_malformed"] = self.answer_malformed(site)
		print(f"answer_malformed : {out['answer_malformed']}, {time.time()-t0:.2f} s; ", end="")

		t0 = time.time()
		out["ssl_cipher"] = self.ssl_cipher(site)
		print(f"ssl_cipher : {out['ssl_cipher']}, {time.time()-t0:.2f} s")

		print(out)

		if STORE == "CSV":
			line = f"{out['site']},{out['http_version']},{out['answer_malformed']},{out['ssl_cipher']}\n"
			self.out_file.write(line)

		elif STORE == "MONGODB":
			self.mongo_db.sites.insert_one(out)
