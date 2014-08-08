import matplotlib
matplotlib.use('WXAgg')
import numpy
import pylab
import wx
import util

## This module shows a window displaying a plot of alignment progress.
# Much of it is adapted from this matplotlib example:
# http://eli.thegreenplace.net/files/prog_code/wx_mpl_dynamic_graph.py.txt


## This class provides a window that displays a plot, showing how much 
# improvement in alignment has been achieved. 
class AlignProgressWindow(wx.Frame):
    def __init__(self, parent, numWavelengths):
        wx.Frame.__init__(self, parent,
                style = wx.RESIZE_BORDER | wx.FRAME_TOOL_WINDOW | wx.CAPTION)
        ## Must implement clearProgressFrame() so we can tell it when we
        # are destroyed.
        self.parent = parent
        ## How many lines we need to be able to support -- one per wavelength.
        self.numWavelengths = numWavelengths
        ## Data for each wavelength
        self.data = [[] for i in xrange(numWavelengths)]

        ## matplotlib Figure instance to hold the plot. The sizing here is
        # pretty arbitrary as it gets resized by the canvas anyway.
        self.figure = matplotlib.figure.Figure((6, 4), dpi = 100, 
                facecolor = (1, 1, 1))
        
        ## matplotlib Axes instance to display the plot.
        self.axes = self.figure.add_subplot(1, 1, 1)
        self.axes.set_axis_bgcolor('white')
        self.axes.set_title('Alignment progress', size = 12)
        self.axes.set_xlabel('Iterations')
        self.axes.set_ylabel('1 - correlation coefficient')
        pylab.setp(self.axes.get_xticklabels(), fontsize = 8)
        pylab.setp(self.axes.get_yticklabels(), fontsize = 8)

        ## Results of calling self.axes.plot
        self.plotData = []
        ## Lines showing the best value for each wavelength.
        self.bestLines = []
        ## Whether or not we should update the line when new data is received.
        # Set to false when we switch to aligning in 3D.
        self.alignModeCutoffPoint = []
        for wavelength in xrange(self.numWavelengths):
            self.alignModeCutoffPoint.append(None)
            self.plotData.append(
                    self.axes.plot(
                        self.data[wavelength],
                        linewidth = 1, 
                        color = parent.colors[wavelength]
                    )[0]
            )
            # All lines start off invisible
            line = matplotlib.lines.Line2D(numpy.arange(10),
                    numpy.array([.5] * 10),
                    linestyle = '--',
                    color = parent.colors[wavelength],
                    visible = False)
            self.bestLines.append(line)
            self.axes.add_line(line)

        ## We need to hold onto this sizer so we can resize ourselves when
        # the close/print buttons are added.
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        ## matplotlib canvas object for drawing the plot.
        self.canvas = matplotlib.backends.backend_wxagg.FigureCanvasWxAgg(
                self, -1, self.figure)

        self.sizer.Add(self.canvas)

        textPanel = wx.Panel(self, -1, style = wx.BORDER_SUNKEN)
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(wx.StaticText(textPanel, -1, "Alignment stats:"))

        ## List of wx StaticText instances displaying the status of each
        # wavelength.
        self.statusTexts = []
        for wavelength in xrange(self.numWavelengths):
            text = wx.StaticText(textPanel, -1, ' ' * 150)
            panelSizer.Add(text)
            self.statusTexts.append(text)
        textPanel.SetSizerAndFit(panelSizer)
        self.sizer.Add(textPanel, 0, wx.ALL, 3)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
       
        ## Button to allow the user to save an image of the plot.
        self.saveButton = wx.Button(self, -1, "Save graph")
        self.saveButton.Bind(wx.EVT_BUTTON, self.onSave)
        buttonSizer.Add(self.saveButton, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        
        ## Button to destroy this window, since we don't show the normal
        # close-window button in the menubar.
        self.closeButton = wx.Button(self, -1, "Close window")
        self.closeButton.Bind(wx.EVT_BUTTON, self.onClose)
        buttonSizer.Add(self.closeButton, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

        self.sizer.Add(buttonSizer)

        self.SetBackgroundColour('white')
        self.SetSizerAndFit(self.sizer)

        # We'll show the buttons when alignment is done.
        self.saveButton.Hide()
        self.closeButton.Hide()

    
    ## Receive a new datapoint for one of the wavelengths
    def newData(self, wavelength, value):
        self.data[wavelength].append(value)
        self.draw()
        if self.alignModeCutoffPoint[wavelength] is None:
            best = min(self.data[wavelength])
            self.statusTexts[wavelength].SetLabel(
                    u"\u03BB%d: %f after %d iterations" % (wavelength, best, len(self.data[wavelength])))
        else:
            cutoff = self.alignModeCutoffPoint[wavelength]
            best2D = min(self.data[wavelength][:cutoff])
            num2D = len(self.data[wavelength][:cutoff])
            best3D = min(self.data[wavelength][cutoff:])
            num3D = len(self.data[wavelength][cutoff:])
            self.statusTexts[wavelength].SetLabel(
                    u"\u03BB%d: 2D %f after %d iterations (complete); 3D %f after %d iterations" % (wavelength, best2D, num2D, best3D, num3D))
        


    ## Receive notification that one of the wavelengths is now working in 3D,
    # so there'll be a discontinuity in the graph, which we mark with a 
    # vertical line.
    def switchTo3D(self, wavelength):
        cutoff = len(self.data[wavelength]) - 1
        line = matplotlib.lines.Line2D(
                numpy.array([cutoff]),
                numpy.array([0, 1]),
                linestyle = '--',
                color = self.parent.colors[wavelength])
        self.axes.add_line(line)
        self.alignModeCutoffPoint[wavelength] = cutoff


    ## Draw the plot.
    def draw(self):
        xMax = max([len(self.data[i]) for i in xrange(self.numWavelengths)])
        self.axes.set_xbound(0, max(50, xMax))
        self.axes.set_ybound(0, 1)
        self.axes.grid(True)
        pylab.setp(self.axes.get_xticklabels(), visible = True)

        for wavelength in xrange(self.numWavelengths):
            xData = numpy.arange(len(self.data[wavelength]))
            if self.data[wavelength]:
                self.plotData[wavelength].set_xdata(xData)
                self.plotData[wavelength].set_ydata(
                        numpy.array(self.data[wavelength]))
                
                if self.alignModeCutoffPoint[wavelength] is None:
                    # Draw the best 2D alignment value we've gotten so far.
                    self.bestLines[wavelength].set_data(xData, 
                            numpy.array([min(self.data[wavelength])] * len(xData))
                    )
                    self.bestLines[wavelength].set_visible(True)
            

        self.canvas.draw()


    ## All done with alignment.
    def finish(self):
        self.saveButton.Show()
        self.closeButton.Show()
        self.SetSizerAndFit(self.sizer)


    ## Save the graph as an image.
    def onSave(self, event = None):
        dialog = wx.FileDialog(self, "Where should the file be saved?",
                '', "alignment-plot.png",
                style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            self.figure.savefig(dialog.GetPath())


    ## Close the window.
    def onClose(self, event = None):
        self.Destroy()
        self.parent.clearProgressFrame()
