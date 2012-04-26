import util

import Priithon.all
import Priithon.histogram

import numpy as N
import wx

class Histogram(wx.Panel):
    def __init__(self, parent, id, image, color, size):
        wx.Panel.__init__(self, parent, size = size)
        self.parent = parent
        self.id = id
        width = size[0] - 25
        self.hist = Priithon.histogram.HistogramCanvas(self, 
                size = (width, -1))
        self.hist.m_histGlRGB = color
        self.hist.SetMinSize((width, 40))
        self.hist_arr = None
        self.hist_min = None
        self.hist_max = None
        self.hist_toggleButton = None
        self.hist_show = True
        self.mmms = None

        self.toggleButton = wx.ToggleButton(self, -1, str(self.id), size=(20,-1))
        self.toggleButton.SetValue(True)
        self.parent.prepHelpText(self.toggleButton,
                "Toggle visibility",
                "Show/hide display of this wavelength."
        )
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.toggleButton, 0, wx.GROW | wx.ALL, 4)
        sizer.Add(self.hist, 1, wx.GROW | wx.ALL, 1)
        self.SetSizerAndFit(sizer)

        self.toggleButton.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggleButton)
        
        self.hist.doOnBrace = self.rescaleHistogram
        self.hist.doOnMouse = self.showHistogramValues

        self.hist_min = image.min()
        self.hist_max = image.max()

        self.hist_arr = N.zeros(shape = self.hist_max - self.hist_min, dtype=N.int32)

        self.recalcHist(image)


    def rescaleHistogram(self, l, r):
        self.parent.changeHistScale(self.id, l, r)


    def showHistogramValues(self, xEff, ev):
        left, right =  self.hist.leftBrace, self.hist.rightBrace
        # \todo Fix this violation of the law of Demeter
        if self.parent.dataDoc.imageArray.dtype.type in (N.uint8, N.int16, N.uint16, N.int32):
            wx.GetApp().setStatusbarText("I: %6.0f  left/right: %6.0f %6.0f"  %(xEff, left, right), self.id)
        else:
            wx.GetApp().setStatusbarText("I: %7.2f  left/right: %7.2f %7.2f"%(xEff, left, right), self.id)


    def recalcHist(self, image):
        '''
        recalculate histogram
        '''

        mmms = util.minMaxMedianStdDev(image)
        self.mmms = mmms

        if self.hist_arr is not None:
            self.hist_arr = Priithon.all.U.histogram(image, amin=self.hist_min, amax=self.hist_max, histArr=self.hist_arr)
            self.hist.setHist(self.hist_arr, self.hist_min, self.hist_max)
        else:
            resolution = 10000 
            a_h = Priithon.all.U.histogram(image, resolution, mmms[0], mmms[1])
            self.hist.setHist(a_h, mmms[0], mmms[1])


    def autoFit(self):
        self.hist.autoFit()


    ## Retrieve the min/max points (below min is 0, above max is 1).
    def getMinMax(self):
        return (self.hist.leftBrace, self.hist.rightBrace)


    def OnToggleButton(self, ev = None):
        if ev is not None:
            self.hist_show = self.toggleButton.GetValue()

        self.parent.setWavelengthVisibility(self.id, self.hist_show)

   
