import unittest

from AccessControl.SecurityManagement import newSecurityManager
from DateTime import DateTime
from Testing import ZopeTestCase
from zope.component.hooks import setSite

from Products.CMFCalendar.browser.tests import _setupVocabulary, _clearVocabulary
from Products.CMFCalendar.testing import FunctionalLayer


class CalendarPython3Tests(ZopeTestCase.FunctionalTestCase):
    layer = FunctionalLayer

    def afterSetUp(self):
        setSite(self.app.site)
        _setupVocabulary(None)
        uf = self.app.site.acl_users
        uf._doAddUser('calendar-manager', 'test-password', ['Manager'], [])
        newSecurityManager(None, uf.getUser('calendar-manager').__of__(uf))
        self.app.site.invokeFactory('Event', id='unicode-event')
        event = self.app.site['unicode-event']
        event.setTitle('Grüße & <Kalender>, 東京; ' + 'ä' * 80)
        event.setDescription('Erste Zeile\nZweite Zeile; Ende, \\')
        event.location = 'Köln & Zürich'
        event.contact_name = 'Müller "A"'
        event.contact_email = 'calendar@example.test'
        event.setStartDate(DateTime('2026/03/29 01:30:00 Europe/Berlin'))
        event.setEndDate(DateTime('2026/03/29 03:30:00 Europe/Berlin'))
        self.event = event

    def beforeTearDown(self):
        _clearVocabulary(None)

    def publish_event(self, view, authenticated=True):
        return self.publish('/site/unicode-event/@@' + view,
                            basic='calendar-manager:test-password' if authenticated else '')

    def test_calendar_macro_does_not_bypass_private_event_permission(self):
        for view in ('view.html', 'calendar_widget', 'view.ics'):
            with self.subTest(view=view):
                self.assertEqual(self.publish_event(view, False).getStatus(), 401)
                self.assertEqual(self.publish_event(view).getStatus(), 200)

    def test_unicode_ical_response_and_dst_boundary(self):
        response = self.publish_event('view.ics')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('content-type'), 'text/calendar; charset=utf-8')
        body = response.getBody()
        if isinstance(body, str):
            body = body.encode('utf-8')
        self.assertEqual(int(response.getHeader('content-length')), len(body))
        for line in body.split(b'\r\n'):
            self.assertLessEqual(len(line), 75)
            line.decode('utf-8')  # Folding never cuts a multibyte code point.
        unfolded = body.replace(b'\r\n ', b'').decode('utf-8')
        self.assertIn('SUMMARY:Grüße & <Kalender>\\, 東京\\; ', unfolded)
        self.assertIn('LOCATION:Köln & Zürich\r\n', unfolded)
        self.assertIn('DESCRIPTION:Erste Zeile\\nZweite Zeile\\; Ende\\, \\\\\r\n', unfolded)
        self.assertIn('DTSTART:20260329T003000Z\r\n', unfolded)
        self.assertIn('DTEND:20260329T013000Z\r\n', unfolded)
        self.assertIn('ATTENDEE;CN="Müller ^\'A^\'":MAILTO:calendar@example.test', unfolded)

    def test_empty_values_and_vcal(self):
        self.event.setDescription('')
        self.event.location = ''
        self.event.contact_name = ''
        response = self.publish_event('view.vcs')
        self.assertEqual(response.getStatus(), 200)
        body = response.getBody()
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        self.assertIn('VERSION:1.0\r\n', body)
        self.assertIn('LOCATION:\r\n', body)
        self.assertIn('DESCRIPTION:\r\n', body)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(CalendarPython3Tests)
