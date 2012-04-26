import numpy
import os
import re
import scipy.ndimage.filters
import sys
import threading
import time
import wx

import alignParamsPanel
import alignProgressFrame
import batchDialog
import cropControlPanel
import datadoc
import histogram

import realign
import util
import imageViewer


## List of colors to assign to different wavelengths in the file.
COLORS_LIST = [
    (1, 0, 0), 
    (0, 1, 0), 
    (0, 0, 1), 
    (1, 1, 0), 
    (0, 1, 1), 
    (1, 0, 1), 
    (1, 1, 1), 
]


## Direction to move, in wavelength, T, Z, Y, X order, when the
# appropriate key is pressed. 46 for X, 28 for Y, 17 for Z, 39 for T.
KEY_MOTION_MAP = {
        wx.WXK_NUMPAD3: (0, -1, 0, 0, 0),
        wx.WXK_NUMPAD9: (0, 1, 0, 0, 0),
        wx.WXK_NUMPAD1: (0, 0, -1, 0, 0),
        wx.WXK_NUMPAD7: (0, 0, 1, 0, 0),
        wx.WXK_NUMPAD2: (0, 0, 0, -1, 0),
        wx.WXK_NUMPAD8: (0, 0, 0, 1, 0),
        wx.WXK_NUMPAD4: (0, 0, 0, 0, -1),
        wx.WXK_NUMPAD6: (0, 0, 0, 0, 1),
}

## Decorator function used to ensure that a given function is only called
# in wx's main thread.
def callInMainThread(func):
    def wrappedFunc(*args, **kwargs):
        wx.CallAfter(func, *args, **kwargs)
    return wrappedFunc


