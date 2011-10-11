# __BEGIN_LICENSE__
# Copyright (C) 2008-2010 United States Government as represented by
# the Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# __END_LICENSE__

from datetime import datetime
import json
from cStringIO import StringIO

from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response

from geocamUtil import KmlUtil
from geocamMemo.models import MemoMessage
from geocamMemo.forms import MemoMessageForm
from geocamMemo import settings


def get_first_geolocation(messages):
    """ return the first geotagged message lat and long as tuple """

    try:
        return [(m.latitude, m.longitude) for m in messages if m.has_geolocation()][0]
    except:  # pylint: disable=W0702
        return ()


@login_required
def message_map(request):
    messages = MemoMessage.getMessages()
    return render_to_response('geocamMemo/map.html',
                              dict(gc_msg=messages,
                                   first_geolocation=get_first_geolocation(messages)),
                              context_instance=RequestContext(request))


@login_required
def message_list(request, author_username=None):
    if author_username is not None:
        author = get_object_or_404(User, username=author_username)
    else:
        author = None
    return render_to_response('geocamMemo/message_list.html',
                              dict(gc_msg=MemoMessage.getMessages(author),
                                   author=author),
                              context_instance=RequestContext(request))


# manual not logged in response
def message_list_json(request):
    if request.user.is_authenticated():
        messages = MemoMessage.getMessages()
        return HttpResponse(json.dumps([msg.getJson() for msg in messages]))
    else:
        return HttpResponseForbidden()


@login_required
def index(request):
    return HttpResponseRedirect(reverse('memo_message_list_all'))


@login_required
def message_details(request, message_id):
    message = get_object_or_404(MemoMessage, pk=message_id)

    return render_to_response('geocamMemo/details.html',
                              {'message': message},
                              context_instance=RequestContext(request))


# login not yet required
def message_details_json(request, message_id):
    message = get_object_or_404(MemoMessage, pk=message_id)
    return HttpResponse(json.dumps(message.getJson()))


@login_required
def create_message(request):
    if request.method == 'POST':
        form = MemoMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            # Set time manually this way in case we switch back to a versioned message
            # model in the future
            msg.content_timestamp = datetime.now()
            msg.save()
            return HttpResponseRedirect(reverse('memo_message_list_all'))
        else:
            return render_to_response('geocamMemo/message_form.html',
                                  dict(form=form),
                                  context_instance=RequestContext(request))
    else:
        form = MemoMessageForm()
        return render_to_response('geocamMemo/message_form.html',
                                  dict(form=form),
                                  context_instance=RequestContext(request))


def create_message_json(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            jsonstring = request.POST["message"]
            messageDict = json.loads(jsonstring)
            messageDict["userId"] = request.user.pk
            message = MemoMessage.fromJson(messageDict)
            try:
                message.save()
                return HttpResponse("", 200)
            except:  # pylint: disable=W0702
                return HttpResponseServerError()
        else:
            return HttpResponseServerError()
    else:
        return HttpResponseForbidden()


@login_required
def edit_message(request, message_id):
    message = MemoMessage.objects.get(pk=message_id)
    if message.author.username != request.user.username and not request.user.is_superuser:
        return HttpResponseRedirect(reverse('memo_message_list_all'))  # you get the boot!
    if request.method == 'POST':
        message.content = request.POST['content']
        form = MemoMessageForm(request.POST)
        if form.is_valid():
            message.save()
            return HttpResponseRedirect(reverse('memo_message_list_all'))
        else:
            return render_to_response('geocamMemo/edit_message_form.html',
                                  dict(form=form,
                                       message=message),
                                  context_instance=RequestContext(request))
    else:
        form = MemoMessageForm(instance=message)
        return render_to_response('geocamMemo/edit_message_form.html',
                                  dict(form=form,
                                       message=message),
                                  context_instance=RequestContext(request))


@login_required
def delete_message(request, message_id):
    message = MemoMessage.objects.get(pk=message_id)
    if message.author.username == request.user.username or request.user.is_superuser:
        message.delete()
    return HttpResponseRedirect(reverse('memo_message_list_all'))

def get_messages(request, author_username=None):
    if author_username is not None:
        author = get_object_or_404(User, username=author_username)
    else:
        author = None
    since = request.GET.get('since', None)

    if since is not None:
        since_dt = since
        messages = MemoMessage.getMessages(author).filter(pk__gt=since_dt)
        message_count = MemoMessage.getMessages(request.user).filter(pk__gt=since_dt).count()
    else:
        messages = MemoMessage.getMessages(author)
        message_count = MemoMessage.getMessages(request.user).count()
    return messages, message_count


def feed_messages_kml(request, author_username=None):
    messages, _message_count = get_messages(request, author_username)
    out = StringIO()
    iconHref = request.build_absolute_uri(settings.MEDIA_URL + 'geocamMemo/icons/note.png')
    out.write("""
<Document>
  <Style id="memoMarker">
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
