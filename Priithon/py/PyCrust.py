"""PyCrust is a python shell and namespace browser application."""

# The next two lines, and the other code below that makes use of
# ``__main__`` and ``original``, serve the purpose of cleaning up the
# main namespace to look as much as possible like the regular Python
# shell environment.
import __main__
original = __main__.__dict__.keys()

__author__ = "Patrick K. O'Brien <pobrien@orbtech.com>"
__cvsid__ = "$Id: PyCrust.py,v 1.7 2004/03/15 13:42:37 PKO Exp $"
__revision__ = "$Revision: 1.7 $"[11:-2]

import wx

class App(wx.App):
    """PyCrust standalone application."""

    def OnInit(self):
        import wx
        #seb from wx import py
        import crust #seb
        wx.InitAllImageHandlers()
        seb self.frame = py.crust.CrustFrame()
        self.frame = crust.CrustFrame()
        self.frame.SetSize((800, 600))
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True

'''
The main() function needs to handle being imported, such as with the
pycrust script that wxPython installs:

    #!/usr/bin/env python

    from wx.py.PyCrust import main
    main()
'''

def main():
    """The main function for the PyCrust program."""
    # Cleanup the main namespace, leaving the App class.
    import __main__
    md = __main__.__dict__
    keepers = original
    keepers.append('App')
    for key in md.keys():
        if key not in keepers:
            del md[key]
    # Create an application instance.
    app = App(0)
    # Mimic the contents of the standard Python shell's sys.path.
    import sys
    if sys.path[0]:
        sys.path[0] = ''
    # Add the application object to the sys module's namespace.
    # This allows a shell user to do:
    # >>> import sys
    # >>> sys.app.whatever
    sys.app = app
    del sys
    # Cleanup the main namespace some more.
    if md.has_key('App') and md['App'] is App:
        del md['App']
    if md.has_key('__main__') and md['__main__'] is __main__:
        del md['__main__']
    # Start the wxPython event loop.
    app.MainLoop()

if __name__ == '__main__':
    main()
