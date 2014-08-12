import numpy
import scipy
import scipy.optimize
import threading
import time
import datadoc
import editor


## Step size multipliers to convince simplex to take differently-sized steps
# in each parameter. Simplex's initial step size is .00025 -- okay for zoom
# but too small to be likely to get the right translational or rotational
# offset.
STEP_MULTIPLIER = numpy.array([10000, 10000, 10000, 1])

## Multiplier to use specifically for the Z transform portion.
Z_MULTIPLIER = 20000

## As long as running Simplex improves our cost function by at least this
# much, we'll run it again.
MIN_COST_CHANGE = .1 ** 4


class AutoAligner():
    """
    Headless SimplexAlign runner with method stubs expected by SimplexAlign,
    since the SimplexAlign class is strongly coupled to the OMXeditor GUI.
    SimplexAlign calls back into the GUI / AutoAligner, so locking required.
    """

    def __init__(self, dataDoc, refChannel):
        self.dataDoc = dataDoc
        self.refChannel = refChannel
        self.alignerLock = threading.Lock()

    def run(self):
        """
        Use Simplex method to auto-align channels to the reference,
        updating dataDoc.alignParams with final alignment parameters.
        """
        channelsToAlign = range(self.dataDoc.numWavelengths)
        del channelsToAlign[self.refChannel]
        self.alignedChannels = dict([(i, False) for i in channelsToAlign])
        targetCoords = self.dataDoc.getSliceCoords((1, 2))
        referenceData = self.getFilteredData(self.refChannel)
        aligners = []
        for i in channelsToAlign:
            if i == self.refChannel:
                continue
            guess = [0.0, 0.0, 0.0, 0.0, 1.0]  # X, Y, Z, Rot, Zoom
            aligner = SimplexAlign(self, referenceData, i, guess,
                    shouldAdjustGuess = True)
            aligners.append(aligner)
        for aligner in aligners:
            aligner.join()

    def getFilteredData(self, channel, perpendicularAxes = (1, 2)):
        """
        Return data thresholded at mid-point between mean/max and normalized 0-1.
        """
        targetCoords = self.dataDoc.getSliceCoords(perpendicularAxes)
        baseData = self.dataDoc.takeSlice(targetCoords).astype(numpy.float)[channel]
        minCut = (baseData.max() + baseData.mean()) / 2
        maxCut = baseData.max()
        baseData[numpy.where(baseData < minCut)] = minCut
        baseData[numpy.where(baseData > maxCut)] = maxCut
        return (baseData - minCut) / (maxCut - minCut)


    def getFullVolume(self, channel, worker):
        """
        Return 3D array for channel + reference channel and pass to worker.
        """
        with self.alignerLock:
            result = self.dataDoc.alignAndCrop(
                    wavelengths = [self.refChannel, channel],
                    timepoints = [self.dataDoc.curViewIndex[1]])
            # Take the first timepoint.
            worker.setVolumes(result[0][0], result[1][0])

    def updateAutoAlign(self, startCost, currentCost, channel):
        """
        Report current cost for this channel.
        """
        with self.alignerLock:
            print "channel ", channel, " current cost = ", currentCost

    def alignSwitchTo3D(self, channel):
        """
        Aligner thread for this channel is now working on 3D.
        """
        with self.alignerLock:
            print "Starting 3D alignment for channel ", channel

    def finishAutoAligning(self, result, channel):
        """
        Act on notification from an aligner thread that it is done.
        """
        print "channel ", channel, " finished auto-aligning"
        with self.alignerLock:
            self.alignedChannels[channel] = True
            allDone = True
            for i, done in self.alignedChannels.iteritems():
                if not done:
                    allDone = False
                    break
            print "Final transformation: ", result, " for channel ", channel
            self.dataDoc.setAlignParams(channel, result)



