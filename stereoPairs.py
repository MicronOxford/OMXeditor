import mainWindow
import util

import numpy
import os
import pipes
import stat
import subprocess
import wx

## @module stereoPairs
# This module handles a special adjunct UI for generating rocking stereo pairs,
# which are one method of doing 3D visualization of our datasets. 
# 
# Because the generation of these pairs requires the use of Priism, which
# can't be distributed (due to including proprietary code), this particular
# module is disabled in most builds of the editor. 

class StereoDialog(wx.Dialog):
    def __init__(self, parent, dataDoc):
        wx.Dialog.__init__(self, parent, -1, 'Generate Stereo Pairs')

        ## DataDoc instance holding data we need to generate the stereo pairs.
        self.dataDoc = dataDoc

        ## Result file that will need to be opened when we're through.
        self.resultFilename = None

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(wx.StaticText(self, -1, 
                "This system will generate a fake-3D view of your images " + 
                "by performing summation projections from two slightly " +
                "different perspectives. The result will be stored in an " + 
                "MRC file which has the two views on separate \"Z-slices\".", 
                size = (300, 100)),
                0, wx.ALIGN_CENTER | wx.ALL, 5)

        if self.dataDoc.size[1] > 1:
            sliderSizer = wx.BoxSizer(wx.HORIZONTAL)
            sliderSizer.Add(wx.StaticText(self, -1, "Timepoint:"))
            self.timeSlider = wx.Slider(self, -1, 0, 0, 
                    self.dataDoc.size[1] - 1, 
                    size = (200, -1), 
                    style = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_AUTOTICKS)
            sliderSizer.Add(self.timeSlider)
            sizer.Add(sliderSizer, 0, wx.ALL, 5)

        self.separation = util.addLabeledInput(self, sizer, 
                label = "View separation angle: ", defaultValue = '6', 
                helperString = "How much angular distance there is between " +
                "the two viewpoints. Bigger values create a stronger 3D " + 
                "effect.", 
                labelHeightAdjustment = 3, border = 5)

        fileSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.filenameControl = util.addLabeledInput(
                self, fileSizer, label = "Filename:",
                size = (150, -1), minSize = (200, -1),
                shouldRightAlignInput = True, border = 5,
                labelHeightAdjustment = 3,
                flags = wx.ALL | wx.ALIGN_CENTER,
        )

        browseButton = wx.Button(self, -1, "Browse...")
        browseButton.Bind(wx.EVT_BUTTON, self.onChooseFile)
        fileSizer.Add(browseButton, 0, wx.ALL, 5)
        sizer.Add(fileSizer)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        cancelButton = wx.Button(self, wx.ID_CANCEL, 'Cancel')
        buttonSizer.Add(cancelButton, 0, wx.ALL, 5)
        startButton = wx.Button(self, -1, "Start")
        startButton.Bind(wx.EVT_BUTTON, self.onStart)
        buttonSizer.Add(startButton, 0, wx.ALL, 5)

        sizer.Add(buttonSizer)
        self.SetSizerAndFit(sizer)


    ## Generate the stereo pairs, by running Priism's rotfast program. Store 
    # the result to be returned by our getResult function.
    def onStart(self, event = None):
        self.Hide()
        separation = int(self.separation.GetValue())
        timepoint = 0
        if self.dataDoc.size[1] > 1:
            timepoint = self.timeSlider.GetValue()

        filename = self.dataDoc.filePath
        backgroundLevels = map(numpy.amin, self.dataDoc.imageArray[:,timepoint])

        # Generate a script to run the command.
        commandFile = os.path.join(os.path.sep, 'tmp', 
                'stereoGen-%d.sh' % os.getpid())
        outputFile = self.filenameControl.GetValue()
        if not outputFile:
            outputFile = os.path.join(os.path.sep, 'tmp', 
                    'stereoGen-%d.mrc' % os.getpid())
        background = ':'.join(str(int(val)) for val in backgroundLevels)
        command = "rotfast -ang=-3:3:6 -bkg=%s %s %s" % (background, pipes.quote(filename), pipes.quote(outputFile))
        makePriismFile(command, commandFile)
        subprocess.call([commandFile])
        self.resultFilename = outputFile


    ## Let the user choose a location to save the file to.
    def onChooseFile(self, event = None):
        dialog = wx.FileDialog(self,
                message = "Please choose a location to save the file to.",
                style = wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            self.filenameControl.SetValue(dialog.GetPath())


    def getResult(self):
        return self.resultFilename


## Generate a file that will run a Priism command when run. This was copied
# from the processor program.
def makePriismFile(command, filename):
    priismDir = os.path.join(os.getcwd(), 'PriismX')
    priismSetup = os.path.join(priismDir, 'Priism_setup.sh')

    scriptFilehandle = open(filename, 'w')
    # The IVE_BASE export here tells Priism where it's "installed"; 
    # since this program can be installed anywhere by its users and
    # includes Priism within it, we need to set this dynamically.
    # Ordinarily it's set by a hardcoded string in Priism_setup.sh, but our
    # copy of that file has been modified to skip that step.
    scriptFilehandle.write('''#!/bin/sh
export IVE_BASE=%s  # Tell Priism where it's installed
source %s   # Prepare Priism
%s  # Process file
rm %s   # Cleanup /tmp''' % (pipes.quote(priismDir), pipes.quote(priismSetup),
    command, filename
))
    scriptFilehandle.close()
    os.chmod(filename, stat.S_IRWXU | stat.S_IRWXG | stat.S_IXOTH)
