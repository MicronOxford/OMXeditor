import numpy
import datadoc
from OpenGL.GL import *
import OpenGL.GL as GL
import wx
import wx.glcanvas

## Vertical adjustment for the size of the menubar
VERTICAL_PADDING = 16

## Minimum size in pixels of a viewer in any dimension.
# This would be smaller, but apparently WX windows aren't allowed to be 
# shorter than this.
MIN_VIEWER_SIZE = 150 - VERTICAL_PADDING

## Maximum initial size in pixels of a viewer in any dimension, to keep 
# windows from going off the edge of the monitor for large datasets.
MAX_VIEWER_SIZE = 600

## Simple window that contains a GLViewer instance.
class ViewerWindow(wx.Frame):
    def __init__(self, parent, axes, **kwargs):
        title = "%s-%s view" % (datadoc.DIMENSION_LABELS[axes[0]], 
                datadoc.DIMENSION_LABELS[axes[1]])
        wx.Frame.__init__(self, parent, title = title, 
                style = wx.RESIZE_BORDER | wx.CAPTION)

        self.viewer = GLViewer(self, viewManager = parent, 
                axes = axes, **kwargs)
        self.dataSize = self.viewer.dataDoc.getSliceSize(*axes)

        # Enforce a minimum size in each dimension.
        targetSize = list(self.dataSize)
        for i, val in enumerate(self.dataSize):
            targetSize[i] = min(MAX_VIEWER_SIZE, max(MIN_VIEWER_SIZE, val))
        targetSize[1] += VERTICAL_PADDING

        self.SetSize(targetSize)

        self.Bind(wx.EVT_SIZE, self.onSize)
        self.Show()


    ## Resize our canvas to fill the window, adjusting zoom factors to suit.
    def onSize(self, event):
        size = list(self.GetSize())
        size[1] -= VERTICAL_PADDING
        self.viewer.setSize(size, self.dataSize)
        event.Skip()



