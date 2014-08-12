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
