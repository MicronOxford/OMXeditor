import wx

import numpy
import OpenGL.GL as GL
import scipy
import scipy.ndimage
import threading

## Copied from the OMX version.
def addLabeledInput(parent, sizer, id = -1, label = '',
                    defaultValue = '', size = (-1, -1), minSize = (-1, -1),
                    shouldRightAlignInput = False, border = 0, labelHeightAdjustment = 0,
                    controlType = None, helperString = '', flags = wx.ALL,
                    style = 0):
    if controlType is None:
        controlType = wx.TextCtrl
    rowSizer = wx.BoxSizer(wx.HORIZONTAL)
    rowSizer.SetMinSize(minSize)
    rowSizer.Add(wx.StaticText(parent, -1, label), 0, wx.TOP, labelHeightAdjustment)
    if helperString != '':
        addHelperString(parent, rowSizer, helperString)
    if shouldRightAlignInput:
        # Add an empty to suck up horizontal space
        rowSizer.Add((10, -1), 1, wx.EXPAND | wx.ALL, 0)
    control = controlType(parent, id, defaultValue, size = size, style = style)
    rowSizer.Add(control)
    sizer.Add(rowSizer, 0, flags, border)
    return control


## Add some explanatory text to the given sizer.
def addHelperString(parent, sizer, text, border = 0, flags = wx.ALL):
    label = wx.StaticText(parent, -1, " (What is this?)")
    label.SetForegroundColour((100, 100, 255))
    label.SetToolTipString(text)
    sizer.Add(label, 0, flags, border)


## Save an array as an image. Copied from 
# http://stackoverflow.com/questions/902761/saving-a-numpy-array-as-an-image
def imsave(filename, array, vmin=None, vmax=None, cmap=None, format=None, origin=None):
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure

    fig = Figure(figsize=array.shape[::-1], dpi=1, frameon=False)
    canvas = FigureCanvas(fig)
    fig.figimage(array, cmap=cmap, vmin=vmin, vmax=vmax, origin=origin)
    fig.savefig(filename, dpi=1, format=format)
  

## Save out the current OpenGL view as an image.
def saveGLView(filename):
    view = GL.glGetIntegerv(GL.GL_VIEWPORT)
    GL.glPixelStorei(GL.GL_PACK_ALIGNMENT, 1)
    GL.glReadBuffer(GL.GL_BACK_LEFT)
    pixels = GL.glReadPixels(0, 0, view[2], view[3], GL.GL_RGB, GL.GL_UNSIGNED_BYTE)
    image = wx.ImageFromData(int(view[2]), int(view[3]), pixels)
    image.SaveFile(filename, wx.BITMAP_TYPE_PNG)



## Apply a transformation to an input 3D array in ZYX order. Angle rotates
# each slice, zoom scales each slice (i.e. neither is 3D).
def transformArray(input, dx, dy, dz, angle, zoom):
    cosTheta = numpy.cos(-angle)
    sinTheta = numpy.sin(-angle)
    affineTransform = zoom * numpy.array(
            [[cosTheta, sinTheta], [-sinTheta, cosTheta]])

    invertedTransform = numpy.linalg.inv(affineTransform)    
    yxCenter = numpy.array(input.shape[1:]) / 2.0
    offset = -numpy.dot(invertedTransform, yxCenter) + yxCenter

    output = numpy.zeros(input.shape)
    for i, slice in enumerate(input):
        output[i] = scipy.ndimage.affine_transform(slice, invertedTransform,
                offset, output = numpy.float32, cval = slice.min())
    output = scipy.ndimage.interpolation.shift(output, [dz, dy, dx])

    return output


## Return the correlation coefficient between two matrices.
def correlationCoefficient(a, b):
    aTmp = a - a.mean()
    bTmp = b - b.mean()
    numerator = numpy.multiply(aTmp, bTmp).sum()
    aSquared = numpy.multiply(aTmp, aTmp).sum()
    bSquared = numpy.multiply(bTmp, bTmp).sum()
    return numerator / numpy.sqrt(aSquared * bSquared)


## Return an estimated offset (as an XY tuple) between two matrices using
# cross correlation.
def getOffset(a, b):
    aFT = numpy.fft.fftn(a)
    bFT = numpy.fft.fftn(b)
    correlation = numpy.fft.ifftn(aFT * bFT.conj()).real
    best = numpy.array(numpy.where(correlation == correlation.max()))
    # They're in YX order, so flip 'em.
    coords = best[:,0][::-1]
    # Negative offsets end up on the wrong side of the image, so 
    # correct for that.
    for i, val in enumerate(coords):
        if val > a.shape[i] / 2:
            coords[i] -= a.shape[i]

    return coords


## Call the passed-in function in a new thread.
def callInNewThread(function):
    def wrappedFunc(*args, **kwargs):
        threading.Thread(target = function, args = args, kwargs = kwargs).start()
    return wrappedFunc


## Simple utility function that I'm using to avoid having to invoke 
# precompiled functions in Priithon
def minMaxMedianStdDev(array):
    return (numpy.min(array), numpy.max(array), numpy.median(array), numpy.std(array))