## This class handles displaying multi-channel 2D images. It includes a 
# crop box and a crosshairs, both of which can be manipulated by the mouse. 
# Most of the actual drawing logic is handled in the Image class.
class GLViewer(wx.glcanvas.GLCanvas):
    ## Instantiate.
    # \param axes: tuple that labels which of the dimensions this viewer shows.
    #        The ordering is WTZYX (that is, if our tuple is e.g. (4, 2) then
    #        we're showing an XZ slice), so this can be used as an index into 
    #        things in the DataDoc.
    def __init__(self, parent, axes = (1, 2), dataDoc = None,
                 viewManager = None,
                 style = 0, size = wx.DefaultSize):
        wx.glcanvas.GLCanvas.__init__(self, parent, style = style, size = size)

        ## DataDoc instance holding the data we show.
        self.dataDoc = dataDoc

        ## Controlling super-parent.
        self.viewManager = viewManager

        ## List of Image instances
        self.imgList = []

        ## Set of Images that need to have their refresh() method called
        # next time OnPaint runs.
        self.imagesToRefresh = set()

        ## Cursor to default to when not displaying any special cursor.
        self.defaultCursor = self.GetCursor()

        ## Dimensions we are displaying; corresponds to dimensions in 
        # the dataDoc instance (T/W/Z/Y/X).
        self.axes = axes

        ## Scaling factors in X and Y
        self.scaleX = 1.0
        self.scaleY = 1.0

        ## Whether or not the mouse is dragging something
        self.isMouseDragging = False

        ## Position of the mouse in the previous update cycle.
        self.mousePrevPos = []
        
        ## If true, then dragging is modifying the slice lines.
        self.amDraggingSlicelines = False
        
        ## Indices of sliceline dimension(s) being dragged.
        self.dragIndices = []
        
        ## If true, then dragging is modifying the cropbox.
        self.amDraggingCropbox = False
        
        ## Whether a given dimension's cropbox is having its min or max 
        # modified.
        self.cropMinMax = []
        
        ## Whether or not the current cursor is our default cursor. Sadly wx
        # doesn't allow you to compare cursors in any meaningful way.
        self.isCurrentCursorDefault = True

        ## Whether or not we've done some one-time initialization work.
        self.haveInitedGL = False

        ## Context instance, needed as of WX 2.9.
        self.context = wx.glcanvas.GLContext(self)

        wx.EVT_PAINT(self, self.OnPaint)
        wx.EVT_MOUSE_EVENTS(self, self.OnMouse)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
    
        
    def InitGL(self):
        self.w, self.h = self.GetClientSizeTuple()
        self.SetCurrent(self.context)
        glClearColor(0.3, 0.3, 0.3, 0.0)   ## background color

        self.haveInitedGL = True


    def addImgL(self, imgL, smin=0, smax=0, refreshNow=1):
        '''
        append images from a list of them
        '''
        for i, img in enumerate(imgL):
            self.addImg(i, img, smin, smax)
        if refreshNow:
            self.Refresh(0)


    ## Update image data, or create a new Image instance if we don't have one
    # in the indicated slot already.
    def addImg(self, index, img, smin=0, smax=10000):
        pic_ny, pic_nx = img.shape

        self.pic_ny, self.pic_nx = pic_ny,pic_nx

        self.SetCurrent(self.context)
        if len(self.imgList) <= index:
            newImage = Image(img, smin, smax)
            self.imgList.append(newImage)
        else:
            self.imgList[index].updateImage(img, smin, smax)


    def changeHistScale(self, imgidx, smin,smax, RefreshNow=1):
        images = self.imgList
        if imgidx != -1:
            images = [self.imgList[imgidx]]
        for image in images:
            image.setMinMax(smin, smax)
        self.imagesToRefresh.update(set(images))

        if RefreshNow:
            self.Refresh(False)

    def changeImgOffset(self, imgidx, tx, ty, rot, mag, RefreshNow=1):
        self.imgList[imgidx].setTransform(tx, ty, rot, mag)

        if RefreshNow:
            self.Refresh(False)

    def setColor(self, imgidx, color, RefreshNow=1):
        self.imgList[imgidx].setColor(color)
        if RefreshNow:
            self.Refresh(0)

    def toggleVisibility(self, imgidx, RefreshNow = 1):
        self.imgList[imgidx].toggleVisibility()
        if RefreshNow:
            self.Refresh(0)
        
    def OnPaint(self, event):
        try:
            dc = wx.PaintDC(self)
        except:
            return

        if not self.haveInitedGL:
            self.InitGL()
            
        self.SetCurrent(self.context)

        glViewport(0, 0, self.w, self.h)
        glMatrixMode (GL_PROJECTION)
        glLoadIdentity ()
        glOrtho (0, self.w, 0, self.h, 1., -1.)
        glMatrixMode (GL_MODELVIEW)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        glLoadIdentity()

        for image in self.imagesToRefresh:
            image.refresh()

        self.imagesToRefresh = set()

        glScalef(self.scaleX, self.scaleY, 1)
            
        if self.viewManager.getIsViewCropped():
            # Set up some clipping planes based on the relevant portion 
            # of the cropbox.
            lx = self.dataDoc.cropMin[self.axes[0]]
            ux = self.dataDoc.cropMax[self.axes[0]]
            ly = self.dataDoc.cropMin[self.axes[1]]
            uy = self.dataDoc.cropMax[self.axes[1]]

            plane0 = [0.0, 1.0, 0.0, -ly]
            plane1 = [0.0, -1.0, 0.0, uy]
            plane2 = [1.0, 0.0, 0.0, -lx]
            plane3 = [-1.0, 0.0, 0.0, ux]
            
            glClipPlane(GL_CLIP_PLANE0, plane0)
            glEnable(GL_CLIP_PLANE0)
            glClipPlane(GL_CLIP_PLANE1, plane1)
            glEnable(GL_CLIP_PLANE1)
            glClipPlane(GL_CLIP_PLANE2, plane2)
            glEnable(GL_CLIP_PLANE2)
            glClipPlane(GL_CLIP_PLANE3, plane3)
            glEnable(GL_CLIP_PLANE3)
        else:
            glDisable(GL_CLIP_PLANE0)
            glDisable(GL_CLIP_PLANE1)
            glDisable(GL_CLIP_PLANE2)
            glDisable(GL_CLIP_PLANE3)

        ## first, for each image in the list at its particular position,
        ## draw a black rectangle so that the colors can blend
        glColor3i(0, 0, 0)
        for image in self.imgList:
            if image.isVisible:
                imageData = image.imageData
                tx, ty, rot, mag = image.dx, image.dy, image.angle, image.zoom
                cx,cy = imageData.shape[-1]/2., imageData.shape[-2]/2.
                glPushMatrix()
                # Move so we rotate about the center.
                glTranslated(cx,cy, 0)
                if self.axes == (4, 3):   ## mag both dimesions in x-y view
                    glScaled(mag,mag, 1)
                elif self.axes == (4, 2):   ## mag only horizontal dimesion in x-z view
                    glScaled(mag, 1, 1)
                else:         ## mag only vertical dimesion in z-y view
                    glScaled(1, mag, 1)
                glRotated(rot, 0,0,1)
                glTranslated(tx-cx,ty-cy, 0)
                glColor3f(0, 0, 0)
                glBegin(GL_QUADS)
                glVertex2i(0, 0)
                glVertex2i(self.pic_nx, 0)
                glVertex2i(self.pic_nx, self.pic_ny)
                glVertex2i(0, self.pic_ny)
                glEnd()
                glPopMatrix()

        # Now draw each image.
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_ONE, GL_ONE)

        for image in self.imgList:
            if image.isVisible:
                scaleAxes = [0, 1]
                if self.axes == (4, 2):
                    # Magnify only X
                    scaleAxes = [0]
                elif self.axes == (3, 2):
                    # Magnify only Y
                    scaleAxes = [1]
                image.render(scaleAxes)

        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)

        # Draw slice lines.
        index = list(self.axes)
        cropBox = [self.dataDoc.cropMin[index], self.dataDoc.cropMax[index]]
        sliceCenter = self.dataDoc.curViewIndex[index]

        glColor3f(.5, .5, .5)
        glLineWidth(1)
        glBegin(GL_LINES)
        glVertex2f(sliceCenter[0], cropBox[0][1])
        glVertex2f(sliceCenter[0], cropBox[1][1])
        glVertex2f(cropBox[0][0], sliceCenter[1])
        glVertex2f(cropBox[1][0], sliceCenter[1])
        glEnd()

        # Draw crop box
        glBegin(GL_LINE_LOOP)
        glVertex2f(cropBox[0][0], cropBox[0][1])
        glVertex2f(cropBox[1][0], cropBox[0][1])
        glVertex2f(cropBox[1][0], cropBox[1][1])
        glVertex2f(cropBox[0][0], cropBox[1][1])
        glEnd()

        glFlush()
        glPopMatrix()
        self.SwapBuffers()


    def doOnMouse(self, xeff, yeff):
        cropMin = self.dataDoc.cropMin[list(self.axes)]
        cropMax = self.dataDoc.cropMax[list(self.axes)]

        sliceHoriz = self.dataDoc.curViewIndex[self.axes[0]]
        sliceVert   = self.dataDoc.curViewIndex[self.axes[1]]

        haveSetCursor = False
        if not self.isMouseDragging:
            # Check if we're close to a sliceline or the cropbox, and set
            # the cursor and some internal state appropriately.
            # The first tuple is the required position of the mouse to 
            # trigger the cursor change. The second tuple has the cursor to 
            # change to, the type of modification to perform (either moving
            # the slicelines or cropbox), and the third describes how dragging
            # the mouse will affect values.
            locCursorActions = [
                    # Both slice lines.
                    ((sliceHoriz, sliceVert), 
                        (wx.CURSOR_SIZING, 'slice', list(self.axes))),
                    # Horizontal slice line; None indicates we should ignore
                    # motion in the X direction.
                    ((None, sliceVert), 
                        (wx.CURSOR_SIZENS, 'slice', [None, self.axes[1]])),
                    # Vertical slice line
                    ((sliceHoriz, None), 
                        (wx.CURSOR_SIZEWE, 'slice', [self.axes[0], None])),
                    # Upper-left corner
                    ((cropMin[0], cropMax[1]), 
                        (wx.CURSOR_SIZENWSE, 'crop', ('min', 'max'))),
                    # Upper-right corner
                    ((cropMax[0], cropMax[1]), 
                        (wx.CURSOR_SIZENESW, 'crop', ('max', 'max'))),
                    # Lower-left corner
                    ((cropMin[0], cropMin[1]), 
                        (wx.CURSOR_SIZENESW, 'crop', ('min', 'min'))),
                    # Lower-right corner
                    ((cropMax[0], cropMin[1]), 
                        (wx.CURSOR_SIZENWSE, 'crop', ('max', 'min'))),
                    # Upper edge
                    ((None, cropMax[1]),
                        (wx.CURSOR_SIZENS, 'crop', (None, 'max'))),
                    # Lower edge
                    ((None, cropMin[1]),
                        (wx.CURSOR_SIZENS, 'crop', (None, 'min'))),
                    # Left edge
                    ((cropMin[0], None),
                        (wx.CURSOR_SIZEWE, 'crop', ('min', None))),
                    # Right edge
                    ((cropMax[0], None),
                        (wx.CURSOR_SIZEWE, 'crop', ('max', None))),
            ]
            for loc, (cursor, action, metadata) in locCursorActions:
                xDist = 0
                yDist = 0
                if loc[0] is not None:
                    xDist = abs(xeff - loc[0])
                if loc[1] is not None:
                    yDist = abs(yeff - loc[1])
                if xDist <= 6 and yDist <= 6:
                    self.SetCursor(wx.StockCursor(cursor))
                    self.isCurrentCursorDefault = False
                    haveSetCursor = True
                    if action == 'crop':
                        self.amDraggingCropbox = True
                        self.amDraggingSlicelines = False
                        self.cropMinMax = list(metadata)
                    else:
                        self.amDraggingSlicelines = True
                        self.amDraggingCropbox = False
                        self.dragIndices = list(metadata)
                    break

        if not haveSetCursor and not self.isMouseDragging:
            self.SetCursor(self.defaultCursor)
            self.isCurrentCursorDefault = True

        if self.isMouseDragging and not self.isCurrentCursorDefault:
            delta = [xeff - self.mousePrevPos[0], yeff - self.mousePrevPos[1]]
            if self.amDraggingSlicelines:
                motionMap = [0, 0, 0, 0, 0]
                for i, axis in enumerate(self.dragIndices):
                    if axis is not None:
                        motionMap[self.axes[i]] = delta[i]
                self.viewManager.moveSliceLines(motionMap)
            elif self.amDraggingCropbox:
                for i, axis in enumerate(self.cropMinMax):
                    cropAdjustment = [0, 0, 0, 0, 0]
                    cropAdjustment[self.axes[i]] += delta[i]
                    if axis == 'min':
                        self.dataDoc.moveCropbox(cropAdjustment, isMin = True)
                    elif axis == 'max':
                        self.dataDoc.moveCropbox(cropAdjustment, isMin = False)
                    self.viewManager.refreshViewers()
                self.viewManager.updateCropboxEdit()
            self.mousePrevPos = [xeff, yeff]
            self.Refresh()

        # For some reason, setting the statusbar text when we're dragging 
        # stuff around causes horrible flickering effects. 
        if not self.isMouseDragging:
            pic_nx, pic_ny = self.imgList[0].imageData.shape
            # Generate the TZYX coordinate we want info on.
            coord = numpy.array(self.dataDoc.curViewIndex[1:])
            # Subtract 1 because wavelength isn't included in the coord variable
            coord[self.axes[0] - 1] = xeff
            coord[self.axes[1] - 1] = yeff
            values, mappedCoords = self.dataDoc.getValuesAt(coord)
            for wavelength in xrange(self.dataDoc.numWavelengths):
                text = u"\u03BB%d: " % wavelength
                axisLabel = "(%s-%s view)" % tuple([datadoc.DIMENSION_LABELS[a].lower() for a in self.axes])
                locLabel = "<%d, %d>" % (mappedCoords[wavelength][self.axes[0] - 1],
                        mappedCoords[wavelength][self.axes[1] - 1])
                text += "%s: at %s; %.2f" % (axisLabel, locLabel, values[wavelength])
                wx.GetApp().setStatusbarText(text, wavelength)

    
    def doLDown(self, xeff, yeff):
        if not self.isCurrentCursorDefault:
            # Mouse is over something the user can manipulate.
            self.isMouseDragging = True
            self.mousePrevPos = [xeff, yeff]


    def doLUp(self):
        self.isMouseDragging = False


    def OnMouse(self, ev):
        if ev.Entering():
            self.SetFocus()
        
        x, y = ev.GetPosition()
        y = self.h - y
        xEff, yEff = int(x / self.scaleX), int(y / self.scaleY)

        midButt = ev.MiddleDown() or (ev.LeftDown() and ev.AltDown())
        midIsButt = ev.MiddleIsDown() or (ev.LeftIsDown() and ev.AltDown())
        rightButt = ev.RightDown() or (ev.LeftDown() and ev.ControlDown())
        
        if ev.Leaving():
            # Mouse is leaving the canvas, so stop what we're doing.
            wx.GetApp().setStatusbarText('')
            self.doOnMouse(xEff, yEff)
            self.isMouseDragging = False
            return
        elif ev.LeftDown():
            self.doLDown(xEff,yEff)
        elif ev.LeftUp():
            self.doLUp()

        self.doOnMouse(xEff, yEff)
        # Let other handlers use the mouse too.
        ev.Skip()


    ## Return true if we're in the middle of dragging something around.
    def getIsMouseBusy(self):
        return self.isMouseDragging and not self.isCurrentCursorDefault


    def OnReload(self, event=None):
        self.Refresh(False)


    ## Update the size of the canvas by scaling it.
    def setSize(self, size, dataSize):
        self.scaleX = size[0] / float(dataSize[0])
        self.scaleY = size[1] / float(dataSize[1])
        self.w, self.h = size
        self.Refresh(0)


    ## Pass keyboard events through to the controller.
    def OnKey(self, event):
        self.viewManager.onKey(event.GetKeyCode())


