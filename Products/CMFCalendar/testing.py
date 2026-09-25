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
""" Unit test layers.

$Id$
"""

from Testing import ZopeTestCase
ZopeTestCase.installProduct('ZCTextIndex', 1)
ZopeTestCase.installProduct('CMFCore', 1)
ZopeTestCase.installProduct('PluginIndexes', 1)

import transaction

from Testing.ZopeTestCase.layer import ZopeLite
from zope.component.hooks import setHooks
from zope.testing.cleanup import cleanUp
from Products.CMFDefault.factory import addConfiguredSite

# BBB for Zope 2.12
try:
    from Zope2.App import zcml
except ImportError:
    from Products.Five import zcml


class CalendarZCMLLayer(ZopeLite):

    @classmethod
    def setUp(cls):
        import Products.CMFCalendar
        zcml.load_config('testing.zcml', Products.CMFCalendar)
        setHooks()

    @classmethod
    def tearDown(cls):
        cleanUp()


class FunctionalLayer(CalendarZCMLLayer):

    @classmethod
    def setUp(cls):
        import Products.CMFCalendar
        import Products.CMFDefault
        import Products.DCWorkflow
        import OFS

        zcml.load_config('configure.zcml', Products.CMFCalendar)
        zcml.load_config('configure.zcml', Products.CMFDefault)
        zcml.load_config('configure.zcml', Products.DCWorkflow)

        try:
            zcml.load_config('meta.zcml', OFS)
            zcml.load_config('configure.zcml', OFS)
        except IOError:  # Zope <= 2.13.0a2
            pass
        ZopeTestCase.installPackage('OFS')

        app = ZopeTestCase.app()
        from OFS.Folder import Folder
        from Products.Sessions.BrowserIdManager import BrowserIdManager
        from Products.Sessions.SessionDataManager import SessionDataManager
        from Products.Transience.Transience import TransientObjectContainer
        app._setObject('temp_folder', Folder('temp_folder'))
        app.temp_folder._setObject('session_data',
                                  TransientObjectContainer('session_data'))
        app._setObject('browser_id_manager', BrowserIdManager('browser_id_manager'))
        app._setObject('session_data_manager', SessionDataManager(
            'session_data_manager', '/temp_folder/session_data'))
        addConfiguredSite(app, 'site', 'Products.CMFDefault:default',
                          snapshot=False,
                          extension_ids=('Products.CMFCalendar:default',
                                        'Products.CMFCalendar:skins_support'))
        transaction.commit()
        ZopeTestCase.close(app)

    @classmethod
    def tearDown(cls):
        app = ZopeTestCase.app()
        app._delObject('site')
        for name in ('session_data_manager', 'browser_id_manager', 'temp_folder'):
            app._delObject(name)
        transaction.commit()
        ZopeTestCase.close(app)
