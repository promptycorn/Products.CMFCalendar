##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Browser views for events.

$Id$
"""

import time

from zope.app.form.browser import DatetimeI18nWidget
from zope.component import adapts
from zope.component import getUtility
from zope.formlib import form
from zope.interface import implementer
from zope.interface import Interface
from zope.schema import Choice
from zope.schema import Datetime
from zope.schema import Set
from zope.schema import Text
from zope.schema import TextLine
from zope.schema import URI
from zope.schema.interfaces import IVocabularyFactory

from Products.CMFCore.interfaces import IMetadataTool
from Products.CMFDefault.browser.utils import decode, ViewBase
from Products.CMFDefault.formlib.form import ContentEditFormBase
from Products.CMFDefault.formlib.form import DisplayFormBase
from Products.CMFDefault.formlib.schema import EmailLine
from Products.CMFDefault.formlib.schema import ProxyFieldProperty
from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from Products.CMFDefault.formlib.vocabulary import SimpleVocabulary
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFCalendar.interfaces import IMutableEvent
from Products.CMFCalendar.utils import Message as _


@implementer(IVocabularyFactory)
class EventTypeVocabulary(object):

    """Vocabulary factory for available event types.
    """


    def __call__(self, context):
        context = getattr(context, 'context', context)
        mdtool = getUtility(IMetadataTool)
        items = [ (str(v), str(v), _(v))
                  for v in mdtool.listAllowedSubjects(context) ]
        return SimpleVocabulary.fromTitleItems(items)

EventTypeVocabularyFactory = EventTypeVocabulary()


class IEventSchema(Interface):

    """Schema for event views.
    """

    title = TextLine(
        title=_('Title'),
        required=False,
        missing_value='',
        max_length=100)

    contact_name = TextLine(
        title=_('Contact Name'),
        required=False,
        missing_value='',
        max_length=100)

    location = TextLine(
        title=_('Location'),
        required=False,
        missing_value='',
        max_length=100)

    contact_email = EmailLine(
        title=_('Contact Email'),
        required=False)

    categories = Set(
        title=_('Category'),
        required=False,
        missing_value=set(),
        value_type=Choice(vocabulary="cmf.calendar.AvailableEventTypes"))

    contact_phone = TextLine(
        title=_('Contact Phone'),
        required=False,
        missing_value='',
        max_length=100)

    event_url = URI(
        title=_('URL'),
        required=False,
        missing_value='',
        max_length=100)

    start_date = Datetime(
        title=_('From'),)

    stop_date = Datetime(
        title=_('To'),)

    description = Text(
        title=_('Description'),
        required=False,
        missing_value='')


@implementer(IEventSchema)
class EventSchemaAdapter(SchemaAdapterBase):

    """Adapter for IMutableEvent.
    """

    adapts(IMutableEvent)

    title = ProxyFieldProperty(IEventSchema['title'], 'Title', 'setTitle')
    contact_name = ProxyFieldProperty(IEventSchema['contact_name'])
    location = ProxyFieldProperty(IEventSchema['location'])
    contact_email = ProxyFieldProperty(IEventSchema['contact_email'])
    categories = ProxyFieldProperty(IEventSchema['categories'],
                                    'Subject', 'setSubject')
    contact_phone = ProxyFieldProperty(IEventSchema['contact_phone'])
    event_url = ProxyFieldProperty(IEventSchema['event_url'])
    start_date = ProxyFieldProperty(IEventSchema['start_date'],
                                    'start', 'setStartDate')
    stop_date = ProxyFieldProperty(IEventSchema['stop_date'],
                                   'end', 'setEndDate')
    description = ProxyFieldProperty(IEventSchema['description'],
                                     'Description', 'setDescription')


class EventViewMixin(object):

    def setUpWidgets(self, ignore_request=False):
        super(EventViewMixin,
              self).setUpWidgets(ignore_request=ignore_request)
        self.widgets['title'].split = True
        self.widgets['contact_name'].split = True
        self.widgets['location'].split = True
        self.widgets['contact_email'].split = True
        self.widgets['categories'].split = True
        self.widgets['categories'].size = 4
        self.widgets['contact_phone'].split = True
        self.widgets['start_date'].split = True
        self.widgets['stop_date'].split = True
        self.widgets['description'].height = 5


class EventView(EventViewMixin, DisplayFormBase):

    """View for IEvent.
    """

    template = ViewPageTemplateFile('templates/event_view.pt')

    form_fields = form.FormFields(IEventSchema)


class EventEditView(EventViewMixin, ContentEditFormBase):

    """Edit view for IMutableEvent.
    """

    form_fields = form.FormFields(IEventSchema)
    form_fields['start_date'].custom_widget = DatetimeI18nWidget
    form_fields['stop_date'].custom_widget = DatetimeI18nWidget

class EventiCalView(ViewBase):
    
    """iCal view"""
        
    form_fields = form.FormFields(IEventSchema)
    icalformat = "%Y%m%dT%H%M%SZ" # Zulu time enforces UTC
    
    def mk_iCal(self, dt):
        """Convert a datetime type to its iCal using it's representation
        Unfortunately not available directly. Depends upon the underlying OS timezone"""
        dt = time.gmtime(dt.timeTime())
        return time.strftime(self.icalformat, dt)

    @decode
    def location(self):
        return self.context.location
        
    @decode
    def contact_name(self):
        return self.context.contact_name
        
    def __call__(self):
        self.creation_date = self.mk_iCal(self.context.creation_date)
        self.timestamp = time.strftime(self.icalformat, time.gmtime())
        self.tz = self.context.start().timezone()
        self.start = self.mk_iCal(self.context.start())
        self.end = self.mk_iCal(self.context.end())
        self.UID = "%s-%s" %(self.context.Title(), self.creation_date)
        return self._write_body()

    def _write_body(self):
        response = self.request.response
        body = self._calendar_body('2.0')
        response.setHeader('Content-Type', 'text/calendar; charset=utf-8')
        response.setHeader('Content-Disposition', 'filename=cmf.ics')
        return body

    def _calendar_body(self, version):
        # Calendar content is TEXT, not HTML. Escape property separators and
        # newlines before folding UTF-8 content lines at 75 octets (RFC 5545).
        def text(value):
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            return (str(value).replace('\\', '\\\\')
                    .replace('\r\n', '\n').replace('\r', '\n')
                    .replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,'))

        def uri(value):
            if '\r' in value or '\n' in value:
                raise ValueError('Calendar URI must not contain a newline')
            return value

        context = self.context
        lines = [
            'BEGIN:VCALENDAR', 'VERSION:' + version,
            'X-WR-CALNAME:' + text(context.absolute_url()),
            'PRODID:-//Zope CMF 2.1//Calendar//EN',
            'X-WR-TIMEZONE:UTC' if version == '2.0' else 'TZ:' + text(self.tz),
            'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'BEGIN:VEVENT',
            'CREATED:' + self.creation_date, 'DTSTAMP:' + self.timestamp,
            'UID:' + text(self.UID), 'DTSTART:' + self.start, 'DTEND:' + self.end,
            'SUMMARY:' + text(self.title()),
            'LOCATION:' + text(self.location()),
            'DESCRIPTION:' + text(self.description()),
        ]
        if version == '2.0':
            if self.contact_name():
                # RFC 6868 parameter escaping, inside a quoted parameter.
                contact = (self.contact_name().replace('^', '^^')
                           .replace('\r\n', '\n').replace('\r', '\n')
                           .replace('\n', '^n').replace('"', "^'"))
                lines.append('ATTENDEE;CN="%s":MAILTO:%s' % (
                    contact, uri(context.contact_email)))
            lines.append('URL:' + uri(context.absolute_url()))
            if getattr(self, 'alarm', None):
                lines.extend(['BEGIN:VALARM', 'DESCRIPTION:' + text(self.title()),
                              'ACTION:DISPLAY',
                              'TRIGGER;RELATED=START:' + uri(context.alarm),
                              'END:VALARM'])
        elif getattr(self, 'alarm', None):
            lines.append('DALARM:' + text(self.dalarm))
        lines.extend(['END:VEVENT', 'END:VCALENDAR'])

        folded = []
        for line in lines:
            part = b''
            for char in line:
                encoded = char.encode('utf-8')
                if len(part) + len(encoded) > 75:
                    folded.append(part)
                    part = b' '
                part += encoded
            folded.append(part)
        return b'\r\n'.join(folded) + b'\r\n'

class EventvCalView(EventiCalView):

    """vCal view"""

    def _write_body(self):
        response = self.request.response
        body = self._calendar_body('1.0')
        response.setHeader('Content-Type', 'text/vCal; charset=utf-8')
        response.setHeader('Content-Disposition', 'filename=cmf.vcs')
        return body
