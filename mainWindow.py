import wx, wx.aui
import os
import re
import sys
import threading
import time
import traceback

import numpy
import datadoc
import scipy.ndimage.filters

import editor
import viewerWindow
import viewControlWindow
import dialogs
import histogram
import align
import alignProgressWindow
import util


## This class defines the primary window for the application, which is always
# open so long as the app is. Primarily, this window contains a set of tabs, 
# each of which corresponds to a single ControlPanel and contains controls 
# for modifying a single open MRC file. The actual views of the pixel data
# in the file are handled by the ControlPanel instance.
class MainWindow(wx.Frame):
    def __init__(self, title, parent=None, id=wx.ID_ANY):
        wx.Frame.__init__(self, parent, id, title, style=wx.DEFAULT_FRAME_STYLE | wx.BORDER_SUNKEN, size=wx.Size(625, 540))

        self.auiManager = wx.aui.AuiManager()
        self.auiManager.SetManagedWindow(self)
        wx.MenuBar.SetAutoWindowMenu(False)  # disable "Windows" menu
        self.menuBar = wx.MenuBar()

        fileMenu = wx.Menu()
        self.menuBar.Append(fileMenu, 'File')
        util.addMenuItem(self, fileMenu, '&Open...\tCtrl+O', self.OnFileOpen)
        util.addMenuItem(self, fileMenu, '&Save\tCtrl+S', self.OnFileSave)
        util.addMenuItem(self, fileMenu, '&Save As...\tCtrl+Shift+S', self.OnFileSaveAs)
        fileMenu.AppendSeparator()
        util.addMenuItem(self, fileMenu, '&Load parameters...\tCtrl+L',
                self.OnLoadParams)
        util.addMenuItem(self, fileMenu, '&Export parameters...\tCtrl+E',
                self.OnExportParams)
        util.addMenuItem(self, fileMenu, '&Quit\tCtrl+Q', 
                self.OnQuit)

        viewMenu = wx.Menu()
        self.menuBar.Append(viewMenu, 'View')
        viewMenu.AppendSeparator()
        util.addMenuItem(self, viewMenu, '&Show view controls\tCtrl+T', 
                self.OnViewControls)

        editMenu = wx.Menu()
        self.menuBar.Append(editMenu, 'Edit')
        util.addMenuItem(self, editMenu, '&Auto align...', self.OnAutoAlign)
        util.addMenuItem(self, editMenu, '&Split/Merge/Reorder...', self.OnSplitMerge)
        util.addMenuItem(self, editMenu, '&Project/Resize...', self.OnProjResize)
        util.addMenuItem(self, editMenu, '&Batch process...\tCtrl+B',
                self.OnBatchProcess)

        helpMenu = wx.Menu()
        self.menuBar.Append(helpMenu, 'Help')
        item = wx.MenuItem(helpMenu, wx.ID_ABOUT, '&About OMX Editor')
        self.Bind(wx.EVT_MENU, self.OnAbout, id = wx.ID_ABOUT)
        helpMenu.AppendItem(item)

        self.SetMenuBar(self.menuBar)
        self.auiManager.AddPane(self.CreateNotebook(), wx.aui.AuiPaneInfo().CloseButton(False).CenterPane())
        self.auiManager.Update()

        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnNotebookPageChange)

        self.statbar = self.CreateStatusBar(2)  # status bar (mouse pos etc.)

        self.SetDropTarget(FileDropper(self))  # upper area of window
        self.controlPanelsNotebook.SetDropTarget(FileDropper(self))  # main area

        self.origPos = self.GetPosition() # use when opening new files


    ## Exit the program.
    def OnQuit(self, event = None):
        self.Destroy()

        
    def CreateNotebook(self):
        self.controlPanelsNotebook = wx.aui.AuiNotebook(self, wx.ID_ANY, style=wx.aui.AUI_NB_DEFAULT_STYLE | wx.aui.AUI_NB_WINDOWLIST_BUTTON | wx.aui.AUI_NB_TAB_FIXED_WIDTH)

        if sys.platform == 'linux2':
            self.controlPanelsNotebook.SetNormalFont(wx.NORMAL_FONT)
            self.controlPanelsNotebook.SetSelectedFont(wx.NORMAL_FONT)  # do not use bold for selected tab
            self.controlPanelsNotebook.SetMeasuringFont(wx.NORMAL_FONT)
        return self.controlPanelsNotebook

    def OnFileOpen(self,event = None):
        dialog = wx.FileDialog(self, "Please select a file to open", 
                               style = wx.FD_OPEN | wx.FD_MULTIPLE)
        if dialog.ShowModal() == wx.ID_OK:
            for file in dialog.GetPaths():
                self.openFile(file)

    def OnFileSave(self,event):
        curPanel = self.getCurPanel()
        if curPanel is None:
            return

        pageIndex = self.controlPanelsNotebook.GetSelection()

        # gb, Oct2012 - change save path if we have align or crop params
        currPath = curPanel.getFilePath()
        targetPath = self.updatePath(currPath,curPanel)
        permission = wx.CANCEL
        if targetPath == currPath:
            permission = wx.MessageBox("Overwrite %s?" % targetPath, 
                 "Please confirm", 
                 style = wx.OK | wx.CANCEL)
        else:
            permission = wx.OK
        if permission != wx.OK:
            return
                
        curPanel.dataDoc.alignAndCrop(savePath = targetPath)

        doc_to_edit = datadoc.DataDoc(targetPath)

        self.controlPanelsNotebook.DeletePage(pageIndex)
        self.controlPanelsNotebook.InsertPage(pageIndex, 
                controlPanel.ControlPanel(self, doc_to_edit),
                os.path.basename(targetPath), select=True)

    # gb, Oct2012 - check if crop/align params non-default - update save name
    def updatePath(self,currPath,curPanel):
        """
        Check whether Crop or Align parameters imply changes -
        if so, modify save path accordingly (_ECR=cropped, _EAL=algined).
        """
        # use existing file root, and .dv extension
        pathBase = os.path.splitext(currPath)[0]
        fileExt = ".dv"
        tags = ""
        doc = self.getCurPanel().dataDoc
        # 1. Will any cropping take place?
        startMin = numpy.array([0, 0, 0, 0, 0], numpy.int32)
        startMax = numpy.array(doc.size, numpy.int32)
        if (set(doc.cropMin) != set(startMin)) or \
            (set(doc.cropMax) != set(startMax)):
            tags = tags + "_ECR"
        # 2. Will any alignment take place?
        alignParams = doc.alignParams
        for wavelength in xrange(doc.numWavelengths):   
            dx, dy, dz, angle, zoom = alignParams[wavelength]          
            if dz and self.size[2] == 1:                                    
                dz = 0  # Chris' HACK: no Z translate in 2D files
            if dx or dy or dz or angle or zoom != 1:                        
                tags = tags + "_EAL"
                break
        return pathBase + tags + fileExt


    def OnFileSaveAs(self,event):
        curPanel = self.getCurPanel()
        if curPanel is None:
            return
        
        pageIndex = self.controlPanelsNotebook.GetSelection()

        caption = self.controlPanelsNotebook.GetPageText(pageIndex)
        fd = wx.FileDialog(self, "Save as ...",
                           caption, caption,
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if fd.ShowModal() == wx.ID_OK:
            targetPath = fd.GetPath()
            curPanel.dataDoc.alignAndCrop(savePath = targetPath)
            doc_to_edit = datadoc.DataDoc(targetPath)
            self.controlPanelsNotebook.AddPage(
                    ControlPanel(self, doc_to_edit),
                    os.path.basename(targetPath), select=True)


    ## This would be a decorator function if I could find a non-hacky way to 
    # do decorators of instance methods, but since I can't, it just pops up a
    # message dialog if the user hasn't opened a file yet, and otherwise
    # returns True.
    def requireOpenFile(self):
        if not self.controlPanelsNotebook.GetPageCount():
            wx.MessageDialog(self,
                    "Please open a file first.",
                    "No open file to operate on.",
                    wx.ICON_ERROR | wx.OK | wx.STAY_ON_TOP).ShowModal()
            return False
        return True


    ## Show the view controls window.
    def OnViewControls(self, event):
        if self.requireOpenFile():
            self.getCurPanel().toggleViewsWindow()


    ## Passthrough to the current panel.
    def OnAutoAlign(self, event):
        if self.requireOpenFile():
            self.getCurPanel().autoAlign()


    ## Passthrough to the current panel.
    def OnSplitMerge(self, event):
        if self.requireOpenFile():
            dialogs.SplitMergeDialog(
                    self.getCurPanel(), self.getCurPanel().dataDoc)


    ## Passthrough to the current panel.
    def OnProjResize(self, event):
        if self.requireOpenFile():
            dialogs.ProjResizeDialog(
                self.getCurPanel(), self.getCurPanel().dataDoc)
    

    ## Passthrough to the current panel.
    def OnLoadParams(self, event):
        if self.requireOpenFile():
            self.getCurPanel().loadParameters()

    
    ## Passthrough to the current panel.
    def OnExportParams(self, event):
        if self.requireOpenFile():
            self.getCurPanel().exportParameters()


    ## Create a BatchDialog instance.
    def OnBatchProcess(self, event):
        if self.requireOpenFile():
            dialogs.BatchDialog(self, self.getCurPanel())

    
    def OnAbout(self, event = None):
        wx.MessageDialog(self, 
                "This program is for viewing and editing MRC files. It " +
                "allows you to align data across wavelengths, crop out " + 
                "unnecessary pixels, and view the data from many different " +
                "perspectives. Alignment and cropping parameters can also " + 
                "be exported for use in the OMX Processor program.\n\n" + 
                "Copyright 2012 Sedat Lab, UCSF.\n" +
                "(this version has been customized by Micron Oxford)",
                "About OMX Editor", 
                wx.ICON_INFORMATION | wx.OK | wx.STAY_ON_TOP).ShowModal()


    ## Retrieve the currently active panel, or None if no panel exists.
    def getCurPanel(self):
        pageIndex = self.controlPanelsNotebook.GetSelection()
        if pageIndex >= 0:
            return self.controlPanelsNotebook.GetPage(pageIndex)
        return None

                
    def openFile(self, filename):
        ## if this file is already open, just go to that tab and return
        for i in range(self.controlPanelsNotebook.GetPageCount()):
            if filename == self.controlPanelsNotebook.GetPage(i).getFilePath():
                self.controlPanelsNotebook.SetSelection(i)
                return

        if os.path.isdir(filename):
            return # Do nothing for directories
        else:
            try:
                doc_to_edit = datadoc.DataDoc(filename) 
            except Exception, e:
                wx.MessageDialog(None, 
                        "Failed to open file: %s\n\n%s" % (e, traceback.format_exc()), 
                        "Error", wx.OK).ShowModal()
                return

            newPanel = ControlPanel(self, doc_to_edit)
            self.controlPanelsNotebook.AddPage(
                    newPanel,
                    os.path.basename(filename), select=True)


    def OnNotebookPageChange(self, event):
        # Hide windows used by the previous panel.
        prevPage = event.GetOldSelection()
        if prevPage >= 0:
            self.controlPanelsNotebook.GetPage(prevPage).setWindowVisibility(False)

        new_page = event.GetSelection()
        controlPanel = self.controlPanelsNotebook.GetPage(new_page)
        controlPanel.setWindowVisibility(True)
        self.statbar.SetFieldsCount(controlPanel.dataDoc.numWavelengths)

    def getDocs(self):
        """ 
        Returns an up-to-date list of DataDoc references for all open files.
        """
        dataDocs = []
        for i in range(self.controlPanelsNotebook.GetPageCount()):
            panel = self.controlPanelsNotebook.GetPage(i)
            doc = panel.dataDoc
            dataDocs.append(doc)
        return dataDocs


## A simple class to handle dragging and dropping files onto the main window.
class FileDropper(wx.FileDropTarget):
    def __init__(self, parent):
        wx.FileDropTarget.__init__(self)
        self.parent = parent


    ## Open the dropped files, in reverse order because they seem to be handed
    # to us backwards.
    def OnDropFiles(self, x, y, filenames):
        for file in filenames[::-1]:
            self.parent.openFile(file)



## This panel provides an interface for viewing and editing an MRC file
class ControlPanel(wx.Panel):
    def __init__(self, parent, imageDoc,
                 id = wx.ID_ANY, pos = wx.DefaultPosition,
                 size = wx.DefaultSize):
        wx.Panel.__init__(self, parent, id, style=wx.SP_NOBORDER)
        self.parent = parent

        self.shouldProject = False
        ## Contains all the information on the displayed image
        self.dataDoc = imageDoc
        # list of channel color tuples (default white before updating)
        self.colors = [(1, 1, 1,) for x in range(self.dataDoc.numWavelengths)]

        ## Which wavelengths are controlled by the mouse
        self.mouseControlWavelengths = [False] * self.dataDoc.numWavelengths
        self.mouseControlWavelengths[0] = True
        ## Tracks position of the mouse when it was clicked down, for 
        # transforming the image data
        self.initialMouseLoc = None
        ## Original alignment parameters before the user started dragging 
        # the image around.
        self.initialAlignParams = None

        ## Maps wavelength index to whether or not we're done aligning it, 
        # so we know when alignment has finished.
        self.alignedWavelengths = dict()

        ## Whether or not we are currently showing a "preview crop" of the
        # image.
        self.isViewCropped = False
        
        ## List of windows holding different views of the data.
        self.windows = []
        # Check out DataDoc.size for the ordering of these axes.
        axes = [(4, 3)]
        if self.dataDoc.size[2] > 1:
            # Have more than one Z slice, so show the Z views.
            axes.extend([(4, 2), (2, 3)])
        for axesPair in axes:
            self.windows.append(viewerWindow.ViewerWindow(self, 
                            axes = axesPair,
                            dataDoc = self.dataDoc,
                    )
            )

        # Adjust window positions - parent moved right for new window0
        base = self.parent.origPos
        self.windows[0].SetPosition( base )
        rect = self.windows[0].GetRect()
        self.windows[0].SetPosition( (rect[0]-rect[2], rect[1]) )
        if len(self.windows) > 1:
            # We have the XZ and YZ views, so we need to position them too.
            self.windows[1].SetPosition( (rect[0]-rect[2], rect[1] + rect[3]) )
            rect2 = self.windows[2].GetRect()
            self.windows[2].SetPosition( (rect[0]-rect[2]-rect2[2], rect[1]) )
        # move the parent last because the other windows move with it (Mac)
        self.parent.SetPosition( (rect[0]+rect[2], rect[1]) )

        self.setParentSize()

        ## List of canvases showing actual pixels, held in each window.
        self.viewers = [window.viewer for window in self.windows]

        # Set up mouse events for the viewers so the user can control 
        # alignment parameters by dragging.
        for viewer in self.viewers:
            viewer.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)

        ## Maps axis pairs to the projection mode for the corresponding viewer.
        self.axesToProjectionMap = dict()
        for viewer in self.viewers:
            self.axesToProjectionMap[viewer.axes] = None

        ## Lock around self.updateGLGraphics so we don't try to update it
        # while already updating.
        self.displayUpdateLock = threading.Lock()

        self.updateGLGraphics()

        wx.CallAfter(self.autoFitHistograms)

        # Set up the panel layout.
        ## Sizer to hold the panel layout.
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        rowSizer.Add(self.makeCropPanel())
        rowSizer.Add(self.makeHelpPanel())
        self.sizer.Add(rowSizer)

        self.sizer.Add(self.makeWavelengthPanels())

        ## Maps axes to whether or not the corresponding views are visible, 
        # for the views that aren't shown by default.
        self.axesToVisibilityMap = dict()
        for viewer in self.viewers:
            self.axesToVisibilityMap[viewer.axes] = True

        ## Allows user to customize the views they see, e.g. add kymographs,
        # or take projections of views.
        self.viewControlWindow = viewControlWindow.ViewControlWindow(self,
                self.dataDoc,
                title = 'View Controls',
                style = wx.RESIZE_BORDER | wx.CAPTION)
        self.viewControlWindow.SetPosition((10, 40))
        self.viewControlWindow.Hide()

        ## We need to track the visibility of the views window, so we know
        # whether or not to show it when we get focus.
        self.wasViewsWindowShown = False

        self.SetSizerAndFit(self.sizer)

        # Allow use of numpad keys to change the slice lines.
        accelTable = []
        for code, offset in util.KEY_MOTION_MAP.iteritems():
            id = wx.NewId()
            accelTable.append((wx.ACCEL_NORMAL, code, id))
            self.Bind(wx.EVT_MENU, lambda event, code = code: self.onKey(code),
                    id = id)

        # Auto-rescale the histograms to match the current XY view.
        id = wx.NewId()
        accelTable.append((wx.ACCEL_NORMAL, wx.WXK_NUMPAD_MULTIPLY, id))
        self.Bind(wx.EVT_MENU, lambda event: self.autoFitHistogramsXY(), id = id)
        table = wx.AcceleratorTable(accelTable)
        self.SetAcceleratorTable(table)

        ## Window holding display of auto-alignment progress
        self.alignProgressWindow = None

        ## So we can close our window if necessary.
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        ## Get the viewers' min/max values initialized properly.
        self.setViewerScalings()


    ## Make the panel for cropping.
    def makeCropPanel(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.cropControlPanel = CropControlPanel(
                parent = panel, helpFunc = self.prepHelpText,
                dimensions = self.dataDoc.size[1:][::-1],
                textChangeCallback = self.updateCrop,
                toggleCropCallback = self.toggleCrop,
        )
        sizer.Add(self.cropControlPanel, 0, wx.LEFT, 10)
        panel.SetSizerAndFit(sizer)
        return panel

    
    ## Make the panel that holds alignment parameter panels for all
    # wavelengths, as well as the wavelength histograms. This also creates 
    # self.alignParamsPanels, self.alignSwapButtons, and self.histograms
    def makeWavelengthPanels(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.alignParamsPanels = []
        #self.alignSwapButtons = []

        self.histograms = []
        # For generating the histograms.
        dataSlice = self.dataDoc.takeDefaultSlice((1, 2), False)

        for wavelength in range(self.dataDoc.numWavelengths):
            # Create the panels containing the alignment parameters for each
            # wavelength
            rowSizer = wx.BoxSizer(wx.HORIZONTAL)

            # This sizer holds the label, swap button, and histogram.
            columnSizer = wx.BoxSizer(wx.VERTICAL)

            # gb, Oct2012 - should really rename all wavelength names to channel
            #   "wavelength" below is just an arbitrary channel number
            trueWavelength = self.dataDoc.channelWaves[wavelength]
            label = wx.StaticText(panel, -1, 
                    "Channel %d (%d nm)" % (wavelength, trueWavelength) )
            columnSizer.Add(label, 0, wx.ALL, 3)

            # Holds the swap and visibility buttons.
            buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

            toggleButton = wx.ToggleButton(panel, -1, label = "On/Off")
            self.prepHelpText(toggleButton, "Toggle On/Off",
                    "Click to toggle visibility for this wavelength.")
            toggleButton.SetValue(True)
            toggleButton.Bind(wx.EVT_TOGGLEBUTTON, 
                    lambda event, wavelength = wavelength: self.toggleWavelengthVisibility(wavelength))
            buttonSizer.Add(toggleButton, 0, wx.ALL, 3)

            columnSizer.Add(buttonSizer)

            color = util.waveToRGB(self.dataDoc.channelWaves[wavelength])
            self.colors[wavelength] = color
            newHistogram = histogram.HistogramPanel(panel, 
                    self.changeHistScale, self.setHelpText, 
                    wavelength, dataSlice[wavelength], color, 
                    size = (176, 40)
            )
            self.histograms.append(newHistogram)
            columnSizer.Add(newHistogram)

            for viewer in self.viewers:
                viewer.setColor(wavelength, color)

            rowSizer.Add(columnSizer)
            
            initialParams = self.dataDoc.getAlignParams(wavelength)
            # This is called when parameters are changed.
            changeCallback = lambda wavelength = wavelength: self.setAlignParams(wavelength)
            # This is called when the checkbox to modify parameters with the 
            # mouse is clicked.
            checkCallback = lambda wavelength = wavelength: self.setMouseControl(wavelength)
            # This is called when the radio button to use this wavelength as
            # the alignment reference is clicked.
            radioCallback = lambda wavelength = wavelength: self.setAlignReference(wavelength)
            paramsPanel = AlignParamsPanel(panel, self.prepHelpText,
                    initialParams, changeCallback, checkCallback, radioCallback,
                    isFirstPanel = wavelength == 0, 
                    style = wx.BORDER_SUNKEN)
            self.alignParamsPanels.append(paramsPanel)

            rowSizer.Add(paramsPanel, 0, wx.LEFT | wx.BOTTOM, 5)
            sizer.Add(rowSizer, 0, wx.LEFT, 10)

        # Row of buttons.
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        autoAlignButton = wx.Button(panel, -1, "Auto-align")
        self.prepHelpText(autoAlignButton, "Auto-align",
                "Run a Simplex algorithm to attempt to automatically " +
                "align each wavelength with the first. This will take " +
                "some time."
        )
        autoAlignButton.Bind(wx.EVT_BUTTON, self.autoAlign)
        rowSizer.Add(autoAlignButton, 0, wx.LEFT | wx.BOTTOM, 10)

        exportButton = wx.Button(panel, -1, "Export param")
        self.prepHelpText(exportButton, "Export parameters",
                "Generate a file that contains the alignment and cropping " +
                "parameters for this file, so that they may be loaded " +
                "later (NB. alignment parameters saved in Microns)."
        )
        exportButton.Bind(wx.EVT_BUTTON, self.exportParameters)
        rowSizer.Add(exportButton, 0, wx.LEFT | wx.BOTTOM, 10)

        loadButton = wx.Button(panel, -1, "Load param")
        self.prepHelpText(loadButton, "Load parameters",
                "Load a previously-generated file describing how to crop " +
                "and align data."
        )
        loadButton.Bind(wx.EVT_BUTTON, self.loadParameters)
        rowSizer.Add(loadButton, 0, wx.LEFT | wx.BOTTOM, 10)

        batchButton = wx.Button(panel, -1, "Batch process")
        self.prepHelpText(batchButton, "Batch process",
                "Apply these cropping and/or alignment parameters to " +
                "a large number of files."
        )
        batchButton.Bind(wx.EVT_BUTTON, lambda event: dialogs.BatchDialog(
                self.parent, self))
        rowSizer.Add(batchButton, 0, wx.LEFT | wx.BOTTOM, 10)
        splitMergeButton = wx.Button(panel, -1, "Split/Merge")
        self.prepHelpText(splitMergeButton, "Split/Merge data", 
                "Split, Merge or Re-order data - merge not yet implemented."
        )
        splitMergeButton.Bind(wx.EVT_BUTTON, lambda event: dialogs.SplitMergeDialog(
                self, self.dataDoc))
        rowSizer.Add(splitMergeButton, 0, wx.LEFT | wx.BOTTOM, 10)
        projResizeButton = wx.Button(panel, -1, "Proj/Resize")
        self.prepHelpText(projResizeButton, "Project/Resize data", 
                "When finished, will allow averaging of phases & angles of " + 
                "raw SI data, and/or rescaling of the result. This should " +
                "facilitate merging and comparison of SI and wide-field " +
                "data for a given sample. Not yet implemented!"
        )
        projResizeButton.Bind(wx.EVT_BUTTON, lambda event: dialogs.ProjResizeDialog(
                self, self.dataDoc))
        rowSizer.Add(projResizeButton, 0, wx.LEFT | wx.BOTTOM, 10)

        sizer.Add(rowSizer)
        panel.SetSizerAndFit(sizer)
        return panel


    ## Make a panel for showing helpful text to the user.
    def makeHelpPanel(self):
        panel = wx.Panel(self, -1, style = wx.BORDER_SUNKEN)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.infoText = wx.StaticText(panel, -1, ' ' * 600)
        self.infoText.Wrap(350)
        sizer.Add(self.infoText)
        panel.SetSizerAndFit(sizer)
        # Ensure the panel never shrinks.
        panel.SetMinSize(panel.GetSize())
        return panel


    ## Update the text in the help panel.
    def setHelpText(self, title, text):
        self.infoText.SetLabel("%s\n%s" % (title, text))
        self.infoText.SetMinSize((300, 200))
        self.infoText.Wrap(300)


    ## Set up a form input to show text in our help panel when the user
    # mouses over it.
    def prepHelpText(self, item, title, text):
        item.Bind(wx.EVT_MOTION, lambda event: self.setHelpText(title, text))


    ## Passthrough to the viewers to update their scalings.
    def changeHistScale(self, wavelength, minVal, maxVal):
        for viewer in self.viewers:
            viewer.changeHistScale(wavelength, minVal, maxVal)


    ## Passthrough to the viewers to toggle the visibility of wavelengths.
    def toggleWavelengthVisibility(self, wavelength):
        for viewer in self.viewers:
            viewer.toggleVisibility(wavelength)


    ## Cause the histograms to automatically fit themselves to the current
    # data; call this after the user has changed which data is shown.
    def autoFitHistograms(self):
        for histogram in self.histograms:
            histogram.autoFit()


    ## Rescale the histograms to fit just the current XY view.
    def autoFitHistogramsXY(self, event = None):
        targetCoords = self.dataDoc.getSliceCoords((1, 2))
        image = self.dataDoc.takeSlice(targetCoords)
        for wavelength, histogram in enumerate(self.histograms):
            histogram.autoFitToImage(image[wavelength])
        wx.CallAfter(self.setViewerScalings)


    ## Update the viewer min/max scale to match the histogram.
    def setViewerScalings(self):
        for wavelength in xrange(self.dataDoc.numWavelengths):
            minVal, maxVal = self.histograms[wavelength].getMinMax()
            for viewer in self.viewers:
                viewer.changeHistScale(wavelength, minVal, maxVal)


    ## This function is invoked when the user changes the alignment parameters.
    def setAlignParams(self, index):
        tx, ty, tz, rot, mag = self.alignParamsPanels[index].getParamsList()
        # first move and rotate image of colorId in x-y view
        self.viewers[0].changeImgOffset(index, tx, ty, rot, mag, False)
        self.viewers[1].changeImgOffset(index, tx, tz, 0, mag, False)
        self.viewers[2].changeImgOffset(index, tz, ty, 0, mag, False)

        # remember, 'mag' should only apply to lateral dimensions, therefore
        # viewers[1] and viewers[2] needs different aspect ratios in x and y (see OnPaint())
            
        # then update the sliced sections because of the translations (tx, ty, tz)
        self.dataDoc.setAlignParams(index, (tx, ty, tz, rot, mag))
        # Alignment parameters have changed, so we need to update our images.
        self.updateGLGraphics()
        self.setViewerScalings()


    ## Toggle whether or not a given wavelength can be manipulated with 
    # the mouse.
    def setMouseControl(self, index):
        self.mouseControlWavelengths[index] = not self.mouseControlWavelengths[index]


    ## Change which wavelength is used as the reference for aligning.
    def setAlignReference(self, index):
        for i, panel in enumerate(self.alignParamsPanels):
            panel.setReferenceControl(i == index)


    ## Close our alignment progress window, if any.
    def OnClose(self, event = None):
        if self.alignProgressWindow is not None:
            self.alignProgressWindow.Destroy()
            self.alignProgressWindow = None


    ## Get the current view index for the given axis.
    def getViewAxisIndex(self, axis):
        return self.dataDoc.curViewIndex[axis]


    def OnMouse(self, event):
        viewer = event.GetEventObject()
        viewer.OnMouse(event)
        if viewer.getIsMouseBusy():
            # Don't do anything else with mouse events as long as the cropbox
            # or slicelines are being manipulated.
            return
        clickLoc = numpy.array(event.GetPosition())
        # The axes modified by dragging in X and Y. Here we convert from
        # DataDoc indices (WTZYX) to align params indices (XYZ)
        xDir = 4 - viewer.axes[0]
        yDir = 4 - viewer.axes[1]
        if ((event.LeftDown() or event.RightDown()) and 
                self.initialMouseLoc is None):
            # Mouse clicked down; set the initial location and store our current
            # parameters so we can move relative to them.
            self.initialMouseLoc = numpy.array(clickLoc)
            self.initialAlignParams = [panel.getParamsList() for panel in self.alignParamsPanels]
        if ((event.LeftIsDown() or event.RightIsDown()) and
                self.initialMouseLoc is not None):
            # Either translate or rotate the image
            params = numpy.array(self.initialAlignParams)
            delta = clickLoc - self.initialMouseLoc
            
            if event.LeftIsDown():
                # Translate, while accounting for the current image rotation
                magnitude = numpy.sqrt(numpy.vdot(delta, delta))
                transAngle = numpy.arctan2(delta[1], delta[0])
                for i, isControlled in enumerate(self.mouseControlWavelengths):
                    if isControlled:
                        curAngle = params[i][3] * numpy.pi / 180.0
                        delta[0] = numpy.cos(curAngle + transAngle) * magnitude
                        delta[1] = numpy.sin(curAngle + transAngle) * magnitude
                        params[i][xDir] += delta[0]
                        params[i][yDir] -= delta[1]
            elif event.RightIsDown() and viewer.axes == (4, 3):
                # Rotate instead.
                for i, isControlled in enumerate(self.mouseControlWavelengths):
                    if isControlled:
                        imageCenter = numpy.array([self.dataDoc.size[4], self.dataDoc.size[3]]) / 2.0
                        initialVector = self.initialMouseLoc - imageCenter
                        initialAngle = numpy.arctan2(initialVector[1], initialVector[0])
                        curVector = clickLoc - imageCenter
                        curAngle = numpy.arctan2(curVector[1], curVector[0])
                        delta = initialAngle - curAngle
                        params[i][3] -= delta * 180 / numpy.pi

            for i, paramSet in enumerate(params):
                if self.mouseControlWavelengths[i]:
                    self.alignParamsPanels[i].setParams(paramSet)
                    self.setAlignParams(i)
            
        else:
            # No more mouse buttons down.
            self.initialMouseLoc = None


    ## Generate an array of data that's been normalized to the range [0, 1] 
    # and filtered by our histograms so values below/above the histogram
    # min/max are set to 0/1.
    def getFilteredData(self, wavelength, perpendicularAxes = (1, 2)):
        targetCoords = self.dataDoc.getSliceCoords(perpendicularAxes)
        baseData = self.dataDoc.takeSlice(targetCoords).astype(numpy.float)[wavelength]
        
        dataMin = baseData.min()
        dataMax = baseData.max()
        histogram = self.histograms[wavelength]
        minCut, maxCut = histogram.getMinMax()
        # This is an order of magnitude faster than using 
        # scipy.ndimage.filters.generic_filter.
        baseData[numpy.where(baseData < minCut)] = dataMin
        baseData[numpy.where(baseData > maxCut)] = dataMax
        baseData = (baseData - dataMin) / (dataMax - dataMin)

        return baseData


    ## Use the Simplex method to automatically align the different wavelengths.
    def autoAlign(self, event = None):
        referenceIndex = self.getReferenceWavelength()

        wavelengthsToAlign = range(self.dataDoc.numWavelengths)
        del wavelengthsToAlign[referenceIndex]
        
        # This datastructure will allow us to track which wavelengths have 
        # finished aligning.
        self.alignedWavelengths = dict([(i, False) for i in wavelengthsToAlign])

        # Calculate the 2D XY reference array
        targetCoords = self.dataDoc.getSliceCoords((1, 2))
        referenceData = self.getFilteredData(referenceIndex)

        self.alignProgressWindow = alignProgressWindow.AlignProgressWindow(
                self, self.dataDoc.numWavelengths)
        self.alignProgressWindow.Show()

        for i in wavelengthsToAlign:
            if i == referenceIndex:
                continue
            
            guess = self.alignParamsPanels[i].getParamsList()

            # Only apply automatic guess adjustment if the user hasn't made
            # their own adjustments already, to either the given data or 
            # the reference data.
            shouldAdjustGuess = True
            referenceParams = self.alignParamsPanels[referenceIndex].getParamsList()
            for j, val in enumerate([0, 0, 0, 0, 1]):
                if (abs(guess[j] - val) > .01 or 
                        abs(referenceParams[j] - val) > .01):
                    shouldAdjustGuess = False
                    break

            aligner = align.SimplexAlign(self, referenceData, i, guess,
                    shouldAdjustGuess = shouldAdjustGuess)


    ## Return the wavelength being used as a reference (i.e. the wavelength
    # that is held fixed, and that the other wavelengths adjust themselves 
    # to when auto-aligning).
    def getReferenceWavelength(self):
        for i, panel in enumerate(self.alignParamsPanels):
            if panel.shouldUseAsReference():
                return i


    ## Retrieve the 3D array for the specified wavelength, in addition to 
    # our reference wavelength, and pass them back to the worker.
    @util.callInMainThread
    def getFullVolume(self, wavelength, worker):
        reference = self.getReferenceWavelength()
        result = self.dataDoc.alignAndCrop(
                wavelengths = [reference, wavelength], 
                timepoints = [self.dataDoc.curViewIndex[1]])
        # Take the first timepoint.
        worker.setVolumes(result[0][0], result[1][0])


    ## Update the status text to show the user how auto-alignment is going.
    @util.callInMainThread
    def updateAutoAlign(self, startingCost, currentCost, wavelength):
        self.alignProgressWindow.newData(wavelength, currentCost)


    ## Receive notification from one of the aligner threads that it's now
    # working on Z alignment.
    def alignSwitchTo3D(self, wavelength):
        self.alignProgressWindow.switchTo3D(wavelength)


    ## Receive notification from one of the aligner threads that it's all 
    # done.
    @util.callInMainThread
    def finishAutoAligning(self, result, wavelength):
        self.alignedWavelengths[wavelength] = True
        # Check if we've done with alignment for all wavelengths
        amDone = True
        for i, done in self.alignedWavelengths.iteritems():
            if not done:
                amDone = False
                break
        if amDone:
            self.alignProgressWindow.finish()
        print "Got transformation",result,"for channel",wavelength
        self.alignParamsPanels[wavelength].setParams(result)
        self.setAlignParams(wavelength)


    ## The align progress frame has been destroyed, so we don't need to 
    # track it any more.
    def clearProgressFrame(self):
        self.alignProgressWindow = None


    ## Calculate the centers of the beads and find out how well we have 
    # aligned the different wavelengths.
    def checkAlignment(self):
        volumes = self.dataDoc.alignAndCrop(
                timepoints = [self.dataDoc.curViewIndex[1]]
        )
        beadCentersByWavelength = []
        for wavelength in xrange(self.dataDoc.numWavelengths):
            print "Processing channel",wavelength
            data = volumes[wavelength][0]
            # Normalize
            data = (data - data.min()) / (data.max() - data.min())
            # Remove a border around the edge to make our lives easier.
            data[:5,:5,:5] = 0
            data[-5:,-5:,-5:] = 0
            smoothed = scipy.ndimage.filters.gaussian_filter(data, 3)
            beadCenters = []
            c = 0
            # Arbitrarily ignore any beads that aren't at least half as bright
            # as the brightest bead.
            while numpy.max(data) > .5:
                # Find max in data, mark as bead, zero it and neighbors out.
                target = numpy.where(data == numpy.max(data))
                # May get multiple results; pick the first.
                target = numpy.array(target).T[0]
                beadCenters.append(target)
                # Zero out pixels near target.
                data[target[0] - 5:target[0] + 5,
                     target[1] - 5:target[1] + 5,
                     target[2] - 5:target[2] + 5] = 0
                c += 1
            print "Found",len(beadCenters),"beads"
            beadCentersByWavelength.append(beadCenters)
        
        distances = []
        zDistances = []
        offsets = []
        for center in beadCentersByWavelength[0]:
            # Find the closest bead in the next wavelength.
            bestDist = None
            bestAlt = None
            for alt in beadCentersByWavelength[1]:
                distance = numpy.linalg.norm(center - alt)
                if bestDist is None or distance < bestDist:
                    bestDist = distance
                    bestAlt = alt
            print "For center",center,"got best",bestDist,"from",bestAlt
            if bestDist < 10:
                distances.append(numpy.linalg.norm(center[1:] - bestAlt[1:]))
                zDistances.append(center[0] - bestAlt[0])
                offsets.append(center - bestAlt)
        offset = numpy.median(numpy.array(offsets), axis = 0)
        print "Median XY offset in pixels is",offset
        offset = numpy.array([offset[1], offset[0], 0])
        print "In microns it's",self.dataDoc.convertToMicrons(offset)
        print "Median Z is",numpy.median(numpy.array(zDistances))
        print "Average offset in pixels is",numpy.mean(numpy.array(offsets), axis = 0)


    ## Prompt the user for a location to save alignment and cropping
    # parameters, then generate the corresponding file.
    def exportParameters(self, event = None):
        defaultName = editor.resultName(self.dataDoc, 'saveAlignParameters')
        dialog = wx.FileDialog(self, "Where do you want to save the file?",
                os.path.dirname(self.dataDoc.filePath),
                defaultName,
                style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() != wx.ID_OK:
            return
        editor.saveAlignParameters(self.dataDoc, dialog.GetPath())


    ## Load a parameters file as generated by OnExportParameters
    def loadParameters(self, event = None):
        dialog = wx.FileDialog(self, "Please select the parameters file.",
                os.path.dirname(self.dataDoc.filePath),
                style = wx.FD_OPEN)
        if dialog.ShowModal() != wx.ID_OK:
            return
        
        handle = open(dialog.GetPath(), 'r')
        cropParams = [1] * 8
        cropLabelOrder = ['minX', 'maxX', 'minY', 'maxY', 'minZ', 'maxZ', 
                'minT', 'maxT']
        alignLabelOrder = ['dx', 'dy', 'dz', 'angle', 'zoom']
        alignParams = {}
        for line in handle:
            if 'crop' in line:
                match = re.search('crop-(.*): (.*)', line)
                field, value = match.groups()
                cropParams[cropLabelOrder.index(field)] = int(value)
            elif 'align' in line:
                match = re.search('align-(\d+)-(.*): (.*)', line)
                wavelength, field, value = match.groups()
                wavelength = int(wavelength)
                value = float(value)
                if wavelength not in alignParams:
                    alignParams[wavelength] = [0.0] * 5
                    # Set zoom to 1
                    alignParams[wavelength][4] = 1.0
                alignParams[wavelength][alignLabelOrder.index(field)] = value
        handle.close()
        
        # Check for users loading 2D cropping parameters.
        if cropParams[5] - cropParams[4] == 0:
            wx.MessageDialog(self,
                    "The Z cropping parameters are invalid; the file must " +
                    "have at least one Z slice. I am incrementing the Z " + 
                    "maximum by 1.",
                    "Invalid Z cropping parameters", 
                    wx.OK | wx.STAY_ON_TOP | wx.ICON_EXCLAMATION).ShowModal()
            cropParams[5] += 1
        self.cropControlPanel.setParams(cropParams)

        for wavelength, params in alignParams.iteritems():
            if wavelength < self.dataDoc.numWavelengths:
                # Go from microns to pixels
                params[:3] = self.dataDoc.convertFromMicrons(params[:3])
                self.alignParamsPanels[wavelength].setParams(params)
                self.setAlignParams(wavelength)
        self.updateCrop()


    ## Re-generate our various views from the data. 
    # We need a lock around this function as a whole so that
    # we don't get concurrent view-update calls.
    # Can't do this in parallel because the OpenGL calls aren't threadsafe.
    def updateGLGraphics(self, viewsToUpdate = []):
        if not viewsToUpdate:
            viewsToUpdate = self.viewers

        with self.displayUpdateLock:
            # Update each viewer in sequence.
            for viewer in viewsToUpdate:
                self.updateViewerDisplay(viewer)


    ## Update the images displayed in the specified viewer by taking an 
    # appropriate slice out of the data. This can take some time, if the 
    # DataDoc has to do expensive transformations to retrieve the relevant
    # data.
    def updateViewerDisplay(self, viewer):
        # axes_set is the set of all axes that we use -- X, Y, Z, and time.
        axes_set = set((4, 3, 2, 1))
        axesNormal = list(axes_set.difference(set(viewer.axes)))
        targetCoords = self.dataDoc.getSliceCoords(axesNormal)
        # We can save processing power if we offload transformations to 
        # OpenGL whenever feasible. That basically is limited to the XY
        # slice when there's no Z translation, or the YZ/XZ slices when 
        # there's no transformation at all.
        shouldTransform = False
        if viewer.axes == (4, 3) and self.dataDoc.hasZMotion():
            shouldTransform = True
        elif viewer.axes != (4, 3) and self.dataDoc.hasTransformation():
            shouldTransform = True
            
        # Only do this if we've generated a full list of images already.
        if not shouldTransform and len(viewer.imgList) == self.dataDoc.numWavelengths:
            # Ensure that the viewer is applying its own transformations.
            for wavelength in xrange(self.dataDoc.numWavelengths):
                dx, dy, dz, angle, zoom = self.alignParamsPanels[wavelength].getParamsList()
                # NB this only works because we know that we only apply 
                # viewer transformations to the XY slice.
                viewer.changeImgOffset(wavelength, dx, dy, angle, zoom, False)

        # If necessary, take a projected slice.
        imageSlice = None
        if (viewer.axes in self.axesToProjectionMap and 
                self.axesToProjectionMap[viewer.axes]):
            imageSlice = self.dataDoc.takeProjectedSlice(targetCoords, self.axesToProjectionMap[viewer.axes], shouldTransform)
        else:
            imageSlice = self.dataDoc.takeSlice(targetCoords, shouldTransform)
            
        # HACK: For now, transpose the YZ view so Y is vertical. Later we
        # want to make this a property of the viewer
        if viewer.axes == (2, 3):
            imageSlice = imageSlice.transpose(0, 2, 1)
        viewer.addImgL(imageSlice)
        
        if shouldTransform:
            # OpenGL transforms should not be used since the slice already
            # covers all that, so clear the viewer's transforms.
            for wavelength in xrange(self.dataDoc.numWavelengths):
                viewer.changeImgOffset(wavelength, 0, 0, 0, 1, False)

        for i in xrange(self.dataDoc.numWavelengths):
            viewer.setColor(i, self.colors[i])


    def getIsViewCropped(self):
        return self.isViewCropped


    ## Push a new set of cropping parameters to self.cropControlPanel, as 
    # received from one of our viewers when the user drags the crop box around.
    def updateCropboxEdit(self):
        newParams = []
        for i in xrange(4):
            newParams.append(self.dataDoc.cropMin[4 - i])
            newParams.append(self.dataDoc.cropMax[4 - i])
        self.cropControlPanel.setParams(newParams)
    

    ## Receive a new set of cropping parameters from self.cropControlPanel and
    # apply them to the data and our viewers.
    def updateCrop(self, event = None):
        params = self.cropControlPanel.getParams()
        for i in xrange(4):
            self.dataDoc.cropMin[4 - i] = params[i * 2]
            self.dataDoc.cropMax[4 - i] = params[i * 2 + 1]
        self.updateGLGraphics()
        wx.CallAfter(self.setViewerScalings)


    ## This callback is invoked by self.cropControlPanel when the "toggle crop"
    # button is clicked.
    def toggleCrop(self):
        self.isViewCropped = not self.isViewCropped
        self.refreshViewers()


    ## Add or remove a new viewer window with the specified axes.
    def toggleWindowVisibility(self, axes):
        if axes not in self.axesToVisibilityMap:
            # Never toggled this display before; add it now.
            self.axesToVisibilityMap[axes] = False
        self.axesToVisibilityMap[axes] = not self.axesToVisibilityMap[axes]
        if not self.axesToVisibilityMap[axes]:
            # Find the corresponding viewer and destroy it.
            for i, viewer in enumerate(self.viewers):
                if viewer.axes == axes:
                    del self.viewers[i]
                    self.windows[i].Destroy()
                    del self.windows[i]
                    break
        else:
            # Create a new viewer.
            newWindow = viewerWindow.ViewerWindow(self, axes, dataDoc = self.dataDoc)

            self.windows.append(newWindow)
            viewer = newWindow.viewer
            self.viewers.append(viewer)
            viewer.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)
            self.updateGLGraphics(viewsToUpdate = [viewer])
            self.setViewerScalings()
            self.viewControlWindow.Raise()


    ## Show/hide our views control window.
    def toggleViewsWindow(self):
        self.viewControlWindow.Show(not self.viewControlWindow.IsShown())
        self.wasViewsWindowShown = self.viewControlWindow.IsShown()


    ## Change the projection mode for the window with the specified axes.
    # \param axis Axis to project along, or None to disable projection.
    def setViewProjection(self, axes, axis):
        self.axesToProjectionMap[axes] = axis
        for viewer in self.viewers:
            if viewer.axes == axes:
                self.updateViewerDisplay(viewer)
                wx.CallAfter(self.setViewerScalings)


    ## Refresh all viewers.
    def refreshViewers(self):
        for viewer in self.viewers:
            viewer.Refresh(False)


    ## Retrieve the file this view loaded its data from.
    def getFilePath(self):
        return self.dataDoc.filePath


    ## Handle changing the slice lines.
    # \param offset A list of offsets to apply to each dimension in the data.
    def moveSliceLines(self, offset):
        self.dataDoc.moveSliceLines(offset)
        updatedViews = []
        # Find viewers that don't view along the axes modified by offset, 
        # since they'll need new arrays to display.
        for viewer in self.viewers:
            for axis, delta in enumerate(offset):
                if delta and axis not in viewer.axes:
                    updatedViews.append(viewer)
        # Inform our ViewsWindow about the new sliceline locations.
        self.viewControlWindow.setSliders(self.dataDoc.getSliceCoords())
        wx.CallAfter(self.updateGLGraphics, updatedViews)
        wx.CallAfter(self.setViewerScalings)


    ## As moveSliceLines, but instead of adding an offset, sets a specific
    # axis to a certain value.
    def setSliceLine(self, axis, target):
        curVal = self.dataDoc.curViewIndex[axis]
        delta = target - curVal
        if delta == 0:
            # Bogus call; do nothing.
            return
        offset = numpy.zeros(len(self.dataDoc.size))
        offset[axis] = delta
        self.moveSliceLines(offset)


    ## Process keypad inputs to move the slice lines around.
    def onKey(self, code):
        if code in util.KEY_MOTION_MAP:
            self.moveSliceLines(util.KEY_MOTION_MAP[code])


    ## Toggle the visibility of our child windows. If we become displayed,
    # ensure that our parent window is big enough to show all our controls.
    def setWindowVisibility(self, isVisible):
        for window in self.windows:
            window.Show(isVisible)
        # Only show the views window if we were showing it before we were
        # hidden earlier.
        self.viewControlWindow.Show(isVisible and self.wasViewsWindowShown)
        if isVisible:
            self.setParentSize()
            self.parent.Raise()


    ## Adjust the height of our parent so that it can contain all of our
    # wavelength controls.
    def setParentSize(self):
        self.parent.SetSize((-1, 250 + 111 * self.dataDoc.numWavelengths))


## This class is a small panel that contains alignment parameter controls 
# (X, Y, and Z translate; rotate about Z axis; zoom)
class AlignParamsPanel(wx.Panel):
    ## Instantiate the panel.
    # \param helpFunc Function to call to set up on-hover help display.
    # \param params Default values for alignment parameters.
    # \param isFirstPanel True if this is the first alignment panel to be 
    #        created; causes some controls to default to on.
    def __init__(self, parent, helpFunc, params, 
            changeCallback, checkCallback, radioCallback, 
            isFirstPanel = False, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)

        sizer = wx.BoxSizer(wx.VERTICAL)
        ## Initial parameters
        self.initialParams = list(params)

        ## Function to call when parameters are changed.
        self.changeCallback = changeCallback
        ## Function to call when mouse-control checkbox is clicked. 
        self.checkCallback = checkCallback
        ## Function to call when radio button is clicked.
        self.radioCallback = radioCallback

        ## List of text boxes, one for each parameter
        self.controls = []
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        columnSizer = wx.BoxSizer(wx.VERTICAL)
        # Arrange things so that Rotate and Zoom are in one column, and the
        # three translate parameters are in the other.
        for i, label in enumerate(['X translate (pixels)', 'Y translate (pixels)', 'Z translate (pixels)',
            'Rotate (degrees)', 'Zoom']):
            control = util.addLabeledInput(self, columnSizer, label = label,
                    defaultValue = str(params[i]),
                    style = wx.TE_PROCESS_ENTER,
                    size = (80, -1), minSize = (200, -1), border = 3,
                    shouldRightAlignInput = True)
            control.Bind(wx.EVT_TEXT_ENTER, lambda event: self.changeCallback())
            action = label.replace('ate', 'ation')
            helpFunc(control, label, 
                    "Set the %s parameter for alignment of this wavelength relative to the reference wavelength." % action)
            self.controls.append(control)
            if i == 2:
                # Start a new column
                rowSizer.Add(columnSizer)
                columnSizer = wx.BoxSizer(wx.VERTICAL)

        resetButton = wx.Button(self, -1, "Reset")
        resetButton.Bind(wx.EVT_BUTTON, self.resetParams)
        helpFunc(resetButton, "Reset", 
                "Resets all alignment parameters to their defaults"
        )
        columnSizer.Add(resetButton, 0, wx.ALIGN_RIGHT)

        rowSizer.Add(columnSizer)
        sizer.Add(rowSizer)
        
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        checkbox = wx.CheckBox(self, label = "Control with mouse")
        helpFunc(checkbox, "Control with mouse",
                "Allows you to manually align the image by " +
                "clicking and dragging the mouse. Use left-click to " +
                "translate, right-click to rotate."
        )
        checkbox.Bind(wx.EVT_CHECKBOX, lambda event: self.checkCallback())
        checkbox.SetValue(isFirstPanel)
        rowSizer.Add(checkbox)

        ## A radio button to let the user mark this specific wavelength as 
        # the one that other wavelengths are aligned against. Only one
        # wavelength can be so specified at a time, but since the radio buttons
        # are contained in separate panels, we have to turn them on and off
        # manually using self.radioCallback. Currently this is buggy in Linux,
        # so they have to be replaced by checkboxes there.
        self.shouldUseAsReferenceControl = wx.RadioButton(self, 
                -1, "Use as auto-alignment reference")
        helpFunc(self.shouldUseAsReferenceControl, 
                "Use as auto-alignment reference",
                "If set, then this wavelength is used as the fixed reference " +
                "wavelength that the other wavelengths attempt to align " + 
                "against, when running the Simplex auto-alignment process."
        )
        self.shouldUseAsReferenceControl.SetValue(isFirstPanel)
        self.shouldUseAsReferenceControl.Bind(wx.EVT_RADIOBUTTON, lambda event: self.radioCallback())
        rowSizer.Add(self.shouldUseAsReferenceControl, 0, wx.LEFT, 15)
        sizer.Add(rowSizer)
        self.SetSizerAndFit(sizer)


    ## Restore the params to default
    def resetParams(self, event = None):
        for i, param in enumerate(self.initialParams):
            self.controls[i].SetValue(str(param))
            self.changeCallback()

    ## Update to new set of parameters
    def setParams(self, params):
        for i, control in enumerate(self.controls):
            control.SetValue(str(params[i]))


    ## Retrieve parameters as a list [X, Y, Z, rotation, zoom].
    def getParamsList(self):
        return [float(control.GetValue()) for control in self.controls]


    ## Return whether or not this particular panel is for the wavelength that
    # is the reference wavelength for alignment
    def shouldUseAsReference(self):
        return self.shouldUseAsReferenceControl.GetValue()


    ## Set our radio button to the specified value
    def setReferenceControl(self, value):
        self.shouldUseAsReferenceControl.SetValue(value)


## This class provides an interface for manipulating the cropping controls.
class CropControlPanel(wx.Panel):
    ## Instantiate the panel.
    # \param helpFunc Function to call to set up on-hover help text.
    # \param dimensions Size of the image we are manipulating (determines 
    #        default cropping parameters).
    # \param toggleCropCallback Function to call when the "toggle crop" button
    #        is clicked.
    # \param textChangeCallback Function to call when the parameters are changed
    def __init__(self, parent, helpFunc, dimensions, toggleCropCallback, 
                 textChangeCallback, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, -1, "Crop parameters:"))
        self.controls = []
        index = 0
        # Create a 2x3 grid of text controls for setting the crop box volume.
        for dimension in ['X', 'Y', 'Z', 'T']:
            rowSizer = wx.BoxSizer(wx.HORIZONTAL)
            for mode in ['Min', 'Max']:
                defaultValue = '0'
                if index % 2:
                    # Is a maximum; use the image size
                    defaultValue = str(dimensions[index / 2])
                label = "%s %s:" % (dimension, mode)
                control = util.addLabeledInput(self, rowSizer, 
                        label = label,
                        size = (40, -1), minSize = (80, -1), border = 3,
                        shouldRightAlignInput = True,
                        defaultValue = defaultValue,
                        style = wx.TE_PROCESS_ENTER,
                )
                control.Bind(wx.EVT_TEXT_ENTER, lambda event: textChangeCallback())
                helpFunc(control, label, 
                        ("Set the %s extent for cropping in the %s direction." %
                        (mode.lower(), dimension)) +
                        " You can also adjust this by dragging the cropbox " +
                        "with the mouse.")
                self.controls.append(control)
                index += 1
            sizer.Add(rowSizer)
            rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizerAndFit(sizer)


    ## Retrieve the params as [minX, maxX, minY, maxY, minZ, maxZ]
    def getParams(self):
        strings = [control.GetValue() for control in self.controls]
        result = []
        for string in strings:
            if not string:
                result.append(0)
            else:
                result.append(int(float(string)))
        return result


    ## Update the crop parameters
    def setParams(self, params):
        for i, param in enumerate(params):
            self.controls[i].SetValue(str(param))

