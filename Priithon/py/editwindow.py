"""EditWindow class."""

__author__ = "Patrick K. O'Brien <pobrien@orbtech.com>"
__cvsid__ = "$Id: editwindow.py,v 1.10 2004/03/26 19:26:34 RD Exp $"
__revision__ = "$Revision: 1.10 $"[11:-2]

import wx
from wx import stc

import keyword
import os
import sys
import time

import dispatcher
from version import VERSION

if wx.VERSION[:2] < (2,6): # seb
    if wx.Platform == '__WXMSW__':
        FACES = { 'times'  : 'Times New Roman',
                  'mono'   : 'Courier New',
                  'helv'   : 'Lucida Console',
                  'lucida' : 'Lucida Console',
                  'other'  : 'Comic Sans MS',
                  'size'   : 10,
                  'lnsize' : 9,
                  'backcol': '#FFFFFF',

                  'calltipbg' : '#FFFFB8',
                  'calltipfg' : '#404040',
                  }
    else:  # GTK
        FACES = { 'times'  : 'Times',
                  'mono'   : 'Courier',
                  'helv'   : 'Helvetica',
                  'other'  : 'new century schoolbook',
                  'size'   : 12,
                  'lnsize' : 10,
                  'backcol': '#FFFFFF',

                  'calltipbg' : '#FFFFB8',
                  'calltipfg' : '#404040',                  
                  }
else: #seb
    if 'wxMSW' in wx.PlatformInfo:
        FACES = { 'times'     : 'Times New Roman',
                  'mono'      : 'Courier New',
                  'helv'      : 'Arial',
                  'lucida'    : 'Lucida Console',
                  'other'     : 'Comic Sans MS',
                  'size'      : 10,
                  'lnsize'    : 8,
                  'backcol'   : '#FFFFFF',
                  'calltipbg' : '#FFFFB8',
                  'calltipfg' : '#404040',
                }

    elif 'wxGTK' in wx.PlatformInfo and 'gtk2' in wx.PlatformInfo:
        FACES = { 'times'     : 'Serif',
                  'mono'      : 'Monospace',
                  'helv'      : 'Sans',
                  'other'     : 'new century schoolbook',
                  'size'      : 10,
                  'lnsize'    : 9,
                  'backcol'   : '#FFFFFF',
                  'calltipbg' : '#FFFFB8',
                  'calltipfg' : '#404040',
                }

    elif 'wxMac' in wx.PlatformInfo:
        FACES = { 'times'     : 'Lucida Grande',
                  'mono'      : 'Courier New',
                  'helv'      : 'Geneva',
                  'other'     : 'new century schoolbook',
                  'size'      : 13,
                  'lnsize'    : 10,
                  'backcol'   : '#FFFFFF',
                  'calltipbg' : '#FFFFB8',
                  'calltipfg' : '#404040',
                }

    else: # GTK1, etc.
        FACES = { 'times'     : 'Times',
                  'mono'      : 'Courier',
                  'helv'      : 'Helvetica',
                  'other'     : 'new century schoolbook',
                  'size'      : 12,
                  'lnsize'    : 10,
                  'backcol'   : '#FFFFFF',
                  'calltipbg' : '#FFFFB8',
                  'calltipfg' : '#404040',
                }



