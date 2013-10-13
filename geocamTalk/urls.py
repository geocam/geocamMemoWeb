# __BEGIN_LICENSE__
# Copyright (C) 2008-2010 United States Government as represented by
# the Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# __END_LICENSE__

import django.views.generic.simple
from django.conf.urls import *  # pylint: disable=W0401
from django.views.generic import RedirectView

urlpatterns = patterns('geocamTalk.views',
    url(r'^$', RedirectView.as_view(url='messages'),
        {'permanent': False},
        name='geocamTalk_home'),
                       
    url(r'^register$', 'register',
         name='geocamTalk_register_c2dm'),

    url(r'^unregister$', 'unregister',
         name='geocamTalk_unregister_c2dm'),

    url(r'^messages/create.json$', 'create_message_json',
         name='geocamTalk_create_message_json'),

    url(r'^messages/create$', 'create_message',
         name='geocamTalk_create_message'),

    url(r'^messages/clear$', 'clear_messages',
         name='geocamTalk_clear_messages'),

    url(r'^messages/details/(?P<message_id>\d+).json$', 'message_details_json',
        name="geocamTalk_message_details_json"),

    url(r'^messages/details/(?P<message_id>\d+)$', 'message_details',
        name="geocamTalk_message_details"),

    url(r'^messages/(?P<recipient_username>[^ ]+)/(?P<author_username>[^ ]+).json$', 'feed_messages',
         name="geocamTalk_message_list_to_from_json"),

    url(r'^messages/(?P<recipient_username>[^ ]+).json$', 'feed_messages',
         name="geocamTalk_message_list_author_json"),

    url(r'^messages.json$', 'feed_messages',
         name="geocamTalk_message_list_all_json"),

    url(r'^messages/(?P<recipient_username>[^ ]+)/(?P<author_username>[^ ]+)$', 'message_list',
         name="geocamTalk_message_list_to_from"),

    url(r'^messages/(?P<recipient_username>[^ ]+)$', 'message_list',
         name="geocamTalk_message_list_to"),

    url(r'^messages/(?P<recipient_username>[^ ]+)$', 'message_list',
         name="geocamTalk_message_list_author"),

    url(r'^messages$', 'message_list',
         name="geocamTalk_message_list_all"),

    url(r'^map$', 'message_map',
        name="geocamTalk_message_map"),

    url(r'^messages\.kml$', 'feed_messages_kml',
        {'readOnly': True},
        name='geocamTalk_message_list_all_kml'),
)
