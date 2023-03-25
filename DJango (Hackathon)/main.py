import os
import signal
import json
import requests
import base64
import sys

sys.path.append('../Custom Methods VI')
import Connection

from flask import Flask, send_file, request, render_template, redirect, Response

import FileSystem


def onkill(sig, frame):
	print('\n\033[38;2;255;0;0mServer Stopped\033[0m')
	os.kill(os.getpid(), signal.SIGTERM)


def open_read_json_file(file: FileSystem.File) -> dict:
	with file.open('r') as f:
		decoder = json.JSONDecoder()
		return decoder.decode(f.read())


def get_website_logo(url: str) -> bytes:
	res = requests.get(f'https://logo.clearbit.com/{url}')
	return base64.b64encode(res.content)


signal.signal(signal.SIGINT, onkill)

app = Flask(__name__, static_folder='main/static', template_folder='main/templates')


@app.route('/', methods=['GET'])
def index():
	return render_template('index.html')


@app.route('/questionnaire', methods=['GET'])
def questionnaire():
	return render_template('questionnaire.html')


@app.route('/get_disciplines', methods=['POST'])
def get_disciplines():
	return Response(json.encoder.JSONEncoder().encode({'keys': list(DISCIPLINES.keys()), 'names': [' '.join(d.capitalize() for d in x.split('_')) for x in DISCIPLINES.keys()]}), 200)


@app.route('/get_select_disciplines', methods=['POST'])
def get_select_disciplines():
	targets = json.decoder.JSONDecoder().decode(request.data.decode())['targets']
	output = {}

	for target in targets:
		if target in DISCIPLINES:
			output[target] = json.encoder.JSONEncoder().encode(DISCIPLINES[target])
		else:
			return Response('Target discipline not found', status=404)

	return Response(json.encoder.JSONEncoder().encode(output), status=200)


@app.route('/get_web_logo', methods=['POST'])
def get_web_logo():
	data = json.decoder.JSONDecoder().decode(request.data.decode())
	discipline = data['discipline']
	company = data['company']

	if discipline not in DISCIPLINES:
		return Response('Target discipline not found', status=404)
	elif company not in DISCIPLINES[discipline]['companies']:
		return Response('Target company not found', status=404)
	else:
		return get_website_logo(DISCIPLINES[discipline]['companies'][company]['url'])


if __name__ == '__main__':
	# [ Start Server ] #
	JSON_FILE = FileSystem.File("data/disciplines.json")

	if not JSON_FILE.exists():
		print('\n\033[38;2;255;0;0mMissing JSON file, server start INTERRUPT\033[0m')
	else:
		DISCIPLINES = open_read_json_file(JSON_FILE)
		SOCKETIO = Connection.FlaskSocketioServer(app)
		print('\n\033[38;2;0;255;0mServer Started [0.0.0.0:8080]\033[0m')
		SOCKETIO.listen('0.0.0.0', 8080)

