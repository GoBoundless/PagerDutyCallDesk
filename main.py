import json
import textwrap
import logging
from urllib2 import Request, urlopen, URLError, HTTPError
import urllib
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

SERVICE_KEY = "d1768578cf9c445b8c3105e0578bd7ef"

def details(request):
  result = {}
  for param in ["Caller", "CallerName", "CallerCity", "CallerState", "CallerZip", "CallerCountry", "RecordingDuration", "RecordingUrl", "TranscriptionText"]:
    result[param] = request.get(param)
  return result

def caller_identity(request):
  "%s (%s)"%(request.get("Caller"), request.get("CallerName"))

def create_event(event):
  try:
    r = Request("https://events.pagerduty.com/generic/2010-04-15/create_event.json", json.dumps(event))
    results = urlopen(r)
    logging.info(event)
    logging.info(results)
  except HTTPError, e:
    logging.warn( e.code )
  except URLError, e:
    logging.warn(e.reason)

class CallHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write(textwrap.dedent(
      """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
        <Response>
          <Say>Thank you for contacting the Boundless emergency support hotline. To reach the on-call engineer, please leave a message at the beep.</Say>
          <Record action=\"/record\" transcribeCallback=\"/transcribe\" method=\"GET\"/>
          <Say>I did not receive a recording</Say>
        </Response>
      """
    ))
    logging.info('Recieved CALL ' + self.request.query_string)

class RecordHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write(textwrap.dedent(
      """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
        <Response>
          <Say>Directing your message to the agent on call.</Say>
        </Response>
      """
    ))
    logging.info('Recieved RECORDING: ' + self.request.query_string)

    recUrl = self.request.get("RecordingUrl")
    recUrl = recUrl + '.mp3'

    if (recUrl):
      create_event({
        'service_key': SERVICE_KEY,
        'event_type': 'trigger',
        'incident_key': self.request.get("RecordingSid"),
        'description': "Incoming call from %s"%(caller_identity(self.request)),
        'client': caller_identity(self.request),
        'client_url': recUrl,
        'details': details(self.request),
        'contents': [
          {
            'type': 'link',
            'href': recUrl,
            'text': 'Recording'
          }
        ]
      })

class TranscribeHandler(webapp.RequestHandler):
  def post(self):
    self.response.out.write("Ok")
    logging.info('Recieved TRANSCRIPTION: ' + self.request.query_string)

    create_event({
      'service_key': SERVICE_KEY,
      'event_type': 'trigger',
      'incident_key': self.request.get("RecordingSid"),
      'description': self.request.get("TranscriptionText"),
      'client': caller_identity(self.request),
      'details': details(self.request),
    })

def main():
  application = webapp.WSGIApplication([
                                    ('/', CallHandler),
                                    ('/record', RecordHandler),
                                    ('/transcribe', TranscribeHandler)],
                                       debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()