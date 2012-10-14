import wx

import util

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
        for i, label in enumerate(['X translate', 'Y translate', 'Z translate',
            'Rotate', 'Zoom']):
            control = util.addLabeledInput(self, columnSizer, label = label,
                    defaultValue = str(params[i]),
                    style = wx.TE_PROCESS_ENTER,
                    size = (80, -1), minSize = (200, -1), border = 3,
                    shouldRightAlignInput = True)
            control.Bind(wx.EVT_TEXT_ENTER, lambda event: self.changeCallback())
            action = label.replace('ate', 'ation')
            helpFunc(control, label, 
                    "Set the %s parameter for alignment of this wavelength" % action)
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

