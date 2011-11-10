# __BEGIN_LICENSE__
# Copyright (C) 2008-2010 United States Government as represented by
# the Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# __END_LICENSE__

# suppress bogus messages about missing class members
# pylint: disable=E1101

from datetime import datetime
import os
import json
from cStringIO import StringIO

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, \
    HttpResponseBadRequest, HttpResponseServerError
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.contrib.auth.models import User

from geocamUtil import KmlUtil
from geocamTalk.models import TalkMessage
from geocamTalk.forms import GeocamTalkForm
from geocamTalk import settings


def get_first_geolocation(messages):
    """ return the first geotagged message lat and long as tuple """
    try:
        return [(m.latitude, m.longitude) for m in messages if m.has_geolocation()][0]
    except:  # pylint: disable=W0702
        return ()


@login_required
def message_map(request):
    messages = TalkMessage.getMessages()
    return render_to_response('geocamTalk/map.html',
                              dict(gc_msg=messages,
                                   first_geolocation=get_first_geolocation(messages)),
                              context_instance=RequestContext(request))


@login_required
def clear_messages(request):
    profile = request.user.profile
    profile.last_viewed_mymessages = TalkMessage.getLargestMessageId()
    profile.save()

    return HttpResponse(json.dumps({'ts': TalkMessage.getLargestMessageId()}))


@login_required
def message_list(request, recipient_username=None, author_username=None):
    timestamp = TalkMessage.getLargestMessageId()
    if recipient_username is not None:
        recipient = get_object_or_404(User, username=recipient_username)
    else:
        recipient = None

    if author_username is not None:
        author = get_object_or_404(User, username=author_username)
    else:
        author = None

    if recipient is not None and recipient.pk == request.user.pk and author is None:
        profile = recipient.profile
        profile.last_viewed_mymessages = timestamp
        profile.save()

    return render_to_response('geocamTalk/message_list.html',
                               dict(gc_msg=TalkMessage.getMessages(recipient, author),
                                   recipient=recipient,
                                   author=author,
                                   timestamp=timestamp),
                               context_instance=RequestContext(request))


def get_messages(request, recipient_username=None, author_username=None):
    timestamp = TalkMessage.getLargestMessageId()
    if recipient_username is not None:
        recipient = get_object_or_404(User, username=recipient_username)
    else:
        recipient = None

    if author_username is not None:
        author = get_object_or_404(User, username=author_username)
    else:
        author = None
    since = request.GET.get('since', None)

    if since is not None:
        since_dt = since
        messages = TalkMessage.getMessages(recipient, author).filter(pk__gt=since_dt)
        message_count = TalkMessage.getMessages(recipient).filter(pk__gt=since_dt).count()
    else:
        messages = TalkMessage.getMessages(recipient, author)
        message_count = TalkMessage.getMessages(recipient).count()
    return timestamp, messages, message_count


def feed_messages(request, recipient_username=None, author_username=None):
    timestamp, messages, message_count = get_messages(request, recipient_username, author_username)
    return HttpResponse(json.dumps({'ts': timestamp,
                                    'msgCnt': message_count,
                                    'ms': [msg.getJson() for msg in messages]}))


def message_details_json(request, message_id):
    if not request.user.is_authenticated():
        return HttpResponseForbidden()
    else:
        message = get_object_or_404(TalkMessage, pk=message_id)
        return HttpResponse(json.dumps(message.getJson()))


@login_required
def message_details(request, message_id):
    message = get_object_or_404(TalkMessage, pk=message_id)

    return render_to_response('geocamTalk/details.html',
                              {'message': message},
                              context_instance=RequestContext(request))


@login_required
def index(request):
    return render_to_response('geocamTalk/home.html',
                              dict(),
                              context_instance=RequestContext(request))


@login_required
def create_message(request):
    if request.method == 'POST':
        form = GeocamTalkForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            # Set time manually this way in case we switch back to a versioned message
            # model in the future
            msg.content_timestamp = datetime.now()
            msg.save()
            form.save_m2m()
            msg.push_to_phone(True)
            return HttpResponseRedirect(reverse("talk_message_list_all"))
        else:
            return render_to_response('geocamTalk/message_form.html',
                                  dict(form=form),
                                  context_instance=RequestContext(request))
    else:
        form = GeocamTalkForm()
        return render_to_response('geocamTalk/message_form.html',
                                  dict(form=form),
                                  context_instance=RequestContext(request))


def register(request):
    if not request.user.is_authenticated():
        return HttpResponseForbidden()
    else:
        if request.method == 'POST':
            try:  # to access the POST object via a potentially nonexistant key
                regid = request.POST["registration_id"]
            except KeyError:
                return HttpResponseBadRequest()

            profile = request.user.profile
            profile.registration_id = regid
            profile.save()
            return HttpResponse("", 200)
        else:
            return HttpResponseBadRequest()


def unregister(request):
    if not request.user.is_authenticated():
        return HttpResponseForbidden()
    else:
        profile = request.user.profile
        profile.registration_id = None
        profile.save()
        return HttpResponse("", 200)


def create_message_json(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            jsonstring = request.POST["message"]
            messageDict = json.loads(jsonstring)
            messageDict["userId"] = request.user.pk
            message = TalkMessage.fromJson(messageDict)

            if "audio" in request.FILES:
                filename = "%s%s.mp4" % (message.author, message.content_timestamp.strftime("%H%M%S"))
                file_content = ContentFile(request.FILES['audio'].read())
                _file_format = os.path.splitext(request.FILES['audio'].name)[-1]
                message.audio_file.save(filename, file_content)
            try:
                print message
                message.save()
                print "SAVED"
                message.push_to_phone(False)
                print "PUSHED"
                return HttpResponse(json.dumps(
                        {"messageId": "%s" % message.pk,
                          "authorFullname": message.get_author_string(),
                          "audioUrl": message.get_audio_url()
                        }), 200)
            except:  # pylint: disable=W0702
                return HttpResponseServerError()  # TODO: change the tests and here to respond with HttpResponseBadRequest
        else:
            return HttpResponseServerError()
    else:
        return HttpResponseForbidden()


def feed_messages_kml(request, recipient_username=None, author_username=None):
    _timestamp, messages, _message_count = get_messages(request, recipient_username, author_username)
    out = StringIO()
    iconHref = request.build_absolute_uri(settings.MEDIA_URL + 'geocamTalk/icons/word_bubble.png')
    out.write("""
<Document>
  <Style id="talkMarker">
    <IconStyle>
      <Icon>
        <href>%(iconHref)s</href>
      </Icon>
    </IconStyle>
  </Style>
    """ % dict(iconHref=iconHref))
    for msg in messages:
        out.write(msg.getKml())
    out.write("</Document>")
    return KmlUtil.wrapKmlDjango(out.getvalue())
