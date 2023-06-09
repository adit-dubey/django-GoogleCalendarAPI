from django.shortcuts import render
from django.shortcuts import redirect

from rest_framework.decorators import api_view
from rest_framework.response import Response

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import os


os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

CLIENT_SECRETS_FILE = "C:/Users/aditd/GoogleCalendar/Calendar/credentials.json"
SCOPES = ['https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/calendar.readonly',
          'https://www.googleapis.com/auth/calendar.events.readonly']
REDIRECT_URL = 'http://127.0.0.1:8080/GC/v1/calendar/redirect'



API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'


@api_view(['GET'])
def GoogleCalendarInitView(request):
   
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    flow.redirect_uri = REDIRECT_URL

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',)
    request.session['state'] = state

    return Response({"authorization_url": authorization_url})


@api_view(['GET'])
def GoogleCalendarRedirectView(request):
    state = request.session['state']
    print(state)

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    
    flow.redirect_uri = REDIRECT_URL
    authorization_response = request.get_full_path()

    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)

    # Check if credentials are in session
    if 'credentials' not in request.session:
        return redirect('v1/calendar/init')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(**request.session['credentials'])

    # Use the Google API Discovery Service to build client libraries, IDE plugins,
    # and other tools that interact with Google APIs.
    # The Discovery API provides a list of Google APIs and a machine-readable "Discovery Document" for each API
    service = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # Returns the calendars on the user's calendar list
    calendar_list = service.calendarList().list().execute()

    # Getting user ID which is his/her email address
    calendar_id = calendar_list['items'][1]['id']
    # calendar_list['items'][0] = For Public events
    # calendar_list['items'][0] = For Private events
    
    # Getting all events associated with a user ID (email address)
    events  = service.events().list(calendarId=calendar_id).execute()

    events_list_append = []
    if not events['items']:
        print('No data found.')
        return Response({"message": "No data found or user credentials invalid."})
    else:
        for events_list in events['items']:
            events_list_append.append(events_list)
            return Response({"events": calendar_list,"events1":events})
    return Response({"error": "calendar event aren't here"})


def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}