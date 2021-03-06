# __BEGIN_LICENSE__
# Copyright (C) 2008-2010 United States Government as represented by
# the Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# __END_LICENSE__

# suppress messages about defining attributes outside constructor
# pylint: disable=W0201

import time
import datetime

from django.db import models
from django.contrib.auth.models import User
# from geocamMemo import authentication


class GeocamMessage(models.Model):
    class Meta:
        abstract = True

    server_timestamp = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, related_name="%(app_label)s_%(class)s_set")
    content = models.TextField(max_length=1024)
    # content_timestamp: no auto_add_now in case we go back to versioned message model
    content_timestamp = models.DateTimeField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    altitude = models.FloatField(null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    heading = models.FloatField(null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)
    position_timestamp = models.DateTimeField(null=True, blank=True)

    def get_date_string(self):
        return self.content_timestamp.strftime("%m/%d/%y %H:%M:%S")

    def get_date_timestamp(self):
        return int(time.mktime(self.content_timestamp.timetuple())) * 1000  # * 1000 for java timestamp

    def get_author_string(self):
        return get_user_string(self.author)

    def title(self):
        return self.content[:16] + "..." if len(self.content) > 19 else self.content

    def has_geolocation(self):
        return bool(self.latitude != None and self.longitude != None)


class MemoMessage(GeocamMessage):
    def __unicode__(self):
        return "Memo from %s on %s: %s" % (self.author.username, self.content_timestamp, self.content)

    def getJson(self):
        return  dict(
                    messageId=self.pk,
                    userId=self.author.pk,
                    authorUsername=self.author.username,
                    authorFullname=self.get_author_string(),
                    content=self.content,
                    contentTimestamp=self.get_date_timestamp(),
                    latitude=self.latitude,
                    longitude=self.longitude,
                    accuracy=self.accuracy,
                    hasGeolocation=bool(self.has_geolocation()))

    def getKml(self):
        if not self.has_geolocation():
            return ''
        fields = vars(self).copy()
        fields['authorFullname'] = self.get_author_string()
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
      <div><span style="color: #888;">Date:</span> %(content_timestamp)s</div>
      <div><span style="color: #888;">Position:</span> %(latitude).6f, %(longitude).6f</div>
      <div style="margin: 20px;">%(content)s</div>
    ]]>
  </description>
  <styleUrl>#memoMarker</styleUrl>
</Placemark>
""" % fields)

    @staticmethod
    def fromJson(messageDict):
        message = MemoMessage()
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
    def getMessages(author=None):
        """ Message Listing Rules:

        If no author is specified: all messages are displayed
        If author is specified: all messages are displayed from author
        """

        if (author is None):
            # all messages are displayed
            messages = MemoMessage.objects.all()
        else:
            # messages displayed are from author:
            messages = MemoMessage.objects.filter(author__username=author.username)
        return messages.order_by('-content_timestamp')


def get_user_string(user):
    if user.first_name and user.last_name:
        if user.last_name in ('group', 'Group'):
            return user.first_name
        else:
            return (user.first_name + " " + user.last_name)
    else:
        return (user.username)

User.full_name = property(lambda u: get_user_string(u))  # pylint: disable=W0108