class EditWindow(stc.StyledTextCtrl):
    """EditWindow based on StyledTextCtrl."""

    revision = __revision__

    def __init__(self, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.CLIP_CHILDREN | wx.SUNKEN_BORDER):
        """Create EditWindow instance."""
        stc.StyledTextCtrl.__init__(self, parent, id, pos, size, style)
        self.__config()
        stc.EVT_STC_UPDATEUI(self, id, self.OnUpdateUI)
        dispatcher.connect(receiver=self._fontsizer, signal='FontIncrease')
        dispatcher.connect(receiver=self._fontsizer, signal='FontDecrease')
        dispatcher.connect(receiver=self._fontsizer, signal='FontDefault')

        #seb:    http://wiki.wxpython.org/index.cgi/StyledTextCtrl_Log_Window_Demo
        self._styles = [None]*32
        self._free = 1


    def _fontsizer(self, signal):
        """Receiver for Font* signals."""
        size = self.GetZoom()
        if signal == 'FontIncrease':
            size += 1
        elif signal == 'FontDecrease':
            size -= 1
        elif signal == 'FontDefault':
            size = 0
        self.SetZoom(size)

    def __config(self):
        """Configure shell based on user preferences."""
        self.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(1, 40)

        self.SetLexer(stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, ' '.join(keyword.kwlist))

        self.setStyles(FACES)
        self.SetViewWhiteSpace(False)
        self.SetTabWidth(4)
        self.SetUseTabs(False)
        # Do we want to automatically pop up command completion options?
        self.autoComplete = True
        self.autoCompleteIncludeMagic = True
        self.autoCompleteIncludeSingle = True
        self.autoCompleteIncludeDouble = True
        self.autoCompleteCaseInsensitive = True
        self.AutoCompSetIgnoreCase(self.autoCompleteCaseInsensitive)
        self.autoCompleteAutoHide = False
        self.AutoCompSetAutoHide(self.autoCompleteAutoHide)
        self.AutoCompStops(' .,;:([)]}\'"\\<>%^&+-=*/|`')
        # Do we want to automatically pop up command argument help?
        self.autoCallTip = True
        self.CallTipSetBackground(FACES['calltipbg'])
        self.CallTipSetForeground(FACES['calltipfg'])
        self.SetWrapMode(False)
        try:
            self.SetEndAtLastLine(False)
        except AttributeError:
            pass

    def setStyles(self, faces):
        """Configure font size, typeface and color for lexer."""

        # Default style
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT,
                          "face:%(mono)s,size:%(size)d,back:%(backcol)s" % \
                          faces)

        self.StyleClearAll()

        # Built in styles
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER,
                          "back:#C0C0C0,face:%(mono)s,size:%(lnsize)d" % faces)
        self.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR,
                          "face:%(mono)s" % faces)
        self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT,
                          "fore:#0000FF,back:#FFFF88")
        self.StyleSetSpec(stc.STC_STYLE_BRACEBAD,
                          "fore:#FF0000,back:#FFFF88")

        # Python styles
        self.StyleSetSpec(stc.STC_P_DEFAULT,
                          "face:%(mono)s" % faces)
        self.StyleSetSpec(stc.STC_P_COMMENTLINE,
                          "fore:#007F00,face:%(mono)s" % faces)
        self.StyleSetSpec(stc.STC_P_NUMBER,
                          "")
        self.StyleSetSpec(stc.STC_P_STRING,
                          "fore:#7F007F,face:%(mono)s" % faces)
        self.StyleSetSpec(stc.STC_P_CHARACTER,
                          "fore:#7F007F,face:%(mono)s" % faces)
        self.StyleSetSpec(stc.STC_P_WORD,
                          "fore:#00007F,bold")
        self.StyleSetSpec(stc.STC_P_TRIPLE,
                          "fore:#7F0000")
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE,
                          "fore:#000033,back:#FFFFE8")
        self.StyleSetSpec(stc.STC_P_CLASSNAME,
                          "fore:#0000FF,bold")
        self.StyleSetSpec(stc.STC_P_DEFNAME,
                          "fore:#007F7F,bold")
        self.StyleSetSpec(stc.STC_P_OPERATOR,
                          "")
        self.StyleSetSpec(stc.STC_P_IDENTIFIER,
                          "")
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK,
                          "fore:#7F7F7F")
        self.StyleSetSpec(stc.STC_P_STRINGEOL,
                          "fore:#000000,face:%(mono)s,back:#E0C0E0,eolfilled" % faces)

    def OnUpdateUI(self, event):
        """Check for matching braces."""
        # If the auto-complete window is up let it do its thing.
        if self.AutoCompActive() or self.CallTipActive():
            return
        braceAtCaret = -1
        braceOpposite = -1
        charBefore = None
        caretPos = self.GetCurrentPos()
        if caretPos > 0:
            charBefore = self.GetCharAt(caretPos - 1)
            styleBefore = self.GetStyleAt(caretPos - 1)

        # Check before.
        if charBefore and chr(charBefore) in '[]{}()' \
        and styleBefore == stc.STC_P_OPERATOR:
            braceAtCaret = caretPos - 1

        # Check after.
        if braceAtCaret < 0:
            charAfter = self.GetCharAt(caretPos)
            styleAfter = self.GetStyleAt(caretPos)
            if charAfter and chr(charAfter) in '[]{}()' \
            and styleAfter == stc.STC_P_OPERATOR:
                braceAtCaret = caretPos

        if braceAtCaret >= 0:
            braceOpposite = self.BraceMatch(braceAtCaret)

        if braceAtCaret != -1  and braceOpposite == -1:
            self.BraceBadLight(braceAtCaret)
        else:
            self.BraceHighlight(braceAtCaret, braceOpposite)

    def CanCopy(self):
        """Return True if text is selected and can be copied."""
        return self.GetSelectionStart() != self.GetSelectionEnd()

    def CanCut(self):
        """Return True if text is selected and can be cut."""
        return self.CanCopy() and self.CanEdit()

    def CanEdit(self):
        """Return True if editing should succeed."""
        return not self.GetReadOnly()

    def CanPaste(self):
        """Return True if pasting should succeed."""
        return stc.StyledTextCtrl.CanPaste(self) and self.CanEdit()


    # seb added this inspired by 
    #    http://wiki.wxpython.org/index.cgi/StyledTextCtrl_Log_Window_Demo
    def getStyle(self, c='black'):
        """
        Returns a style for a given colour if one exists.  If no style
        exists for the colour, make a new style.
        
        If we run out of styles, (only 32 allowed here) we go to the top
        of the list and reuse previous styles.

        """
        free = self._free
        if c and isinstance(c, (str, unicode)):
            c = c.lower()
        else:
            c = 'black'

        try:
            style = self._styles.index(c)
            return style

        except ValueError:
            style = free
            self._styles[style] = c
            self.StyleSetForeground(style, wx.NamedColour(c))

            free += 1
            if free >31:
                free = 0
            self._free = free
            return style


    def write(self, text, c=None):
        """
        Add the text to the end of the control using colour c which
        should be suitable for feeding directly to wx.NamedColour.
        
        'text' should be a unicode string or contain only ascii data.
        """
        style = self.getStyle(c)
        lenText = len(text.encode('utf8'))
        end = self.GetLength()
        self.AddText(text)
        self.StartStyling(end, 31)
        self.SetStyling(lenText, style)
        self.EnsureCaretVisible()


    __call__ = write

