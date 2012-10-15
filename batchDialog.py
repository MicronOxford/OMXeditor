import datadoc

import numpy
import os
import time
import wx

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

