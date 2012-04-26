import wx, wx.aui
import os
import sys

import controlPanel

import numpy
from Priithon import Mrc
import traceback

class MainWindow(wx.Frame):
    def __init__(self, title, parent=None, id=wx.ID_ANY):
        wx.Frame.__init__(self, parent, id, title, style=wx.DEFAULT_FRAME_STYLE | wx.BORDER_SUNKEN, size=wx.Size(600, 550))

        self.auiManager = wx.aui.AuiManager()
        self.auiManager.SetManagedWindow(self)

        self.menuBar = wx.MenuBar()
        file_menu = wx.Menu()
        self.menuBar.Append(file_menu, "File")
        file_menu.Append(wx.ID_OPEN, "Open")
        file_menu.Append(wx.ID_SAVE, "Save")
        file_menu.Append(wx.ID_SAVEAS, "Save as")
        self.SetMenuBar(self.menuBar)

        toolbar = wx.ToolBar(self, wx.ID_ANY)
        toolbar.SetToolBitmapSize(wx.Size(16,16))
        toolbar.AddTool(wx.ID_OPEN, 
                wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN),
                shortHelpString = "Open")
        toolbar.AddTool(wx.ID_SAVE, 
                wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE),
                shortHelpString = "Save")
        toolbar.AddTool(wx.ID_SAVEAS, 
                wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS),
                shortHelpString = "Save as")
        toolbar.SetToolShortHelp(wx.ID_SAVEAS, "Save as")
        toolbar.Realize()
        
        self.auiManager.AddPane(toolbar, wx.aui.AuiPaneInfo().CaptionVisible(False).Top().Position(0).Fixed().CloseButton(False))

        self.auiManager.AddPane(self.CreateNotebook(), wx.aui.AuiPaneInfo().CloseButton(False).CenterPane())

        # The size of the AUI panes is only determined after auiManager.Update()
        self.auiManager.Update()

        wx.EVT_MENU(self, wx.ID_OPEN, self.OnFileOpen)
        wx.EVT_MENU(self, wx.ID_SAVE, self.OnFileSave)
        wx.EVT_MENU(self, wx.ID_SAVEAS, self.OnFileSaveAs)
        
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnNotebookPageChange)

        self.statbar = self.CreateStatusBar(2)  # status bar for displaying pixel values/histogram info
        # We have to use a separate FileDropper instance for each area we 
        # want to have support drag-and-drop, or else the program segfaults
        # on exit (presumably due to a double-free).
        # Handles dropping on the upper area of the window with the buttons
        self.SetDropTarget(FileDropper(self))
        # Handles dropping on the main area of the window with the images
        self.controlPanelsNotebook.SetDropTarget(FileDropper(self))

        ## Store this position for later so we can refer to it when
        # opening new files.
        self.origPos = self.GetPosition()

        
    def CreateNotebook(self):
        self.controlPanelsNotebook = wx.aui.AuiNotebook(self, wx.ID_ANY, style=wx.aui.AUI_NB_DEFAULT_STYLE | wx.aui.AUI_NB_WINDOWLIST_BUTTON | wx.aui.AUI_NB_TAB_FIXED_WIDTH)

        if sys.platform == 'linux2':
            self.controlPanelsNotebook.SetNormalFont(wx.NORMAL_FONT)
            self.controlPanelsNotebook.SetSelectedFont(wx.NORMAL_FONT)  # do not use bold for selected tab
            self.controlPanelsNotebook.SetMeasuringFont(wx.NORMAL_FONT)
        return self.controlPanelsNotebook

    def OnFileOpen(self,event):
        dialog = wx.FileDialog(self, "Please select a file to open", 
                               style = wx.FD_OPEN | wx.FD_MULTIPLE)
        if dialog.ShowModal() == wx.ID_OK:
            for file in dialog.GetPaths():
                self.openFile(file)

    def OnFileSave(self,event):
        pageIdx = self.controlPanelsNotebook.GetSelection()  ## returns -1 when no notebook window is open
        if pageIdx >= 0:
            curPanel = self.controlPanelsNotebook.GetPage(pageIdx)

            targetPath = curPanel.getFilePath()
            permission = wx.MessageBox("Overwrite %s?" % targetPath, 
                    "Please confirm", 
                    style = wx.OK | wx.CANCEL)
            if permission != wx.OK:
                return
                    
            curPanel.dataDoc.alignAndCrop(savePath = targetPath)

            im_to_edit = Mrc.bindFile(targetPath)

            self.controlPanelsNotebook.DeletePage(pageIdx)
            self.controlPanelsNotebook.InsertPage(pageIdx, 
                    controlPanel.ControlPanel(self, im_to_edit),
                    os.path.basename(targetPath), select=True)

    def OnFileSaveAs(self,event):
        pageIdx = self.controlPanelsNotebook.GetSelection()  ## returns -1 when no notebook window is open
        if pageIdx >= 0:
            curPanel = self.controlPanelsNotebook.GetPage(pageIdx)
            caption = self.controlPanelsNotebook.GetPageText(pageIdx)
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



class FileDropper(wx.FileDropTarget):
    def __init__(self, parent):
        wx.FileDropTarget.__init__(self)
        self.parent = parent


    ## Open the dropped files, in reverse order because they seem to be handed
    # to us backwards.
    def OnDropFiles(self, x, y, filenames):
        for file in filenames[::-1]:
            self.parent.openFile(file)

