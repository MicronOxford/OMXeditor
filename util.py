import wx
import OpenGL.GL as GL
import threading

# key codes: 70=F, 76=L, 84=T, 66=B (as in First, Last, Top, Bottom)
KEY_MOTION_MAP = {
        70: (0, -1, 0, 0, 0),
        76: (0, 1, 0, 0, 0),
        66: (0, 0, -1, 0, 0),
        84: (0, 0, 1, 0, 0),
        wx.WXK_DOWN: (0, 0, 0, -1, 0),
        wx.WXK_UP: (0, 0, 0, 1, 0),
        wx.WXK_LEFT: (0, 0, 0, 0, -1),
        wx.WXK_RIGHT: (0, 0, 0, 0, 1),
}


# Convert wavelength (nm) into (R,G,B) tuple for approx color.
def waveToRGB(wave):
    """
    Convert wavelength (nm) into (R,G,B) tuple for approx color.
    """
    # "python style switch" ... using a dictionary - bizarre!
    RGBtuple = {
        wave<420 : (0.5,0,1),
        420<=wave<470 : (0,0,1),
        470<=wave<500 : (0,1,1),
        500<=wave<560 : (0,1,0),
        560<=wave<590 : (1,1,0),
        590<=wave<620 : (1,0.5,0),
        620<=wave<670 : (1,0,0),
        670<=wave : (0.5,0,0)
        }[1]
    return RGBtuple


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
        addHelperString(parent, rowSizer, helperString, labelHeightAdjustment, 
                wx.TOP)
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


## Create a new menu item and insert it into the given menu.
def addMenuItem(parent, menu, label, action):
    item = wx.MenuItem(menu, -1, label)
    parent.Bind(wx.EVT_MENU, action, id = item.GetId())
    menu.AppendItem(item)


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


## Call the passed-in function in a new thread.
def callInNewThread(function):
    def wrappedFunc(*args, **kwargs):
        threading.Thread(target = function, args = args, kwargs = kwargs).start()
    return wrappedFunc


## Decorator function used to ensure that a given function is only called
# in wx's main thread.
def callInMainThread(func):
    def wrappedFunc(*args, **kwargs):
        wx.CallAfter(func, *args, **kwargs)
    return wrappedFunc


printLock = threading.Lock()
## Simple function for debugging when dealing with multiple threads, since
# otherwise Python's "print" builtin isn't threadsafe.
def threadPrint(*args):
    with printLock:
        print " ".join([str(s) for s in args])
