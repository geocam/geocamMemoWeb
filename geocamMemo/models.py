# __BEGIN_LICENSE__
# Copyright (C) 2008-2010 United States Government as represented by
# the Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# __END_LICENSE__

from django.db import models
from django.contrib.auth.models import User
import json
import time, datetime
# from geocamMemo import authentication

class GeocamMessage(models.Model):
    class Meta:
        abstract = True
    
    server_timestamp = models.DateTimeField(auto_now_add = True)
    author = models.ForeignKey(User, related_name="%(app_label)s_%(class)s_set")
    content = models.TextField(max_length=1024)
    # removed auto_add_now from content_timestamp since revisions are also instances in the 
    # same table and we don't overwrite this timestamp on an edit
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
        return int(time.mktime(self.content_timestamp.timetuple())) * 1000 # * 1000 for java timestamp
    
    def get_author_string(self):
        return get_user_string(self.author)
    
    def title(self):
        return self.content[:16] + "..." if len(self.content) > 19 else self.content
          
    def has_geolocation(self):
        return bool(self.latitude != None and self.longitude != None)

    pass

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
                    hasGeolocation=bool(self.has_geolocation()) )
    
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
        
        If no author is specified: all messages are displayed (latest revisions)
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
        return (user.first_name + " " + user.last_name)
    else:
        return (user.username)

User.full_name = property(lambda u: get_user_string(u))

