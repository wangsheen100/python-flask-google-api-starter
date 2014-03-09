#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
from apiclient.discovery import build_from_document, build
import httplib2
import random
from oauth2client import client
from oauth2client.client import OAuth2WebServerFlow


from flask import jsonify

from flask import Flask, render_template, session, request, redirect, url_for, abort

CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'

app = Flask(__name__)


@app.route('/login')
def login():
  flow = OAuth2WebServerFlow(client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scope='https://www.googleapis.com/auth/calendar',
    redirect_uri='http://localhost:5000/oauth2callback',
    approval_prompt='force',
    access_type='offline')

  auth_uri = flow.step1_get_authorize_url()
  return redirect(auth_uri)

@app.route('/signout')
def signout():
  del session['credentials']
  session['message'] = "You have logged out"

  return redirect(url_for('index'))

@app.route('/oauth2callback')
def oauth2callback():
  code = request.args.get('code')
  if code:
    # exchange the authorization code for user credentials
    flow = OAuth2WebServerFlow(CLIENT_ID,
      CLIENT_SECRET,
      "https://www.googleapis.com/auth/calendar")
    flow.redirect_uri = request.base_url
    try:
      credentials = flow.step2_exchange(code)
    except Exception as e:
      print "Unable to get an access token because ", e.message

    # store these credentials for the current user in the session
    # This stores them in a cookie, which is insecure. Update this
    # with something better if you deploy to production land
    session['credentials'] = credentials.to_json()

  return redirect(url_for('index'))

@app.route('/')
def index():

  try:
    credentials = client.Credentials.new_from_json(session['credentials'])

  except KeyError:
    credentials = None

  if credentials == None:
    return redirect(url_for('login'))

  http = httplib2.Http()
  http = credentials.authorize(http)
  service = build("calendar", "v3", http=http)
  calendar_list = service.calendarList().list().execute()


  page_token = None
  while True:
    mycalendar_list = service.calendarList().list(pageToken=page_token).execute()
    for calendar_list_entry in mycalendar_list['items']:
      print calendar_list_entry['summary']
      epage_token = None
      while True:
        events = service.events().list(calendarId=calendar_list_entry['id'], pageToken=epage_token).execute()
        for event in events['items']:
          try:
            print event['summary']
          except KeyError:
            print "no summary here"
            continue
            
        epage_token = events.get('nextPageToken')
        if not epage_token:
          break

        page_token = mycalendar_list.get('nextPageToken')
    if not page_token:
      break


  for calendar_list_entry in calendar_list['items']:
    print calendar_list_entry['id']
    service.events()
  #print calendar_list 

  return render_template("index.html", calendar_list=events)

if __name__ == '__main__':
  app.secret_key = 'hello world'
  app.run(host='0.0.0.0')
