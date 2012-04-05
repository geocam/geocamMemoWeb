# __BEGIN_LICENSE__
# Copyright (C) 2008-2010 United States Government as represented by
# the Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# __END_LICENSE__

from django.test import TestCase
from django.contrib.auth.models import User
from geocamTalk.models import TalkMessage


class GeocamTalkListViewTest(TestCase):
    fixtures = ['demoUsers.json', 'demoTalkMessages.json']

    def testEnsureMyMessagesAreFilteredByAuthor(self):
        # arrange
        author = User.objects.all()[0]
        recipient = User.objects.all()[2]
        recipient_messages_from_author_or_broadcast = TalkMessage.getMessages(recipient, author)

        # act
        response = self.get_recipient_messages_response_filtered_by_author(recipient, author)

        # assert
        self.assertEqual(200, response.status_code)
        for m in recipient_messages_from_author_or_broadcast:
            self.assertContains(response, m.content)

    def testEnsureMyMessageListAuthorLinksPresent(self):
        author = User.objects.all()[2]
        recipient = User.objects.all()[1]
        #arrange
        recipient_messages = TalkMessage.getMessages(recipient, author)
        #act
        response = self.get_recipient_messages_response(recipient)

        #assert
        for _ in recipient_messages:
            link_to_recipient_msgs_from_author = 'href="FIXME/messages/%s/%s"' % (recipient.username, author.username)
            #print 'didnt find %s in %s' % (link_to_recipient_msgs_from_author, response)
            self.assertContains(response, link_to_recipient_msgs_from_author)

    def get_recipient_messages_response_filtered_by_author(self, recipient, author):
        self.client.login(username=recipient.username, password='geocam')
        response = self.client.get('FIXME/messages/%s/%s' % (recipient.username, author.username))
        return response

    def get_recipient_messages_response(self, recipient):
        self.client.login(username=recipient.username, password='geocam')
        response = self.client.get('FIXME/messages/' + recipient.username)
        return response

    def testMessageListAudioPresent(self):
        # arrange
        _author = User.objects.all()[2]
        recipient = User.objects.all()[1]
        response = self.get_recipient_messages_response(recipient)
        recipient_messages = TalkMessage.getMessages(recipient)
        # act
        geocount = 0
        for m in recipient_messages.all():
            if m.audio_file:
                geocount += 1
        # assert
        self.assertContains(response, 'class="media"', geocount)
        #self.assertContains(response, 'data-rel="dialog"', geocount)
