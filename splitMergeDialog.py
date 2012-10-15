import numpy
import os
import wx

import datadoc
import util
import pdb

class SplitMergeDialog(wx.Dialog):
    """
    This dialog will enable re-ordering, splitting, & merging of different 
    dimensions - currently it allows a user to cut up a file into multiple 
    sub-files, each of which contain a subset of the original file's data.                           
    Based on the original DiceDialog of Chris.
    """
    
    def __init__(
            self, parent, dataDoc, size = wx.DefaultSize, 
            pos = wx.DefaultPosition, 
            style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
            ):
        wx.Dialog.__init__(self, parent, -1, "Split/Merge", pos, size, style)

        self.dataDoc = dataDoc

        mainSizer = wx.BoxSizer(wx.ALIGN_CENTER)

        mainSizer.AddSpacer(5)
        explanationText = wx.StaticText(self, -1, 
                "Work in progress! Select ONE of the tasks below - Split, Merge, or Re-order data.",
                size = (600, 25))
        mainSizer.Add(explanationText, 0, wx.ALIGN_CENTRE | wx.ALL, 10)

        pixelSizes = self.dataDoc.imageHeader.d

        # TODO: 1. remove cruft, and 2. improve layout
        columnSizer = wx.BoxSizer(wx.VERTICAL) 

        # TODO: sizer containing 3xcomboBox for all open files (for merge)
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)                                  
        sectionTitle = wx.StaticText(self, -1, "Specify datasets to Merge:")
        columnSizer.Add(sectionTitle)
        columnSizer.AddSpacer(10)
        TODOtext = wx.StaticText(self, -1, "    TODO: add comboBoxes here")
        columnSizer.Add(TODOtext)
        columnSizer.Add(rowSizer)
        columnSizer.AddSpacer(20)
        
        # Channel label boxes to specify mapping for re-ordering
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)                                  
        sectionTitle = wx.StaticText(self, -1, "Specify Channel Re-ordering:")
        self.channelMap = []
        for i in xrange(self.dataDoc.size[0]):
            self.channelMap.append( util.addLabeledInput(self, rowSizer,                
                label = "  Channel %d => " % i, defaultValue = str(i)) )
        columnSizer.Add(sectionTitle)
        columnSizer.AddSpacer(10)
        columnSizer.Add(rowSizer)
        columnSizer.AddSpacer(20)

        # Horizontal sizer containing action buttons 
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        rowSizer.Add((1, 1), 1, wx.EXPAND)
        button = wx.Button(self, wx.ID_OK, "Split Channels")
        button.Bind(wx.EVT_BUTTON, self.OnSplitChannels)
        rowSizer.Add(button, 0, wx.LEFT | wx.BOTTOM, 10)
        button = wx.Button(self, wx.ID_OK, "Split Frames")
        button.Bind(wx.EVT_BUTTON, self.OnSplitFrames)
        rowSizer.Add(button, 0, wx.LEFT | wx.BOTTOM, 10)
        button = wx.Button(self, wx.ID_OK, "Merge Images")
        button.Bind(wx.EVT_BUTTON, self.OnMerge)
        rowSizer.Add(button, 0, wx.LEFT | wx.BOTTOM, 10)
        button = wx.Button(self, wx.ID_OK, "Re-order Channels")
        button.Bind(wx.EVT_BUTTON, self.OnReorder)
        rowSizer.Add(button, 0, wx.LEFT | wx.BOTTOM, 10)
        button = wx.Button(self, wx.ID_CANCEL, "Cancel")
        button.Bind(wx.EVT_BUTTON, self.OnCancel)
        rowSizer.Add(button, 0, wx.LEFT | wx.BOTTOM, 10)
        columnSizer.Add(rowSizer)

        mainSizer.Add(columnSizer, 0, wx.ALL, 10)

        self.SetSizerAndFit(mainSizer)

        self.SetPosition((400, 300))
        self.Show()


    def OnSplitFrames(self, event):
        """
        Cut the file up into single-frame files and save each one to 
        a directory the user chooses.
        """
        # TODO: remove align and crop, and move core to dataDoc
        alignParams = self.dataDoc.alignParams

        ## This is the MRC object we will use to instantiate new 
        # DataDocs with only one timepoint each.
        fullImagePath = self.dataDoc.filePath

        # Make a copy of the DataDoc so we can freely change values without
        # affecting the original. \todo This is wasteful of memory.
        doc = datadoc.DataDoc(fullImagePath)
        # Can't crop in time, obviously.
        cropMin = numpy.array(self.dataDoc.cropMin)
        cropMin[1] = 0
        cropMax = numpy.array(self.dataDoc.cropMax)
        cropMax[1] = 1
        doc.cropMin = cropMin
        doc.cropMax = cropMax

        #XYSize = float(self.XYPixelSize.GetValue())
        #ZSize = float(self.ZPixelSize.GetValue())
        #doc.imageHeader.d = numpy.array([XYSize, XYSize, ZSize])

        for i in xrange(self.dataDoc.size[1]):
            #targetFilename = os.path.join(savePath,
            #        os.path.basename(self.dataDoc.filePath) + '_T%03d' % i)

            # use existing file path+root but tag with timepoint
            pathBase = os.path.splitext(fullImagePath)[0]                                
            tags = '_T%03d' % i
            fileExt = ".dv"                                                         
            targetFilename = pathBase + tags + fileExt
            doc.alignAndCrop(savePath = targetFilename, timepoints = [i])

        self.Hide()
        self.Destroy()


    # TODO: create and call datadoc.reorder(), then update display 
    def OnReorder(self, event):
        """
        Take the currently selected image doc and re-order the dimensions
        according to any changes already entered (save with _ERE tag).
        """
        fullImagePath = self.dataDoc.filePath
        # make a copy of the doc - TODO, remove?
        doc = datadoc.DataDoc(fullImagePath)
        # 1. check the mapping makes sense - i.e. same elements as original
        origMap = []
        for i in xrange(self.dataDoc.size[0]):
            origMap.append(i)
        newMap = []
        for mapc in self.channelMap:
            newMap.append(int(mapc.GetValue()))

        if set(origMap) != set(newMap):
            wx.MessageBox('Re-ordering Error', 'Input does not match Channels.', 
            wx.OK | wx.ICON_INFORMATION)
        else:
            #targetFilename = os.path.join(savePath,
            #        os.path.basename(self.dataDoc.filePath) + '_ERE')
            pathBase = os.path.splitext(fullImagePath)[0]                                
            tags = '_ERE'
            fileExt = ".dv"                                                         
            targetFilename = pathBase + tags + fileExt 
            doc.saveSelection(savePath = targetFilename, wavelengths = newMap)

        self.Hide()
        self.Destroy()

    # TODO: create and call datadoc.splitChannels(), then update display 
    def OnSplitChannels(self, event):
        """
        Take currently selected image doc and split into one doc per channel.
        """
        fullImagePath = self.dataDoc.filePath

        # Make a copy of the DataDoc so we can freely change values without
        # affecting the original. \todo This is wasteful of memory.
        doc = datadoc.DataDoc(fullImagePath)

        for i in xrange(self.dataDoc.size[0]):
            # use existing file path+root but tag with channel number
            pathBase = os.path.splitext(fullImagePath)[0]                                
            tags = '_C%01d' % i
            fileExt = ".dv"                                                         
            targetFilename = pathBase + tags + fileExt 
            doc.saveSelection(savePath = targetFilename, wavelengths = [i])
        self.Hide()
        self.Destroy()

    # TODO: create and call datadoc.merge(), then update display 
    def OnMerge(self, event):
        """
        Take selected image docs and merge channels (if possible).
        """
        print 'dataset merge not yet implemented'
        self.Hide()
        self.Destroy()

    def OnCancel(self, event):
        self.Hide()
        self.Destroy()

