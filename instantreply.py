#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import httplib2
import os
import sys
import email
import base64
import unicodedata
import string
from time import strftime
from apiclient import discovery
from apiclient import errors
from quickstart import get_credentials
from datetime import datetime, timedelta
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes

# Date settings
today     = datetime.now()
yesterday = today - timedelta(days=1)
my_email  = os.environ["MY_EMAIL"]

# file settings
input_file = 'instant_reply_messagesid.txt'
sender     = os.environ["MY_EMAIL"]#os.environ["EMAIL_ADDRESS"]

# ----------------------------------------------------------------------
# Mark message as read
# ----------------------------------------------------------------------
def MarkRead(service, user_id, message_id):
    unread = {"removeLabelIds": ["UNREAD"]}
    service.users().messages().modify(userId=user_id,
                                      id=message_id,
                                      body=unread).execute()

# ----------------------------------------------------------------------
# Return some random excuse
# ----------------------------------------------------------------------
def GetExcuse():
    import random
    reasons = [
        'Ill be there',
        'See you then',
        '11:00 as usual'
    ]
    return random.choice(reasons)

# ----------------------------------------------------------------------
# Get email address from sender.
# TODO: reply to original email and thread the email
#       From the docs:
#       If you're trying to send a reply and want the email to thread, make sure that:
#
#           The Subject headers match
#           The References and In-Reply-To headers follow the RFC 2822 standard.
# ----------------------------------------------------------------------
def GetSender(service, user_id, today, week_counter):
    try:
        message_ids = open(input_file).readlines()
        msg_body_list = []
        for i in range(10):
            message = service.users().messages().get(  userId=user_id,
                                                       id=message_ids[i].rstrip(),
                                                       format='raw').execute()

            msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
            mime_msg = email.message_from_string(msg_str)

            if ('UNREAD' in message['labelIds'][0]) and (sender in mime_msg['From']):
                excuse = "Ok cool, " + GetExcuse()
                created_message = CreateMessage(my_email, sender, "Change subject later", excuse)
                SendMessage(service, sender, created_message)
                MarkRead(service, user_id, message_ids[i].rstrip())

    except errors.HttpError, error:
        print('An error occurred: %s' % error)

# ----------------------------------------------------------------------
# Create a message then send
# ----------------------------------------------------------------------
def CreateMessage(my_email, to, subject, message_text):
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = my_email
  message['subject'] = subject
  return {'raw': base64.urlsafe_b64encode(message.as_string())}

# ----------------------------------------------------------------------
# Send message
# ----------------------------------------------------------------------
def SendMessage(service, user_id, message):
  try:
    message = (service.users().messages().send(userId=user_id,
                                               body=message).execute())
    print('Message Id: %s' % message['id'])
    print("Message sent at " + strftime("%a, %d %b %Y %H:%M:%S"))
    return message
  except errors.HttpError, error:
    print('An error occurred: %s' % error)

# ----------------------------------------------------------------------
# Get message IDs
# ----------------------------------------------------------------------
def GetMessageIds(today, yesterday, service, user_id):
    try:
        # Filter out messages based on a 1 day time span
        query = "before: {0} after: {1}".format(today.strftime('%Y/%m/%d'),
                                                yesterday.strftime('%Y/%m/%d'))

        # Log all captured data as message IDs into a text file.
        response = service.users().messages().list( userId=user_id,
                                                    q=query).execute()
        msg_id_file = open(input_file, 'w')
        for i in range(len(response['messages'])):
            msg_id_file.write(response['messages'][i]['id'] + '\n')

    except errors.HttpError, error:
        print('An error occurred: %s' % error)

# ----------------------------------------------------------------------
# Main program
# ----------------------------------------------------------------------
def main():
    print("Today     : ", today)
    print("yesterday : ", yesterday, '\n')

    # Week counter
    week_counter = 0
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    results = service.users().labels().list(userId=my_email).execute()
    GetMessageIds(today, yesterday, service, my_email)
    GetSender(service, my_email, today, week_counter)

if __name__ == '__main__':
    main()
