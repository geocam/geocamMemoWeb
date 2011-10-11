# __BEGIN_LICENSE__
# Copyright (C) 2008-2010 United States Government as represented by
# the Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# __END_LICENSE__

# suppress bogus messages about missing class members
# pylint: disable=E1101

from django.test import TestCase

from geocamMemo.models import MemoMessage


class GeocamMemoUrls(TestCase):
    fixtures = ['demoUsers.json', 'demoMemoMessages.json']

    def testMessageListUrl(self):
        #arrange
        path = "/memo/messages/"
        template = "geocamMemo/message_list.html"

        #act
        self.assertPathRequiresLoginAndUsesTemplate(path, template)

    def testMessagesJsonListUrl(self):
        #arrange
        path = "/memo/messages.json"

        #act
        guestResponse = self.getResponse(path)

        #assert
        self.assertEqual(403, guestResponse.status_code, "should display list. period")

    def testMessageJsonListUrl(self):
        #arrange
        pk = str(MemoMessage.latest.all()[0].pk)
        path = "/memo/messages/details/" + pk + ".json"

        #act
        guestResponse = self.getResponse(path)

        #assert
        self.assertEqual(200, guestResponse.status_code, "should display single message")

    def testMessageDetailsUrl(self):
        #arrange
        message = MemoMessage.latest.all()[0]
        path = "/memo/messages/details/" + str(message.pk)
        template = "geocamMemo/details.html"

        #act
        self.assertPathRequiresLoginAndUsesTemplate(path, template)

    def testMessageEditUrl(self):
        #arrange
        message = MemoMessage.latest.all()[0]
        path = "/memo/messages/edit/" + str(message.pk)
        template = "geocamMemo/edit_message_form.html"

        #act
        self.assertPathRequiresLoginAndUsesTemplate(path, template)

    def testMessageCreateUrl(self):
        #arrange
        path = "/memo/messages/create"
        template = "geocamMemo/message_form.html"

        #act
        self.assertPathRequiresLoginAndUsesTemplate(path, template)

    def testMessageCreateJSONFeed(self):
        #arrange
        path = "/memo/messages/create.json"

        #act
        guestResponse = self.client.post(path, {})

        #assert
        self.assertEqual(403, guestResponse.status_code, "Unauthorized access if not logged in")

    def testMessageListFilteredByUserUrl(self):
        #arrange
        path = "/memo/messages/root"
        template = "geocamMemo/message_list.html"

        #act
        self.assertPathRequiresLoginAndUsesTemplate(path, template)

    def testMessageDeleteUrl(self):
        #arrange
        message = MemoMessage.latest.all()[0]
        path = "/memo/messages/delete/" + str(message.pk)

        #act
        guestResponse = self.getResponse(path)
        self.login()
        memberResponse = self.getResponse(path)

        #assert
        self.assertEqual(302, guestResponse.status_code, "should redirect if not logged in")
        self.assertEqual(302, memberResponse.status_code, "should redirect upon deletion")

    def testMapViewUrl(self):
       #arrange
        path = "/memo/map"
        template = "geocamMemo/map.html"

        #act
        self.assertPathRequiresLoginAndUsesTemplate(path, template)

    def assertPathRequiresLoginAndUsesTemplate(self, path, template):
        #act
        guestResponse = self.getResponse(path)
        self.login()
        memberResponse = self.getResponse(path)

        #assert
        self.assertEqual(302, guestResponse.status_code, "should redirect if not logged in")
        self.assertEqual(200, memberResponse.status_code, "should display if logged in")
        self.assertTemplateUsed(memberResponse, template)

    def getResponse(self, path):
        return self.client.get(path)

    def login(self):
        return self.client.login(username="root", password="geocam")
