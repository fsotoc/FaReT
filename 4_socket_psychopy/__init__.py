# make human client GUI
#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""

Internal OpenGL Renderer Plugin.

**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    https://bitbucket.org/MakeHuman/makehuman/

**Authors:**           Thanasis Papoutsidakis
                        Jason Hays (socket stuff)

**Copyright(c):**      MakeHuman Team 2001-2017

**Licensing:**         AGPL3

    This file is part of MakeHuman (www.makehuman.org).

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


Abstract
--------

TODO
"""

from . import commons
from . import mh_server

from core import G
import gui
from guirender import RenderTaskView
import mh


class SocketRenderTaskView(RenderTaskView):

    def __init__(self, category):
        RenderTaskView.__init__(self, category, 'Socket Render')

        # Declare settings
        G.app.addSetting('GL_RENDERER_SSS', False)
        G.app.addSetting('GL_RENDERER_AA', True)

        # Don't change shader for this RenderTaskView.
        self.taskViewShader = G.app.selectedHuman.material.shader

        settingsBox = self.addLeftWidget(gui.GroupBox('Settings'))

        self.renderButton = settingsBox.addWidget(gui.Button('Socket Render'))
        

        if not mh.hasRenderToRenderbuffer():
            self.firstTimeWarn = True


        @self.renderButton.mhEvent
        def onClicked(event):
            # do socket ops here
            mh_server.do_op()
            

    def onShow(self, event):
        RenderTaskView.onShow(self, event)
        self.renderButton.setFocus()
        if not mh.hasRenderToRenderbuffer() and self.firstTimeWarn:
            self.firstTimeWarn = False
            G.app.prompt('Lack of 3D hardware support',
                'Your graphics card lacks support for proper rendering.\nOnly limited functionality will be available.',
                'Ok', None, None, None, 'renderingGPUSupportWarning')

    def onHide(self, event):
        RenderTaskView.onHide(self, event)



def load(app):
    category = app.getCategory('Rendering')
    taskview = SocketRenderTaskView(category)
    taskview.sortOrder = 1.5
    category.addTask(taskview)


def unload(app):
    pass