## Use the Simplex algorithm as implemented in SciPy to find the transformation
# (as an XY translation, a rotation about Z, and a zoom factor) from the first
# matrix to the second matrix. Both matrices are 2D here; Z translation is
# not considered.
class SimplexAlign(threading.Thread):
    ## Instantiate the class and start aligning.
    # \param parent Invoker.
    # \param referenceData First array of data, that is held fixed. Needs to be
    #        floats normalized to the range [0, 1].
    # \param index movingData's wavelength.
    # \param guess Initial alignment parameters (dx, dy, rotation, zoom)
    # \param shouldAdjustGuess If true, use cross correlation to adjust the
    #        guess in an attempt to improve it.
    def __init__(self, parent, referenceData, index, guess,
                 shouldAdjustGuess = False):
        threading.Thread.__init__(self)
        ## Our parent needs to implement certain methods so we can communicate
        # with it.
        self.parent = parent
        ## This is the data for the wavelength that is not transformed; the
        # other wavelength attempts to align itself with this.
        self.referenceData = referenceData

        ## Which wavelength we are aligning.
        self.index = index
        ## Initial transformation that we think is vaguely close to actual
        # alignment.
        self.guess = guess

        # Improve the guess by doing a cross correlation.
        if shouldAdjustGuess:
            movingData = self.parent.getFilteredData(self.index)
            dx, dy = self.getOffset(self.referenceData, movingData)
            self.guess[0] += dx
            self.guess[1] += dy

        # Strip out the Z portion of the guess, for later use.
        self.zTransform = self.guess[2]
        self.guess = self.guess[:2] + self.guess[3:]

        self.startingCost = None
        self.currentCost = None

        ## This lock is used whenever we need to interact with our parent to
        # change data (i.e. at the transition from 2D to 3D alignment).
        self.dataLock = threading.Lock()

        ## For 3D alignment, the data that is held fixed in place.
        self.referenceVolume = None
        ## For 3D alignment, the data that moves with respect to
        self.movingVolume = None
        self.daemon = True
        self.start()


    ## Perform optimization. First we do 2D alignment; then we align Z while
    # holding the 2D transformation parameters fixed (on the assumption that
    # Z alignment is independent of 2D alignment).
    def run(self):
        # Keep iterating Simplex until the cost doesn't change much from
        # one iteration to the next. Simplex is prone to getting stuck in
        # local minima that are within the initial step size of the actual
        # minimum, but not within the *current* step size -- thus, restarting
        # Simplex resets its step size and allows it to get to the true minimum.
        delta = 1
        numHits = 0
        while delta > MIN_COST_CHANGE:
            transform = scipy.optimize.fmin(
                    self.cost, [0, 0, 0, 0],
                    xtol = .00001
            )
            print "  (channel ", self.index, ")"
            delta = abs(self.currentCost - self.startingCost)
            self.startingCost = self.currentCost
            self.guess = transform * STEP_MULTIPLIER + self.guess

        # Now optimize the Z alignment. This requires getting transformed 3D
        # volumes from the parent, which, due to thread communication, is a bit
        # tricky.
        # No Z alignment for flat images, of course.
        print "entering Z-alignment code for channel ", self.index
        if self.parent.dataDoc.size[2] > 1:
            self.parent.getFullVolume(self.index, self)
            while True:
                self.dataLock.acquire()
                # Note these are initialized to None in our constructor
                if self.referenceVolume is not None and self.movingVolume is not None:
                    self.dataLock.release()
                    break
                self.dataLock.release()
                time.sleep(.1)

            # Don't do Z offsets if the entire volume is still 2D
            if self.referenceVolume.shape[0] == 1:
                result = 0
            else:
                # Inform the progress dialog that we're in 3D mode now.
                self.parent.alignSwitchTo3D(self.index)
                print "Channel ", self.index, " switched to 3D"
                # Just a single pass here should be sufficient.
                result = scipy.optimize.fmin(self.cost3D,
                        [self.zTransform / Z_MULTIPLIER],
                        xtol = .0001)[0]
                # gb - put line below inside if/else and added initial zTransform
                self.zTransform = self.zTransform + result * Z_MULTIPLIER
            #self.zTransform = result * Z_MULTIPLIER

        transform = transform * STEP_MULTIPLIER + self.guess
        transform = (transform[0], transform[1], self.zTransform,
                     transform[2], transform[3])
        self.parent.finishAutoAligning(transform, self.index)


    ## Accept new working volumes from our parent.
    def setVolumes(self, referenceVolume, movingVolume):
        self.dataLock.acquire()
        self.referenceVolume = referenceVolume
        self.movingVolume = movingVolume
        self.dataLock.release()


    ## Return 1 minus the correlation coefficient between the two arrays.
    def cost(self, transform):
        # Adjust step size
        transform = transform * STEP_MULTIPLIER + self.guess
        # Pad out to Z for grabbing the slice.
        fullTransform = (transform[0], transform[1], self.zTransform,
                transform[2], transform[3])
        self.parent.dataDoc.alignParams[self.index] = fullTransform
        transformedMatrix = self.parent.getFilteredData(self.index)
        cost = 1 - self.correlationCoefficient(transformedMatrix, self.referenceData)
        if self.startingCost is None:
            self.startingCost = cost
        self.currentCost = cost
        self.parent.updateAutoAlign(self.startingCost, self.currentCost, self.index)
        return cost


    ## As self.cost, but we deal with a 3D array and only one transformation
    # parameter.
    def cost3D(self, transform):
        zTransform = transform[0] * Z_MULTIPLIER
        shiftedVolume = scipy.ndimage.interpolation.shift(
                self.movingVolume, [zTransform, 0, 0],
                order = 1, cval = self.parent.dataDoc.averages[self.index])
        cost = 1 - self.correlationCoefficient(shiftedVolume,
                self.referenceVolume)
        self.currentCost = cost
        #print "Current Z cost for",self.index,"is",cost,"for offset",zTransform
        self.parent.updateAutoAlign(self.startingCost, self.currentCost, self.index)
        return cost


    ## Return the correlation coefficient between two matrices.
    def correlationCoefficient(self, a, b):
        aTmp = a - a.mean()
        bTmp = b - b.mean()
        numerator = numpy.multiply(aTmp, bTmp).sum()
        aSquared = numpy.multiply(aTmp, aTmp).sum()
        bSquared = numpy.multiply(bTmp, bTmp).sum()
        return numerator / numpy.sqrt(aSquared * bSquared)


    ## Return an estimated offset (as an XY tuple) between two matrices using
    # cross correlation.
    def getOffset(self, a, b):
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
                coords[i] -= a.transpose().shape[i]
        try:
            # test / debug plot of correlation
            print "X,Y translation estimate for channel ", self.index, ": ", coords[0], ",", coords[1]
            plt.title("correlation for channel %d" % self.index)
            plt.imshow(correlation)
            plt.show()
        except NameError:
            # HACK: plt not defined, so debug plots not shown (TODO, improve)
            pass
        return coords

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    testDoc = datadoc.DataDoc('./test/testData.dv')
    testDoc.image.Mrc.info()
    print "Starting test data auto-alignment..."
    aligner = AutoAligner(testDoc, 0)
    aligner.run()
