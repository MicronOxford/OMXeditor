import numpy
import os
import wx
import datadoc
import util


## This dialog provides an interface for the user to batch-apply alignment
# and cropping parameters to a large number of files. Note that this
# functionality is replicated in the OMX Processor program, which most users
# are more likely to use.
class BatchDialog(wx.Dialog):
    ## Instantiate the dialog. The important extra parameter here compared
    # to a normal dialog is controller, which is a ControlPanel instance that
    # we use to get the "base" align/crop parameters.
    def __init__(
            self, parent, controller, size = wx.DefaultSize, 
            pos = wx.DefaultPosition, 
            style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
            ):
        wx.Dialog.__init__(self, parent, -1, "Batch-process files", pos, size, style)

        self.controller = controller

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        explanationText = wx.StaticText(self, -1, 
                "This dialog allows you to apply the alignment and/or " +
                "cropping parameters of the currently-selected file to a " +
                "group of other files. When you click Start, you will be " + 
                "prompted to choose the files you want to modify, and then " +
                "to choose a location to save the modified files to.\n\n" + 
                "Cropping does not work if the files have different XY " + 
                "sizes, though it will account for variations in the number " +
                "of Z slices and crop all images to the same number of " +
                "slices.",
                size = (400, 150))
        mainSizer.Add(explanationText, 0, wx.ALIGN_CENTRE | wx.ALL, 10)

        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.shouldCrop = wx.CheckBox(self, -1, "Crop files")
        self.shouldCrop.SetValue(True)
        rowSizer.Add(self.shouldCrop)
        mainSizer.Add(rowSizer, 0, wx.ALIGN_CENTRE | wx.BOTTOM, 5)

        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.shouldAlign = wx.CheckBox(self, -1, "Align files")
        self.shouldAlign.SetValue(True)
        rowSizer.Add(self.shouldAlign)
        mainSizer.Add(rowSizer, 0, wx.ALIGN_CENTRE | wx.BOTTOM, 5)
        
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        rowSizer.Add(cancelButton)
        startButton = wx.Button(self, wx.ID_OK, "Start")
        rowSizer.Add(startButton)

        mainSizer.Add(rowSizer, -1, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.SetSizerAndFit(mainSizer)

        wx.EVT_BUTTON(self, wx.ID_OK, self.OnStart)
        wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)

        self.SetPosition((400, 300))
        self.Show()


    ## Extract the alignment and cropping parameters from self.controller, 
    # get the list of files from the user, then open each file, apply the 
    # parameters, and save it.
    def OnStart(self, event):
        alignParams = self.controller.dataDoc.alignParams
        cropMin = self.controller.dataDoc.cropMin
        cropMax = self.controller.dataDoc.cropMax
        cropSize = cropMax - cropMin
        initialShape = self.controller.dataDoc.size
        openDialog = wx.FileDialog(self,
                "Please select the files you wish to modify",
                style = wx.FD_OPEN | wx.FD_MULTIPLE)
        if openDialog.ShowModal() != wx.ID_OK:
            return

        files = openDialog.GetPaths()

        progress = wx.ProgressDialog(parent = self,
                title = "Aligning and cropping files",
                message = " " * 100, # To make the dialog big enough.
                maximum = len(files),
                style = wx.PD_AUTO_HIDE | wx.PD_ESTIMATED_TIME |
                        wx.PD_REMAINING_TIME | wx.PD_SMOOTH)
        progress.Show()
        for i, file in enumerate(files):
            progress.Update(i, os.path.basename(file))
            doc = datadoc.DataDoc(file)
            if self.shouldCrop.GetValue():
                # Scale the cropbox's position in Z so that it's the same 
                # proportionate distance from the top of the Z stack as the 
                # original cropping job was.
                heightScale = float((doc.size[2] - cropSize[0]) / (initialShape[2] - cropSize[0]))
                newBoxMin = numpy.array(cropMin)
                newBoxMax = numpy.array(cropMax)
                newBoxMin[0] = int(newBoxMin[0] * heightScale)
                newBoxMax[0] = newBoxMin[0] + cropSize[0]
                doc.cropMin = newBoxMin
                doc.cropMax = newBoxMax
            if self.shouldAlign.GetValue():
                # We do this one row at a time so that users can align a subset
                # of the wavelengths of their files if they so choose, or 
                # use a source file that has more wavelengths than the target
                # file.
                for j, row in enumerate(alignParams):
                    doc.alignParams[j] = row
                    if j == len(doc.alignParams) - 1:
                        break
            # gb, 26/4/12 - add _SAL
            #targetFilename = os.path.join(savePath, os.path.basename(file))
            froot,fext = os.path.splitext(file)
            # gb, Oct2012 - filename depending on operations performed
            tag = "";
            if self.shouldCrop.GetValue():
                tag += "_ECR"
            if self.shouldAlign.GetValue():
                tag += "_EAL"
            # TODO: always use .dv fext?
            targetFilename = froot + tag + fext
            print targetFilename
            doc.alignAndCrop(savePath = targetFilename)
        progress.Update(len(files), "All done!")

        self.Hide()
        self.Destroy()


    def OnCancel(self, event):
        self.Hide()
        self.Destroy()


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