## Maps numpy datatypes to OpenGL datatypes
dtypeToGlTypeMap = {
    numpy.uint8: GL.GL_UNSIGNED_BYTE,
    numpy.uint16: GL.GL_UNSIGNED_SHORT,
    numpy.int16: GL.GL_SHORT,
    numpy.float32: GL.GL_FLOAT,
    numpy.float64: GL.GL_FLOAT,
    numpy.int32: GL.GL_FLOAT,
    numpy.uint32: GL.GL_FLOAT,
    numpy.complex64: GL.GL_FLOAT,
    numpy.complex128: GL.GL_FLOAT,
}

## Maps numpy datatypes to the maximum value the datatype can represent
dtypeToMaxValMap = {
    numpy.uint16: (1 << 16) - 1,
    numpy.int16: (1 << 15) - 1,
    numpy.uint8: (1 << 8) - 1, 
    numpy.bool_: (1 << 8) - 1,
    numpy.float32: 1
}


## This class handles display of a single 2D array of pixel data.
class Image:
    def __init__(self, imageData, imageMin, imageMax):
        self.imageData = imageData
        self.imageMin = imageMin
        self.imageMax = imageMax
        self.dx = 0
        self.dy = 0
        self.angle = 0
        self.zoom = 1
        self.color = (1, 1, 1)
        self.isVisible = True
        
        self.bindTexture()
        self.refresh()

    def bindTexture(self):
        pic_ny, pic_nx = self.imageData.shape

        if self.imageMin == 0 and self.imageMax == 0:
            self.imageMin = self.imageData.min()
            self.imageMax = self.imageData.max()

        # Generate texture sizes that are powers of 2
        tex_nx = 2
        while tex_nx < pic_nx:
            tex_nx *= 2
        tex_ny = 2
        while tex_ny < pic_ny:
            tex_ny *= 2

        self.picTexRatio_x = float(pic_nx) / tex_nx
        self.picTexRatio_y = float(pic_ny) / tex_ny

        self.textureID = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureID)

        # Define this new texture object based on self.imageData's geometry
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER,
                GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER,
                GL.GL_NEAREST)

        imgType = self.imageData.dtype.type
        if imgType not in dtypeToGlTypeMap:
            raise ValueError, "Unsupported data mode %s" % str(imgType)
        GL.glTexImage2D(GL.GL_TEXTURE_2D,0,  GL.GL_RGB, tex_nx,tex_ny, 0,
                     GL.GL_LUMINANCE, dtypeToGlTypeMap[imgType], None)


    def refresh(self):
        minMaxRange = float(self.imageMax - self.imageMin)
        if abs(self.imageMax - self.imageMin) < 1:
            minMaxRange = 1
        
        imgType = self.imageData.dtype.type
        fBias = -self.imageMin / minMaxRange
        f = dtypeToMaxValMap[imgType] / minMaxRange
        
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureID)

        GL.glPixelTransferf(GL.GL_RED_SCALE,   f)
        GL.glPixelTransferf(GL.GL_GREEN_SCALE, f)
        GL.glPixelTransferf(GL.GL_BLUE_SCALE,  f)

        GL.glPixelTransferf(GL.GL_RED_BIAS,   fBias)
        GL.glPixelTransferf(GL.GL_GREEN_BIAS, fBias)
        GL.glPixelTransferf(GL.GL_BLUE_BIAS,  fBias)

        GL.glPixelTransferf(GL.GL_MAP_COLOR, False)

        GL.glPixelStorei(GL.GL_UNPACK_SWAP_BYTES,
                not self.imageData.dtype.isnative)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, self.imageData.itemsize)
        
        imgString = self.imageData.tostring()

        pic_ny, pic_nx = self.imageData.shape

        if imgType not in dtypeToGlTypeMap:
            raise ValueError, "Unsupported data mode %s" % str(imgType)
        GL.glTexSubImage2D(GL.GL_TEXTURE_2D, 0, 0, 0, pic_nx, pic_ny,
                GL.GL_LUMINANCE, dtypeToGlTypeMap[imgType], imgString)


    def render(self, scaleAxes):
        cx,cy = self.imageData.shape[-1]/2., self.imageData.shape[-2]/2.
        GL.glPushMatrix()

        # To rotate about the center, first we have to move to it.
        GL.glTranslated(self.dx + cx, self.dy + cy, 0)

        scale = [1, 1, 1]
        for axis in scaleAxes:
            scale[axis] = self.zoom
        GL.glScaled(*scale)

        GL.glRotated(-self.angle, 0, 0, 1)
        GL.glTranslated(-cx, -cy, 0)

        GL.glColor3fv(self.color)
        
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureID)

        GL.glBegin(GL.GL_QUADS)
       
        pic_ny, pic_nx = self.imageData.shape

        ###//(0,0) at left bottom
        GL.glTexCoord2f(0, 0)
        GL.glVertex2i(0, 0)
            
        GL.glTexCoord2f(self.picTexRatio_x, 0)
        GL.glVertex2i(pic_nx, 0)
            
        GL.glTexCoord2f(self.picTexRatio_x, self.picTexRatio_y)
        GL.glVertex2i(pic_nx, pic_ny)
            
        GL.glTexCoord2f(0, self.picTexRatio_y)
        GL.glVertex2i(0, pic_ny)

        GL.glEnd()
        GL.glPopMatrix()


    ## Free the allocated GL texture
    def wipe(self):
        GL.glDeleteTextures(self.textureID)
   

    ## Accept a new array of image data.
    def updateImage(self, imageData, imageMin, imageMax):
        self.imageData = imageData
        self.imageMin = imageMin
        self.imageMax = imageMax

        self.wipe()
        self.bindTexture()
        self.refresh()


    def setMinMax(self, imageMin, imageMax):
        self.imageMin = imageMin
        self.imageMax = imageMax


    def setTransform(self, dx, dy, angle, zoom):
        self.dx = dx
        self.dy = dy
        self.angle = angle
        self.zoom = zoom


    def setColor(self, color):
        self.color = color


    def toggleVisibility(self):
        self.isVisible = not self.isVisible
