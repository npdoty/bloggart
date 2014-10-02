import logging
import webapp2
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.ext.webapp.util import run_wsgi_app
import config
import models
import urllib

class DraftMessageHandler(InboundMailHandler):
  def receive(self, mail_message):
    logging.info("Received a message from: " + mail_message.sender)
    
    received_address = urllib.unquote(self.request.path.split('/_ah/mail/')[1])
    if received_address.split('@')[0] != config.secrets.email_alias:
      logging.error('Message received at unapproved address: %s' % received_address)
      return

    content_type, body = mail_message.bodies().next()
    

application = webapp2.WSGIApplication([DraftMessageHandler.mapping()], debug=True)

# boilerplate below is needed though I'm honestly not sure why

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
