import json
import logging
from urllib2 import Request, urlopen, URLError, HTTPError
import urllib
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

SERVICE_KEY = "d1768578cf9c445b8c3105e0578bd7ef"

class CallHandler(webapp.RequestHandler):
  def get(self):
    response = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
      "<Response><Say>Thank you for contacting the  Boundless emergency support hotline. Leave a message at the beep.</Say>"
      "<Record action=\"http://pagerdutyinboundcalls.appspot.com/record\" method=\"GET\"/>"
      "<Say>I did not receive a recording</Say></Response>")
    self.response.out.write(response)
    logging.info('Recieved CALL ' + self.request.query_string)

class RecordHandler(webapp.RequestHandler):
  def get(self):
    response = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response><Say>Directing your message to the agent on call.</Say></Response>")
    self.response.out.write(response)
    logging.info('Recieved RECORDING: ' + self.request.query_string)
    recUrl = self.request.get("RecordingUrl")
    phonenumber = self.request.get("From")

    logging.info('Recieved RECORDING ' + recUrl)
    if(recUrl):
      logging.info('Found recording!')
      recUrl = recUrl + '.mp3' # There's better support for URLs that include the .mp3
    else:
      recUrl = ""
      phonenumber = ""

    # Obviously use your own key:
    incident = {
      'service_key': SERVICE_KEY,
      'event_type': 'trigger',
      'incident_key': phonenumber,
      'description': "Incoming call from %s"%(phonenumber),
      'client_url': 'https://pagerdutyinboundcalls.appspot.com/',
      'details': self.request.arguments(),
      'contents': [
        {
          'type': 'link',
          'href': recUrl,
          'text': 'Message'
        }
      ]
    }

    try:
      r = Request("https://events.pagerduty.com/generic/2010-04-15/create_event.json", json.dumps(incident, indent=4))
      results = urlopen(r)
      logging.info(incident)
      logging.info(results)
    except HTTPError, e:
      logging.warn( e.code )
    except URLError, e:
      logging.warn(e.reason)   

# A somewhat descriptive index page
class IndexHandler(webapp.RequestHandler):
  def get(self):
    response = ("<html><h1>Trigger a <a href='http://www.pagerduty.com'>PagerDuty</a> incident from a phone call</h1><ul>"
      "<li><a href='http://blog.pagerduty.com/2012/02/triggering-an-alert-from-a-phone-call'>About</a>"
      "<li><a href='https://github.com/eurica/PagerDutyCallDesk/'>GitHub page</a>"
      "<li><a href='/call'>/call</a> (returns XML)"
      "<li><a href='/record?RecordingUrl=http%3A%2F%2Fapi.twilio.com%2F2010-04-01%2FAccounts%2FACfdf710462c058abf3a987f393e8e9bc8%2FRecordings%2FRE6f523cd7734fa86e56e5ef0ea5ffd4cf'>/record</a> (test with 'Hey this is Jim...')"
      "</ul>Remember to change the application identifier and the service API key, or else you'll just alert me :)</html>")
    self.response.out.write(response)

def main():
  application = webapp.WSGIApplication([
                                    ('/call', CallHandler),
                                    ('/record', RecordHandler),
                                    ('/', IndexHandler)],
                                       debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()