## This class provides an interface for viewing and performing basic 
# manipulations on MRC files.
class ControlPanel(wx.Panel):
    def __init__(self, parent, imageData,
                 id = wx.ID_ANY, pos = wx.DefaultPosition,
                 size = wx.DefaultSize):
        wx.Panel.__init__(self, parent, id, style=wx.SP_NOBORDER)
        self.parent = parent

        ## Contains all the information on the displayed image
        self.dataDoc = datadoc.DataDoc(imageData)

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
        for axesPair in [(4, 3), (4, 2), (3, 2)]: 
            self.windows.append(imageViewer.ViewerWindow(self, 
                            axes = axesPair,
                            dataDoc = self.dataDoc,
                    )
            )

        # Adjust window positions.
        base = self.parent.origPos
        self.windows[0].SetPosition(base)
        rect = self.windows[0].GetRect()
        self.windows[1].SetPosition((rect[0], rect[1] + rect[3]))
        self.windows[2].SetPosition((rect[0] + rect[2], rect[1]))
        rect = self.windows[2].GetRect()
        self.parent.SetPosition((rect[0], rect[1] + rect[3]))
        # Adjust height based on number of wavelengths
        self.parent.SetSize((-1, 330 + 111 * self.dataDoc.numWavelengths))

        ## List of canvases showing actual pixels, held in each window.
        self.viewers = [window.viewer for window in self.windows]

        # Set up mouse events for the viewers so the user can control 
        # alignment parameters by dragging.
        for viewer in self.viewers:
            viewer.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)

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

        self.sizer.Add(self.makeAlignPanel())

        ## Maps axes to controls to toggle visibility of those axes, just
        # for the views that aren't shown by default.
        self.axesToToggleMap = dict()
        if self.dataDoc.size[1] > 1:
            # Add controls to show time views.
            rowSizer = wx.BoxSizer(wx.HORIZONTAL)
            for axes in [(4, 1), (3, 1), (2, 1)]:
                control = wx.CheckBox(self, 
                        label = "%s-%s view" % (datadoc.DIMENSION_LABELS[axes[0]],
                                                datadoc.DIMENSION_LABELS[axes[1]]))
                self.axesToToggleMap[axes] = control
                rowSizer.Add(control, 0, wx.LEFT, 5)
                control.Bind(wx.EVT_CHECKBOX, 
                        lambda event, axes = axes: self.toggleNewWindow(axes))
            self.sizer.Add(rowSizer)

        ## Time slider for data with a time axis, or None if we don't have
        # time.
        self.timeSlider = None

        # Histograms go along the bottom.
        self.sizer.Add(self.setupHistograms())
        self.SetSizerAndFit(self.sizer)

        # Allow use of numpad keys to change the slice lines.
        accelTable = []
        for code, offset in KEY_MOTION_MAP.iteritems():
            id = wx.NewId()
            accelTable.append((wx.ACCEL_NORMAL, code, id))
            self.Bind(wx.EVT_MENU, lambda event, code = code: self.onKey(code),
                    id = id)

        # Add a debug control to print the correlation coefficient for the 
        # first two wavelengths.
        id = wx.NewId()
        accelTable.append((wx.ACCEL_NORMAL, wx.WXK_NUMPAD_MULTIPLY, id))
        self.Bind(wx.EVT_MENU, lambda event: self.correlate(), id = id)
        table = wx.AcceleratorTable(accelTable)
        self.SetAcceleratorTable(table)

        ## Window holding display of auto-alignment progress
        self.alignProgressFrame = None

        ## So we can close our window if necessary.
        self.Bind(wx.EVT_CLOSE, self.OnClose)


    ## Make the panel for cropping.
    def makeCropPanel(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.cropControlPanel = cropControlPanel.CropControlPanel(
                parent = panel, helpFunc = self.prepHelpText,
                dimensions = self.dataDoc.size[-3:][::-1],
                textChangeCallback = self.updateCrop,
                toggleCropCallback = self.toggleCrop,
        )
        sizer.Add(self.cropControlPanel, 0, wx.LEFT, 10)
        panel.SetSizerAndFit(sizer)
        return panel

    
    ## Make the panel for aligning.
    def makeAlignPanel(self):   
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.alignParamsPanels = []
        self.alignSwapButtons = []
        for wavelength in range(self.dataDoc.numWavelengths):
            # Create the panels containing the alignment parameters for each
            # wavelength
            rowSizer = wx.BoxSizer(wx.HORIZONTAL)
            
            columnSizer = wx.BoxSizer(wx.VERTICAL)
            label = wx.StaticText(panel, -1, 
                    "%d. Align parameters: " % wavelength)
            columnSizer.Add(label, 0, wx.ALL, 3)
            swapButton = wx.ToggleButton(panel, -1, label = "Swap")
            self.prepHelpText(swapButton, "Swap parameters", 
                    "Click on two swap buttons to exchange alignment " + 
                    "parameters between the two corresponding wavelengths.")
            swapButton.Bind(wx.EVT_TOGGLEBUTTON, self.onSwapAlignParams)
            self.alignSwapButtons.append(swapButton)
            columnSizer.Add(swapButton, 0, wx.ALL, 3)
            rowSizer.Add(columnSizer)
            
            initialParams = self.dataDoc.alignParams[wavelength]
            # This is called when parameters are changed.
            changeCallback = lambda wavelength = wavelength: self.setAlignParams(wavelength)
            # This is called when the checkbox to modify parameters with the 
            # mouse is clicked.
            checkCallback = lambda wavelength = wavelength: self.setMouseControl(wavelength)
            # This is called when the radio button to use this wavelength as
            # the alignment reference is clicked.
            radioCallback = lambda wavelength = wavelength: self.setAlignReference(wavelength)
            paramsPanel = alignParamsPanel.AlignParamsPanel(panel, 
                    self.prepHelpText,
                    initialParams, changeCallback, checkCallback, radioCallback,
                    isFirstPanel = wavelength == 0)
            self.alignParamsPanels.append(paramsPanel)

            rowSizer.Add(paramsPanel, 0, wx.LEFT | wx.BOTTOM, 5)
            sizer.Add(rowSizer, 0, wx.LEFT, 10)
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        autoAlignButton = wx.Button(panel, -1, "Auto-align")
        self.prepHelpText(autoAlignButton, "Auto-align", 
                "Run a Simplex algorithm to attempt to automatically " + 
                "align each wavelength with the first. This will take " + 
                "some time. You may need to run it twice to get a good " + 
                "alignment."
        )
        autoAlignButton.Bind(wx.EVT_BUTTON, self.OnAutoAlign)
        rowSizer.Add(autoAlignButton, 0, wx.LEFT | wx.BOTTOM, 10)

        exportButton = wx.Button(panel, -1, "Export parameters")
        self.prepHelpText(exportButton, "Export parameters",
                "Generate a file that contains the alignment and cropping " + 
                "parameters for this file, so that they may be loaded " + 
                "later."
        )
        exportButton.Bind(wx.EVT_BUTTON, self.OnExportParameters)
        rowSizer.Add(exportButton, 0, wx.LEFT | wx.BOTTOM, 10)

        loadButton = wx.Button(panel, -1, "Load parameters")
        self.prepHelpText(loadButton, "Load parameters",
                "Load a previously-generated file describing how to crop " + 
                "and align data."
        )
        loadButton.Bind(wx.EVT_BUTTON, self.OnLoadParameters)
        rowSizer.Add(loadButton, 0, wx.LEFT | wx.BOTTOM, 10)

        batchButton = wx.Button(panel, -1, "Batch process")
        self.prepHelpText(batchButton, "Batch process", 
                "Apply these cropping and/or alignment parameters to " +
                "a large number of files."
        )
        batchButton.Bind(wx.EVT_BUTTON, lambda event: batchDialog.BatchDialog(
                self.parent, self))
        rowSizer.Add(batchButton, 0, wx.LEFT | wx.BOTTOM, 10)

        sizer.Add(rowSizer)
        panel.SetSizerAndFit(sizer)
        return panel


    ## Make a panel for showing helpful text to the user.
    def makeHelpPanel(self):
        panel = wx.Panel(self, -1, style = wx.BORDER_SUNKEN)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.infoText = wx.StaticText(panel, -1, ' ' * 500)
        self.infoText.Wrap(300)
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


    ## Create all of our histograms, and return the sizer that contains them.
    # Also set up the time slider at this time if needed.
    def setupHistograms(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Calculate width of histogram based on number of wavelengths, as 
        # well as presence of a time slider.
        histogramWidth = 600 / self.dataDoc.numWavelengths - 4
        if self.dataDoc.size[1] > 1: # need a time slider
            histogramWidth = 400 / self.dataDoc.numWavelengths - 8
            topSizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(topSizer, 0, wx.ALL | wx.EXPAND, 2)
            self.timeSlider = wx.Slider(self, wx.ID_ANY, 0, 
                    0, self.dataDoc.size[1] - 1, 
                    size = wx.Size(200, -1),
                    style = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_AUTOTICKS)
            topSizer.Add(self.timeSlider, 1, wx.ALL | wx.ALIGN_LEFT, 2)
            wx.EVT_SLIDER(self, self.timeSlider.GetId(), self.OnTimeSlider)

        self.histograms = []
        dataSlice = self.dataDoc.takeDefaultSlice((1, 2), False)
        for i in xrange(self.dataDoc.numWavelengths):
            color = COLORS_LIST[i]
            newHistogram = histogram.Histogram(self, i, 
                    dataSlice[i], color, 
                    size = (histogramWidth, -1)
            )
            self.histograms.append(newHistogram)
            sizer.Add(newHistogram)

            for viewer in self.viewers:
                viewer.setColor(i, color)
        return sizer


    ## Passthrough to the viewers to update their scalings.
    def changeHistScale(self, wavelength, minVal, maxVal):
        for viewer in self.viewers:
            viewer.changeHistScale(wavelength, minVal, maxVal)


    ## Passthrough to the viewers to toggle the visibility of wavelengths.
    def setWavelengthVisibility(self, wavelength, isVisible):
        for viewer in self.viewers:
            viewer.setVisibility(wavelength, isVisible)


    ## Cause the histograms to automatically fit themselves to the current
    # data; call this after the user has changed which data is shown.
    def autoFitHistograms(self):
        for histogram in self.histograms:
            histogram.autoFit()


    ## Update the viewer min/max scale to match the histogram.
    def setViewerScalings(self):
        for wavelength in xrange(self.dataDoc.numWavelengths):
            minVal, maxVal = self.histograms[wavelength].getMinMax()
            for viewer in self.viewers:
                viewer.changeHistScale(wavelength, minVal, maxVal)


    ## This function is invoked when the user clicks one of the "Swap" 
    # buttons for the alignment parameters. If two swap buttons are both
    # active, then their parameters are swapped.
    def onSwapAlignParams(self, event):
        firstButton = event.GetEventObject()
        if not firstButton.GetValue():
            return
        firstIndex = self.alignSwapButtons.index(firstButton)
        for i, button in enumerate(self.alignSwapButtons):
            if button is not firstButton and button.GetValue():
                # Found two active buttons; deactivate them both and swap 
                # their parameters.
                firstButton.SetValue(False)
                button.SetValue(False)
                firstParams = self.alignParamsPanels[firstIndex].getParamsList()
                secondParams = self.alignParamsPanels[i].getParamsList()
                self.alignParamsPanels[firstIndex].setParams(secondParams)
                self.alignParamsPanels[i].setParams(firstParams)
                self.setAlignParams(firstIndex)
                self.setAlignParams(i)
                return
        # Only one button active; do nothing.


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
        self.dataDoc.alignParams[index] = tx, ty, tz, rot, mag
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
        if self.alignProgressFrame is not None:
            self.alignProgressFrame.Destroy()
            self.alignProgressFrame = None


    def OnTimeSlider(self, event):
        self.dataDoc.curViewIndex[1] = event.GetInt()
        self.updateGLGraphics()


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
    def OnAutoAlign(self, event):
        referenceIndex = self.getReferenceWavelength()

        wavelengthsToAlign = range(self.dataDoc.numWavelengths)
        del wavelengthsToAlign[referenceIndex]
        
        # This datastructure will allow us to track which wavelengths have 
        # finished aligning.
        self.alignedWavelengths = dict([(i, False) for i in wavelengthsToAlign])

        # Calculate the 2D XY reference array
        targetCoords = self.dataDoc.getSliceCoords((1, 2))
        referenceData = self.getFilteredData(referenceIndex)

        self.alignProgressFrame = alignProgressFrame.AlignProgressFrame(self, self.dataDoc.numWavelengths)
        self.alignProgressFrame.Show()

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

            aligner = realign.SimplexAlign(self, referenceData, i, guess,
                    shouldAdjustGuess = shouldAdjustGuess)


    ## Return the wavelength being used as a reference (i.e. the wavelength
    # that is held fixed, and that the other wavelengths adjust themselves 
    # to when auto-aligning).
    def getReferenceWavelength(self):
        for i, panel in enumerate(self.alignParamsPanels):
            if panel.shouldUseAsReference():
                return i


    ## Retrieve the 3D array for the specified wavelength, in addition to 
    # our reference wavelength. This is called from one of our worker 
    # threads, so we have to deal with inter-thread communications.
    # \todo This is pretty hackish.
    @callInMainThread
    def getFullVolume(self, wavelength, worker):
        reference = self.getReferenceWavelength()
        result = self.dataDoc.alignAndCrop(
                wavelengths = [reference, wavelength], 
                timepoints = [self.dataDoc.curViewIndex[1]])
        worker.dataLock.acquire()
        # Split out by wavelength and timepoint
        worker.referenceVolume = result[0][0]
        worker.movingVolume = result[1][0]
        worker.dataLock.release()


    ## Update the status text to show the user how auto-alignment is going.
    @callInMainThread
    def updateAutoAlign(self, startingCost, currentCost, wavelength):
        self.alignProgressFrame.newData(wavelength, currentCost)


    ## Receive notification from one of the aligner threads that it's now
    # working on Z alignment.
    def alignSwitchTo3D(self, wavelength):
        self.alignProgressFrame.switchTo3D(wavelength)


    ## Receive notification from one of the aligner threads that it's all 
    # done.
    @callInMainThread
    def finishAutoAligning(self, result, wavelength):
        self.alignedWavelengths[wavelength] = True
        # Check if we've done with alignment for all wavelengths
        amDone = True
        for i, done in self.alignedWavelengths.iteritems():
            if not done:
                amDone = False
                break
        if amDone:
            self.alignProgressFrame.finish()
        print "Got transformation",result,"for wavelength",wavelength
        self.alignParamsPanels[wavelength].setParams(result)
        self.setAlignParams(wavelength)


    ## The align progress frame has been destroyed, so we don't need to 
    # track it any more.
    def clearProgressFrame(self):
        self.alignProgressFrame = None


    ## Calculate the centers of the beads and find out how well we have 
    # aligned the different wavelengths.
    def checkAlignment(self):
        volumes = self.dataDoc.alignAndCrop(
                timepoints = [self.dataDoc.curViewIndex[1]]
        )
        print "Got volumes"
        beadCentersByWavelength = []
        for wavelength in xrange(self.dataDoc.numWavelengths):
            print "Processing wavelength",wavelength
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
    def OnExportParameters(self, event = None):
        defaultName = os.path.basename(self.dataDoc.filePath) + "-align.txt"
        dialog = wx.FileDialog(self, "Where do you want to save the file?",
                os.path.dirname(self.dataDoc.filePath),
                defaultName,
                style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() != wx.ID_OK:
            return
        
        handle = open(dialog.GetPath(), 'w')
        cropParams = self.cropControlPanel.getParams()
        for label, value in zip(['minX', 'maxX', 'minY', 'maxY', 'minZ', 'maxZ'], cropParams):
            handle.write("crop-%s: %s\n" % (label, value))
        for wavelength in xrange(self.dataDoc.numWavelengths):
            alignParams = self.alignParamsPanels[wavelength].getParamsList()
            # Multiply by pixel size to get offsets in microns.
            alignParams[:3] = self.dataDoc.convertToMicrons(alignParams[:3])
            for label, value in zip(['dx', 'dy', 'dz', 'angle', 'zoom'], alignParams):
                handle.write("align-%d-%s: %s\n" % (wavelength, label, value))
        handle.close()


    ## Load a parameters file as generated by OnExportParameters
    def OnLoadParameters(self, event = None):
        dialog = wx.FileDialog(self, "Please select the parameters file.",
                os.path.dirname(self.dataDoc.filePath),
                style = wx.FD_OPEN)
        if dialog.ShowModal() != wx.ID_OK:
            return
        
        handle = open(dialog.GetPath(), 'r')
        cropParams = [0] * 6
        cropLabelOrder = ['minX', 'maxX', 'minY', 'maxY', 'minZ', 'maxZ']
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
                    alignParams[wavelength] = [0] * 5
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
    # On OSX, we can do this multithreaded, which makes for a nice improvement
    # in responsiveness. On Linux however, this doesn't work -- we get OpenGL
    # errors. So we split our behavior at this point based on the value of 
    # sys.platform.
    # In either case, we need a lock around this function as a whole so that
    # we don't get concurrent view-update calls.
    def updateGLGraphics(self, viewsToUpdate = []):
        if not viewsToUpdate:
            viewsToUpdate = self.viewers

        self.displayUpdateLock.acquire()

        if 'linux' in sys.platform:
            # Update each viewer in sequence.
            for viewer in viewsToUpdate:
                self.updateViewerDisplay(viewer)
        else:
            threads = []
            for viewer in viewsToUpdate:
                thread = threading.Thread(
                        target = self.updateViewerDisplay, args = [viewer]
                )
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()

        self.displayUpdateLock.release()


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
        imageSlice = self.dataDoc.takeSlice(targetCoords, shouldTransform)
        # HACK: For now, transpose the YZ view so Y is vertical. Later we
        # want to make this a property of the viewer
        if viewer.axes == (2, 3):
            imageSlice = imageSlice.transpose(0, 2, 1)
        viewer.addImgL(imageSlice)
        if shouldTransform:
            # OpenGL transforms should not be used since the slice already
            # covers all that.
            for wavelength in xrange(self.dataDoc.numWavelengths):
                viewer.changeImgOffset(wavelength, 0, 0, 0, 1, False)

        for i in xrange(self.dataDoc.numWavelengths):
            viewer.setColor(i, COLORS_LIST[i])


    def getIsViewCropped(self):
        return self.isViewCropped


    ## Push a new set of cropping parameters to self.cropControlPanel, as 
    # received from one of our viewers when the user drags the crop box around.
    def updateCropboxEdit(self):
        newParams = []
        for i in xrange(3):
            newParams.append(self.dataDoc.cropMin[4 - i])
            newParams.append(self.dataDoc.cropMax[4 - i])
        self.cropControlPanel.setParams(newParams)
    

    ## Receive a new set of cropping parameters from self.cropControlPanel and
    # apply them to the data and our viewers.
    def updateCrop(self, event = None):
        params = self.cropControlPanel.getParams()
        for i in xrange(3):
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
    def toggleNewWindow(self, axes):
        if not self.axesToToggleMap[axes].GetValue():
            for i, viewer in enumerate(self.viewers):
                if viewer.axes == axes:
                    del self.viewers[i]
                    self.windows[i].Destroy()
                    del self.windows[i]
                    break
        else:
            newWindow = imageViewer.ViewerWindow(self, axes, dataDoc = self.dataDoc)
            self.windows.append(newWindow)
            self.viewers.append(newWindow.viewer)
            self.updateGLGraphics(viewsToUpdate = [newWindow.viewer])
            self.setViewerScalings()


    ## Refresh all viewers.
    def refreshViewers(self):
        for viewer in self.viewers:
            viewer.Refresh(0)


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
        self.updateGLGraphics(viewsToUpdate = updatedViews)
        wx.CallAfter(self.setViewerScalings)


    ## Process keypad inputs to move the slice lines around.
    def onKey(self, code):
        if code in KEY_MOTION_MAP:
            self.moveSliceLines(KEY_MOTION_MAP[code])
            if KEY_MOTION_MAP[code][1] and self.timeSlider:
                # We're moving through time, so update the slider to match.
                self.timeSlider.SetValue(self.dataDoc.curViewIndex[1])


    ## Toggle the visibility of our child windows.
    def setWindowVisibility(self, isVisible):
        for window in self.windows:
            window.Show(isVisible)


    ## Simple debugging function to print out the correlation coefficient for
    # the first two wavelengths. This also makes a convenient hook for other
    # debugging logic.
    def correlate(self):
        data = self.dataDoc.takeDefaultSlice((1, 2))
        first = data[0].astype(numpy.float64)
        first /= first.max()
        second = data[1].astype(numpy.float64)
        second /= second.max()
        print "Correlation is",util.correlationCoefficient(first, second)
        # Calculate phase correlation for comparison:
#        fa = numpy.fft.fftn(data[0])
#        fb = numpy.fft.fftn(data[1])
#        r = (fa * fb.conj())
#        r = r / numpy.abs(r)
#        r = numpy.fft.ifftn(r).real
#        util.imsave("phase.png", r)
#        self.checkAlignment()




printLock = threading.Lock()
## Simple function for debugging when dealing with multiple threads, since
# otherwise Python's "print" builtin isn't threadsafe.
def threadPrint(*args):
    with printLock:
        print " ".join([str(s) for s in args])
