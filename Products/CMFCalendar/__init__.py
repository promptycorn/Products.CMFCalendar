##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" CMF Calendar product.

$Id$
"""

def initialize(context):

    from Products.CMFCore.utils import ContentInit
    from Products.CMFCore.utils import ToolInit

    from . import Event
    from . import CalendarTool
    from .permissions import AddPortalContent


    # Make sure security is initialized
    from . import utils

    ToolInit( 'CMF Calendar Tool'
            , tools=(CalendarTool.CalendarTool,)
            , icon='tool.gif'
            ).initialize( context )

    # BBB: register oldstyle constructors
    ContentInit( 'CMF Calendar Content'
               , content_types=()
               , permission=AddPortalContent
               , extra_constructors=(Event.addEvent,)
               , visibility=None
               ).initialize( context )
