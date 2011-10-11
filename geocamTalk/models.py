# __BEGIN_LICENSE__
# Copyright (C) 2008-2010 United States Government as represented by
# the Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# __END_LICENSE__

# suppress bogus messages about missing class members
# suppress messages about defining class members outside constructor
# pylint: disable=E1101,W0201

import httplib
import urllib
import datetime

from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q, Count

from geocamMemo.models import GeocamMessage, get_user_string
from geocamMemo import settings


class TalkUserProfile(models.Model):
    user = models.ForeignKey(User, related_name='profile')
    last_viewed_mymessages = models.IntegerField(default=0)
    registration_id = models.CharField(max_length=128)

    def getUnreadMessageCount(self):
        return TalkMessage.getMessages(self.user).filter(
                                        pk__gt=self.last_viewed_mymessages).count()

User.profile = property(lambda u: TalkUserProfile.objects.get_or_create(user=u)[0])


class TalkMessage(GeocamMessage):
    """
    This is the data model for Memo application messages
    """
    # TODO - add time to filename location
    audio_file = models.FileField(null=True, blank=True, upload_to='geocamTalk/audio/%Y/%m/%d')  # "%s-audio" % (GeocamMessage.author))

    def __unicode__(self):
        try:
            s = "Talk message from %s to %s on %s: %s" % (self.author.username, self.recipients.all(), self.content_timestamp, self.content)
        except:  # pylint: disable=W0702
            s = "Talk message from %s on %s: %s" % (self.author.username, self.content_timestamp, self.content)
        return s

    recipients = models.ManyToManyField(User, null=True, blank=True, related_name="received_messages")

    def getKml(self):
        if not self.has_geolocation():
            return ''
        fields = vars(self).copy()
        fields['authorFullname'] = self.get_author_string()
        fields['recipients'] = ', '.join([get_user_string(r) for r in self.recipients.all()])
        if self.content:
            fields['name'] = '<name>' + self.content[:10] + '...</name>'
        else:
            fields['name'] = ''
        return ("""
<Placemark>
  <Point>
    <coordinates>%(longitude).6f,%(latitude).6f</coordinates>
  </Point>
  %(name)s
  <description>
    <![CDATA[
      <div><span style="color: #888;">Author:</span> %(authorFullname)s</div>
      <div><span style="color: #888;">Recipients:</span> %(recipients)s</div>
      <div><span style="color: #888;">Date:</span> %(content_timestamp)s</div>
      <div><span style="color: #888;">Position:</span> %(latitude).6f, %(longitude).6f</div>
      <div style="margin: 20px;">%(content)s</div>
    ]]>
  </description>
  <styleUrl>#talkMarker</styleUrl>
</Placemark>
""" % fields)

    def getJson(self):
        return  dict(messageId=self.pk,
                     userId=self.author.pk,
                     authorUsername=self.author.username,
                     authorFullname=self.get_author_string(),
                     recipients=[r.username for r in self.recipients.all()],
                     content=self.content,
                     contentTimestamp=self.get_date_timestamp(),
                     latitude=self.latitude,
                     longitude=self.longitude,
                     accuracy=self.accuracy,
                     audioUrl=self.get_audio_url(),
                     hasGeolocation=bool(self.has_geolocation()))

    @staticmethod
    def fromJson(messageDict):
        message = TalkMessage()
        if "content" in messageDict:
            message.content = messageDict["content"]
        if "contentTimestamp" in messageDict:
            message.content_timestamp = datetime.datetime.fromtimestamp(float(messageDict["contentTimestamp"]) / 1000)
        if "latitude" in messageDict:
            message.latitude = messageDict["latitude"]
        if "longitude" in messageDict:
            message.longitude = messageDict["longitude"]
        if "accuracy" in messageDict:
            message.accuracy = messageDict["accuracy"]
        if "userId" in messageDict:
            message.author_id = messageDict["userId"]
        return message

    @staticmethod
    def getMessages(recipient=None, author=None):
        """ Message Listing Rules:

        If no users are specified: all messages are displayed
        If only author is specified: all messages are displayed from author
        If only recipient is specified: messages displayed are broadcast + from OR to recipient
        If both recipient AND author are specified: messages displayed are braodcast + from author AND to recipient

        Note: a broadcast message is a message with no recipients
        """
        if (recipient is None and author is None):
            # all messages are displayed
            messages = TalkMessage.objects.all()
        elif (recipient is None and author is not None):
            # messages displayed are from author:
            messages = TalkMessage.objects.filter(author__username=author.username)
        elif (recipient is not None and author is None):
            # messages displayed are broadcast + from OR to recipient:
            messages = TalkMessage.objects.annotate(num_recipients=Count('recipients')).filter(Q(num_recipients=0) | Q(recipients__username=recipient.username) | Q(author__username=recipient.username)).distinct()
        else:
            # messages displayed are braodcast + from author AND to recipient
            messages = TalkMessage.objects.annotate(num_recipients=Count('recipients')).filter(Q(num_recipients=0) | Q(recipients__username=recipient.username)).filter(author__username=author.username).distinct()
        return messages.order_by('-content_timestamp')

    @staticmethod
    def getLargestMessageId():
        return TalkMessage.objects.all().order_by('-pk')[0].pk

    def has_audio(self):
        return bool(self.audio_file != '')

    def push_to_phone(self, pushToSender=True):
        push_recipients = self.recipients.all()
        if(push_recipients.count() == 0):
            push_recipients = User.objects.all()

        for user in push_recipients:
            if(user.profile.registration_id):
                if(pushToSender == True or user.pk != self.author.pk):
                    # we need the following params set per http://code.google.com/android/c2dm/index.html#push
                    params = urllib.urlencode({
                             'registration_id': user.profile.registration_id,
                             'collapse_key': "message" + str(self.pk),
                             'data.message_id': str(self.pk),
                             'delay_when_idle': 'TRUE',
                             })

                    # need the following headers set per http://code.google.com/android/c2dm/index.html#push
                    headers = {"Content-Type": "application/x-www-form-urlencoded",
                               "Content-Length": len(params),
                               "Authorization": "GoogleLogin auth=" + settings.GEOCAM_MEMO_GOOGLE_C2DM_TOKEN
                               }

                    # NOW SEND THE REQUEST TO GOOGLE SERVERS
                    # first we need an https connection that ignores the certificate (for now)
                    httpsconnection = httplib.HTTPSConnection("android.apis.google.com", 443)
                    httpsconnection.request("POST", "/c2dm/send", params, headers)

    def get_audio_url(self):
        if self.audio_file:
            return self.audio_file.url
        else:
            return None