class SplitMergeDialog(wx.Dialog):
    """
    This dialog will enable re-ordering, splitting, & merging of different 
    dimensions - currently it allows a user to cut up a file into multiple 
    sub-files, each of which contain a subset of the original file's data.                           
    """
    # loosely based on the original DiceDialog of Chris.
    # TODO: try/except to handle failed editing tasks 
    #       (input checking should be done by edit.py)
    
    def __init__(
            self, parent, dataDoc, size = wx.DefaultSize, 
            pos = wx.DefaultPosition, 
            style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
            ):
        wx.Dialog.__init__(self, parent, -1, "Split/Merge", pos, size, style)

        self.editor = parent.editor
        self.dataDocs = self.editor.dataDocs
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
        docFiles = ["None"]
        for doc in self.dataDocs:
            docFiles.append(doc.filePath)
        sectionTitle = wx.StaticText(self, -1, "Specify datasets to Merge:")
        columnSizer.Add(sectionTitle)
        columnSizer.AddSpacer(10)
        cb1 = wx.ComboBox(self, choices=docFiles, style=wx.CB_READONLY)
        cb1.Bind(wx.EVT_COMBOBOX, self.OnSelect1)
        columnSizer.Add(cb1)
        cb2 = wx.ComboBox(self, choices=docFiles, style=wx.CB_READONLY)
        cb2.Bind(wx.EVT_COMBOBOX, self.OnSelect2)
        columnSizer.Add(cb2)
        cb3 = wx.ComboBox(self, choices=docFiles, style=wx.CB_READONLY)
        cb3.Bind(wx.EVT_COMBOBOX, self.OnSelect3)
        columnSizer.Add(cb3)
        # list of docFiles (paths) below used to interpret ComboBox choices
        self.docFiles = docFiles
        self.cbSelection = ["None", "None", "None"]
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
            success = self.editor.reorderChannels(fullImagePath, doc, newMap)
            if success:
                wx.MessageBox('Re-ordering finished', 
                    'Result with _ERO tag in name.', 
                    wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox('Re-ordering failed',                           
                    'No result saved.',                            
                    wx.OK | wx.ICON_INFORMATION)

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
        # TODO - FIXME - currently using all open docs - need dialog selection
        docsToMerge = []
        print "Not yet implemented - these files selected to merge:-"
        for cbItem in self.cbSelection:
            filePath = cbItem
            if filePath != "None":
                print filePath
        resultDoc = self.editor.mergeChannels(docsToMerge)
        print resultDoc
        # TODO: default should be save to ???_EMG.xxx based on 1st doc ???.xxx
        self.Hide()
        self.Destroy()

    # Handle ComboBox selections - TODO - remove the Ugly repetition below
    def OnSelect1(self, e):
        """Update this comboBox selection."""
        self.cbSelection[1] = e.GetString()

    def OnSelect2(self, e):
        """Update this comboBox selection."""
        self.cbSelection[2] = e.GetString()

    def OnSelect3(self, e):
        """Update this comboBox selection."""
        self.cbSelection[3] = e.GetString()


    def OnCancel(self, event):
        self.Hide()
        self.Destroy()

