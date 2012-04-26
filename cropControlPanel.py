import util

import wx

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
        sizer.Add(wx.StaticText(self, -1, "Crop controls:"))
        self.controls = []
        index = 0
        # Create a 2x3 grid of text controls for setting the crop box volume.
        for dimension in ['X', 'Y', 'Z']:
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
        
        # Add a preview button.
        previewButton = wx.ToggleButton(self, -1, "Preview crop")
        helpFunc(previewButton, "Preview crop", 
                "Shows what the crop will look like when applied to the " + 
                "image. You must save the image to actually apply the crop."
        )
        previewButton.Bind(wx.EVT_TOGGLEBUTTON, lambda event: toggleCropCallback())
        sizer.Add(previewButton)

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

