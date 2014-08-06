import numpy
import os
import wx

import datadoc
import util
import pdb

class ProjResizeDialog(wx.Dialog):
    """
    This dialog will enable allow averaging of phases & angles of raw SI 
    data, and/or resizing of the result. This should facilitate merging and 
    comparison of SI and wide-field data for a given sample.  
    """
    #Based on the original DiceDialog of Chris.
    
    def __init__(
            self, parent, dataDoc, size = wx.DefaultSize, 
            pos = wx.DefaultPosition, 
            style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
            ):
        wx.Dialog.__init__(self, parent, -1, "Project/Resize", pos, size, style)

        self.editor = parent.editor
        self.dataDocs = self.editor.dataDocs
        self.dataDoc = dataDoc

        mainSizer = wx.BoxSizer(wx.ALIGN_CENTER)

        mainSizer.AddSpacer(5)
        explanationText = wx.StaticText(self, -1, 
                "Work in progress! Select ONE of the tasks below - Project or Resize data.",
                size = (600, 25))
        mainSizer.Add(explanationText, 0, wx.ALIGN_CENTRE | wx.ALL, 10)

        pixelSizes = self.dataDoc.imageHeader.d

        # TODO: 1. remove cruft, and 2. improve layout
        columnSizer = wx.BoxSizer(wx.VERTICAL) 

        # Channel label boxes to specify mapping for re-ordering
        sectionTitle = wx.StaticText(self, -1, "Specify Resizing scale factor:")
        columnSizer.Add(sectionTitle)
        columnSizer.AddSpacer(15)
        self.scaleFactor = util.addLabeledInput(self, columnSizer,                
                label = "  Scale Factor: ", defaultValue = str(2) )
        columnSizer.AddSpacer(20)

        # Horizontal sizer containing action buttons 
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        rowSizer.Add((1, 1), 1, wx.EXPAND)
        button = wx.Button(self, wx.ID_OK, "Project SI")
        button.Bind(wx.EVT_BUTTON, self.OnProject)
        rowSizer.Add(button, 0, wx.LEFT | wx.BOTTOM, 10)
        button = wx.Button(self, wx.ID_OK, "Resize")
        button.Bind(wx.EVT_BUTTON, self.OnResize)
        rowSizer.Add(button, 0, wx.LEFT | wx.BOTTOM, 10)
        button = wx.Button(self, wx.ID_OK, "Cancel")
        button.Bind(wx.EVT_BUTTON, self.OnCancel)
        rowSizer.Add(button, 0, wx.LEFT | wx.BOTTOM, 10)
        columnSizer.Add(rowSizer)

        mainSizer.Add(columnSizer, 0, wx.ALL, 10)

        self.SetSizerAndFit(mainSizer)

        self.SetPosition((400, 300))
        self.Show()


    # TODO: create and call editor.projectSI(), then update display 
    def OnProject(self, event):
        """
        Take selected image doc and project (mean) phases and angles in Z-dim.
        """
        #self.editor.projectSI(self.dataDocs)
        print "Not yet implemented."
        self.Hide()
        self.Destroy()

    # TODO: create and call editor.resize(), then update display 
    def OnResize(self, event):
        """
        Take selected image doc and resize/resample XY with interpolation 
        according to scale factor.
        """
        #self.editor.projectSI(self.dataDocs)
        print "Not yet implemented."
        self.Hide()
        self.Destroy()

    def OnCancel(self, event):
        self.Hide()
        self.Destroy()

