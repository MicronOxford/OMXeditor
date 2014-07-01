import wx, wx.aui
import os
import sys

import batchDialog
import controlPanel
import util

import numpy
from Priithon import Mrc
import traceback


## This class defines the primary window for the application, which is always
# open so long as the app is. Primarily, this window contains a set of tabs, 
# each of which corresponds to a single ControlPanel and contains controls 
# for modifying a single open MRC file. The actual views of the pixel data
# in the file are handled by the ControlPanel instance.
class MainWindow(wx.Frame):
    def __init__(self, title, parent=None, id=wx.ID_ANY):
        wx.Frame.__init__(self, parent, id, title, style=wx.DEFAULT_FRAME_STYLE | wx.BORDER_SUNKEN, size=wx.Size(600, 550))

        self.auiManager = wx.aui.AuiManager()
        self.auiManager.SetManagedWindow(self)

        # Disable the "Windows" menu, which is pretty pointless for us.
        wx.MenuBar.SetAutoWindowMenu(False)

        self.menuBar = wx.MenuBar()

        # Create 'File' menu with various options.
        fileMenu = wx.Menu()
        self.menuBar.Append(fileMenu, 'File')
        util.addMenuItem(self, fileMenu, '&Open...\tCtrl+O', self.OnFileOpen)
        util.addMenuItem(self, fileMenu, '&Save\tCtrl+S', self.OnFileSave)
        util.addMenuItem(self, fileMenu, '&Save As...\tCtrl+Shift+S', self.OnFileSaveAs)

        fileMenu.AppendSeparator()
        util.addMenuItem(self, fileMenu, '&Show view controls\tCtrl+T', 
                self.OnViewControls)

        # We can only generate stereo pairs if Priism is installed.
        if 'PriismX' in os.listdir(os.getcwd()):
            util.addMenuItem(self, fileMenu, '&Generate stereo pairs',
                    self.OnStereoPairs)

        fileMenu.AppendSeparator()
        util.addMenuItem(self, fileMenu, '&Auto align...', self.OnAutoAlign)
        util.addMenuItem(self, fileMenu, '&Load parameters...\tCtrl+L',
                self.OnLoadParams)
        util.addMenuItem(self, fileMenu, '&Export parameters...\tCtrl+E',
                self.OnExportParams)
        util.addMenuItem(self, fileMenu, '&Batch process...\tCtrl+B',
                self.OnBatchProcess)
        # As of the Cocoa build of WX, we have to add this manually now.
        util.addMenuItem(self, fileMenu, '&Quit\tCtrl+Q', 
                self.OnQuit)
        
        # Create 'Help' menu with 'About' option. Note that in OSX the About
        # option automatically gets shunted over to the default application 
        # menu because we use ID_ABOUT here. The otherwise-bare Help menu 
        # would get created anyway by OSX even though we don't have anything
        # to put in it...
        helpMenu = wx.Menu()
        self.menuBar.Append(helpMenu, 'Help')

        item = wx.MenuItem(helpMenu, wx.ID_ABOUT, '&About OMX Editor')
        self.Bind(wx.EVT_MENU, self.OnAbout, id = wx.ID_ABOUT)
        helpMenu.AppendItem(item)

        self.SetMenuBar(self.menuBar)

        self.auiManager.AddPane(self.CreateNotebook(), wx.aui.AuiPaneInfo().CloseButton(False).CenterPane())

        # The size of the AUI panes is only determined after auiManager.Update()
        self.auiManager.Update()

        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnNotebookPageChange)

        # Status bar for displaying information based on the mouse position
        # (e.g. pixel values, histogram values).
        self.statbar = self.CreateStatusBar(2)
        # We have to use a separate FileDropper instance for each area we 
        # want to have support drag-and-drop, or else the program segfaults
        # on exit (presumably due to a double-free).
        # Handles dropping on the upper area of the window with the tabs
        self.SetDropTarget(FileDropper(self))
        # Handles dropping on the main area of the window with the controls
        self.controlPanelsNotebook.SetDropTarget(FileDropper(self))

        ## Store this position for later so we can refer to it when
        # opening new files.
        self.origPos = self.GetPosition()


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

        targetPath = curPanel.getFilePath()
        permission = wx.MessageBox("Overwrite %s?" % targetPath, 
                "Please confirm", 
                style = wx.OK | wx.CANCEL)
        if permission != wx.OK:
            return
                
        curPanel.dataDoc.alignAndCrop(savePath = targetPath)

        im_to_edit = Mrc.bindFile(targetPath)

        self.controlPanelsNotebook.DeletePage(pageIndex)
        self.controlPanelsNotebook.InsertPage(pageIndex, 
                controlPanel.ControlPanel(self, im_to_edit),
                os.path.basename(targetPath), select=True)


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
            im_to_edit = Mrc.bindFile(targetPath)
            self.controlPanelsNotebook.AddPage(
                    controlPanel.ControlPanel(self, im_to_edit),
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
    def OnLoadParams(self, event):
        if self.requireOpenFile():
            self.getCurPanel().loadParameters()

    
    ## Passthrough to the current panel.
    def OnExportParams(self, event):
        if self.requireOpenFile():
            self.getCurPanel().exportParameters()


    ## Passthrough to the current panel.
    def OnStereoPairs(self, event):
        if self.requireOpenFile():
            self.getCurPanel().generateStereoPairs()

    
    ## Create a BatchDialog instance.
    def OnBatchProcess(self, event):
        if self.requireOpenFile():
            batchDialog.BatchDialog(self, self.getCurPanel())

    
    def OnAbout(self, event = None):
        wx.MessageDialog(self, 
                "This program is for viewing and editing MRC files. It " +
                "allows you to align data across wavelengths, crop out " + 
                "unnecessary pixels, and view the data from many different " +
                "perspectives. Alignment and cropping parameters can also " + 
                "be exported for use in the OMX Processor program.\n\n" + 
                "Copyright 2012 Sedat Lab, UCSF",
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
                image_to_edit = Mrc.bindFile(filename)
            except Exception, e:
                wx.MessageDialog(None, 
                        "Failed to open file: %s\n\n%s" % (e, traceback.format_exc()), 
                        "Error", wx.OK).ShowModal()
                return

            newPanel = controlPanel.ControlPanel(self, image_to_edit)
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

