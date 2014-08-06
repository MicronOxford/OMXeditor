import numpy
import wx

import datadoc


## The ViewControlWindow class provides a window that allows the user
# to control and customize various views of the data -- by setting the 
# 4D crosshairs, toggling visibility of a specific perspective, and creating
# projections across orthogonal axes.
class ViewControlWindow(wx.Frame):
    def __init__(self, parent, dataDoc, *args, **kwargs):
        wx.Frame.__init__(self, parent, *args, **kwargs)
        ## We call a few functions on our parent as a way to communicate with
        # it.
        self.parent = parent
        ## Reference to the parent's DataDoc instance.
        self.dataDoc = dataDoc
        self.dataDoc.registerAlignmentCallback(self.onAlignChange)

        sizer = wx.BoxSizer(wx.VERTICAL)

        ## List of options that could be a bit expensive (see 
        # self.onAlignChange).
        self.expensiveProjectionOptions = []
        ## List of options that could be very expensive (ditto).
        self.veryExpensiveProjectionOptions = []

        # Set up viewer controls in a grid. Figure out which axes pairs 
        # are valid (i.e. both axes have a size greater than 1) and 
        # only include them. 
        viewSizer = wx.GridSizer(2, 3, 1, 1)
        validAxes = []
        # XY, XZ, YZ, XT, YT, ZT. The first three are also the default views
        # that we show, assuming there's more than one Z slice.
        for a1, a2 in [(4, 3), (3, 2), (4, 2), (4, 1), (3, 1), (2, 1)]:
            if self.dataDoc.size[a1] > 1 and self.dataDoc.size[a2] > 1:
                validAxes.append((a1, a2))
        for i, (a1, a2) in enumerate(validAxes):
            # Show by default all views that don't include a time axis.
            viewSizer.Add(self.makeViewerPanel((a1, a2), a2 != 1))
        sizer.Add(viewSizer)

        sizer.Add(wx.StaticText(self, -1, "Current view position:"))

        ## Maps axes to sliders that change the view along those axes.
        self.axisToSliderMap = dict()
        sliderSizer = wx.FlexGridSizer(4, 2, 1, 1)
        # Set up sliders for each possible view axis.
        for axis in xrange(4, 0, -1):
            # This conditional is for images that have only one timepoint
            # and/or Z slice.
            if self.dataDoc.size[axis] > 1:
                self.axisToSliderMap[axis] = self.makeSliderControl(sliderSizer, axis)
        sizer.Add(sliderSizer)

        self.SetSizerAndFit(sizer)


    ## Create a panel that provides view options for a single viewer: whether
    # or not the viewer is visible, and which, if any, axis to project the 
    # viewer across.
    def makeViewerPanel(self, axes, isVisibleByDefault):
        panel = wx.Panel(self, -1, style = wx.BORDER_SUNKEN | wx.TAB_TRAVERSAL)
        sizer = wx.BoxSizer(wx.VERTICAL)

        label = "%s-%s" % (datadoc.DIMENSION_LABELS[axes[0]], 
                datadoc.DIMENSION_LABELS[axes[1]])
        sizer.Add(wx.StaticText(panel, -1, label), 0, wx.ALIGN_CENTER_HORIZONTAL)
        
        # Size the toggle button to ensure that we fill the entire width of 
        # the window, assuming we have 3 columns of viewer panels.
        toggleButton = wx.ToggleButton(panel, -1, 'Visible', size = (78, -1))
        toggleButton.Bind(wx.EVT_TOGGLEBUTTON, lambda event: self.parent.toggleWindowVisibility(axes))
        toggleButton.SetValue(isVisibleByDefault)
        sizer.Add(toggleButton)

        sizer.Add(wx.StaticText(panel, -1, 'Project:'))
        baseRadio = wx.RadioButton(panel, -1, 'None', style = wx.RB_GROUP)
        baseRadio.SetValue(True)
        baseRadio.Bind(wx.EVT_RADIOBUTTON, 
                lambda event: self.parent.setViewProjection(axes, None))
        sizer.Add(baseRadio)
        # Allow projection across time, Z, Y, and X, but of course we leave
        # out any axes that are already part of the view.
        for axis in xrange(4, 0, -1):
            if axis not in axes and self.dataDoc.size[axis] > 1:
                radio = wx.RadioButton(panel, -1, 
                        datadoc.DIMENSION_LABELS[axis], 
                        style = wx.RB_SINGLE)
                if axis == 1:
                    # Time axis; could be very expensive
                    self.veryExpensiveProjectionOptions.append(radio)
                elif axis in [3, 4]:
                    # X/Y axis; could be moderately expensive
                    self.expensiveProjectionOptions.append(radio)
                radio.Bind(wx.EVT_RADIOBUTTON, 
                        lambda event, axis = axis: self.parent.setViewProjection(axes, axis))
                sizer.Add(radio)

        panel.SetSizerAndFit(sizer)
        return panel


    ## Make a slider that allows the user to change the view coordinates for
    # one axis of the image. Insert the slider, and its label, into the
    # provided sizer.
    def makeSliderControl(self, sizer, axis):
        sizer.Add(wx.StaticText(self, -1, 
            "%s:" % datadoc.DIMENSION_LABELS[axis]), 
                0, wx.ALL, 5)
        
        slider = wx.Slider(self, -1, 0, 0, self.dataDoc.size[axis] - 1,
                size = wx.Size(200, -1),
                style = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_AUTOTICKS)
        slider.SetValue(self.parent.getViewAxisIndex(axis))
        slider.Bind(wx.EVT_SLIDER, 
                lambda event: self.parent.setSliceLine(axis, event.GetInt()))
        sizer.Add(slider)
        return slider


    ## Recognize that alignment parameters have changed. If there is rotation
    # or scaling, then projections through X or Y require transforming the 
    # entire volume, and projections through time require transforming 
    # the entire dataset -- ouch! If this happens, we want to notify the 
    # user before they click on anything, so we adjust background colors
    # and tooltips to suit.
    def onAlignChange(self, alignParams):
        isExpensive = (numpy.any(alignParams[:,3] != 0) or 
                numpy.any(alignParams[:,4] != 1))
        preamble = "Due to the rotation and scaling alignment parameters, " + \
                "this projection option will require transforming the " + \
                "entire "
        badColors = [(255, 255, 0), (255, 0, 0)]
        badTips = [preamble + "current volume, which will take some time.", 
                preamble + "entire dataset, which can take a very long time."]
        
        for i, radioSet in enumerate([self.expensiveProjectionOptions, 
                self.veryExpensiveProjectionOptions]):
            for radio in radioSet:
                if isExpensive:
                    radio.SetBackgroundColour(badColors[i])
                    radio.SetToolTipString(badTips[i])
                else:
                    radio.SetBackgroundColour([230] * 3)
                    radio.SetToolTipString('')
            



    ## Update our sliders because the user changed the view without using them.
    # \param newPositions Maps axes to positions on those axes.
    def setSliders(self, newPositions):
        for axis, slider in self.axisToSliderMap.iteritems():
            if axis in newPositions:
                slider.SetValue(newPositions[axis])

