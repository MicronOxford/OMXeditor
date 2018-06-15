# Copyright 2015, Graeme Ball
# Copyright 2012, The Regents of University of California
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# This import is needed to get py2app to include these libraries when it
# creates the standalone application, since otherwise it doesn't notice that
# OpenGL depends on them. HACK.
import ctypes, ctypes.util

import os
import wx

import mainWindow

## The requisite WX App instance; this just creates the main window and 
# passes it any files that were specified in the commandline.
class OMXeditorApp(wx.App):
    def OnInit(self):
        import sys
        self.frame = mainWindow.MainWindow('OMX Editor v2.5')

        self.frame.Show()
        self.SetTopWindow(self.frame)

        if sys.platform == 'linux2':
            from OpenGL import GLUT
            GLUT.glutInit([])  ## in order to call Y.glutText()

        haveFilesToOpen = False
        for file in sys.argv[1:]:
            # When invoking this program as a standalone bundled app with 
            # py2app, a bunch of junk we don't care about shows up on the 
            # commandline, so only try to open a file if it actually exists.
            if os.path.exists(file):
                self.frame.openFile(file)
                haveFilesToOpen = True

        if not haveFilesToOpen:
            # Instead of just popping up a blank window, show an open-file
            # dialog.
            self.frame.OnFileOpen()

        return True

    def setStatusbarText(self, text, number=0):
        self.frame.SetStatusText(text, number)


if __name__ == '__main__':
    app = OMXeditorApp(redirect=False)
    app.MainLoop()
