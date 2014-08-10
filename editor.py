"""
    The edit module collects together all non-interactive procedures
    and transformations that OMXeditor applies to MRC images.
    The intention is that its methods can be run interactively via the 
    various Editor GUI elements, or headless as scripted jobs.
    
    Authors: Graeme Ball (graeme.ball@bioch.ox.ac.uk)
             Chris Weisiger 
"""

import numpy
import os
import re
import scipy.ndimage.filters
import sys
import datadoc
import argparse


def resultName(dataDoc, operation):
    """
    Generate result filename based on input and tagged by operation.
    """
    tag = {
        'splitTimepoints': "EST.dv",
        'splitChannels': "ESC.dv",
        'reorderChannels': "ERO.dv",
        'mergeChannels': "EMG.dv",
        'project': "EPJ.dv",
        'autoAlign': "EAL.dv",
        'alignAndCrop': "EAC.dv",
        'saveAlignParameters': "EAL-PAR.txt"
    }[operation]
    basename = os.path.splitext(os.path.basename(dataDoc.filePath))[0]
    return basename + "_" + tag


def saveAlignParameters(dataDoc, fullpath=None):
    """
    Save crop and alignment parameters to a .txt file.
    """
    if fullpath is None:
        fullpath = os.path.dirname(dataDoc.filePath)
        fullpath += resultName(dataDoc, 'saveAlignParameters')
    handle = open(fullpath, 'w')
    cropParams = zip(dataDoc.cropMin, dataDoc.cropMax)
    for axis, index in [("X", -1), ("Y", -2), ("Z", -3), ("T", -4)]:
        handle.write("crop-min%s: %s\n" % (axis, cropParams[index][0]))
        handle.write("crop-max%s: %s\n" % (axis, cropParams[index][1]))
    #for label, value in zip(['minX', 'maxX', 'minY', 'maxY', 'minZ', 'maxZ', 'minT', 'maxT'], cropParams):
    #    handle.write("crop-%s: %s\n" % (label, value))
    #for wavelength in xrange(self.dataDoc.numWavelengths):
    #    alignParams = self.alignParamsPanels[wavelength].getParamsList()
    #    # Multiply by pixel size to get offsets in microns.
    #    alignParams[:3] = self.dataDoc.convertToMicrons(alignParams[:3])
    #    for label, value in zip(['dx', 'dy', 'dz', 'angle', 'zoom'], alignParams):
    #        handle.write("align-%d-%s: %s\n" % (wavelength, label, value))
    handle.close()


class Editor():
    """
    This class provides an interface for running OMX Editor tasks.
    It can be run interactively via the various Editor GUI elements,
    or headless for scripted jobs. It is initialized with a list of 
    DataDoc objects (which can be updated later).
    """

    def __init__(self, dataDocs):
        ## a list of datadocs
        self.dataDocs = dataDocs


    def printDocsInfo(self):
        """
        Print header info for a list of datadocs.
        """
        for doc in self.dataDocs:
            print doc.filePath
            print doc.image.Mrc.info()
    
    def splitTimepoints(self):
        """
        Write new datadoc for a subset of timepoints.
        """
        print "TODO: implement SplitTimepoints"

    def splitChannels(self):
        """
        Write new datadoc for a subset of timepoints.
        """
        print "TODO: implement SplitChannels"

    def reorderChannels(self, doc, newMap):
        """
        Re-order image channels according to list mapping old->new.
        e.g. newMap = [2, 0, 1] means 0->2, 1->0, 2->1
        """
        pathBase = os.path.splitext(doc.filePath)[0]
        tags = '_ERO'
        fileExt = ".dv"
        targetFilename = pathBase + tags + fileExt
        doc.saveSelection(savePath = targetFilename, wavelengths = newMap)
        # TODO, get new datadoc & add to list of docs
        return True
        

    def mergeChannels(self, docs):
        """                                                                     
        Merge selected DataDocs by appending channels in the order
        passed. It is assumed that for each DataDoc the non-channel 
        dimensions are equal.
        """                                                                     
        return "mergeChannels returned"   # coward
        shapeOut = []
        numChannelsOut = 0
        shapesExChannel = []
        # 1. check input - bail out if:-
        #    - we were not passed 1+ datadocs
        #    - the non-Channel dims are not identical
        for doc in docs:
            numChannelsOut += doc.size[0]
            shapesExChannel.append(list(doc.size)[1:5])
        for shape in shapesExChannel:
            if shape != shapesExChannel[0]:
                print 'FAIL: non-Channel dimensions must be identical'
                return
        shapeOut = list(docs[0].size)
        shapeOut[0] = numChannelsOut
        shapeOut = tuple(shapeOut)
        # 2. using input docs, set up a new ndarray to hold the result
        ndOut = numpy.ndarray(shape=shapeOut, dtype=ndIn.dtype)
        print "NEW ARRAY SHAPE:-"
        print ndOut.shape
        # 3. Save resulting datadoc, return a ref to it, and add to our list
        

    def project(self, doc):
        """                                                                     
        Project raw SI data to give pseudo-widefield image.
        """                                                                     
        print "all docs known to this Edits instance:-" 
        self.printDocsInfo()
        print "doc to work on: " + doc.filePath
        
        # 1. set up a new ndarray to hold the result
        ndIn = doc.getImageArray()
        ndOut = numpy.ndarray(shape=ndIn.shape, dtype=ndIn.dtype)
        

        # 2. iterate through output Z, filling with averaged result
        #    assuming Phase and Angle are part of Z - i.e. PZA

        # 3. create a new Mrc and DataDoc / save the result


    def alignAndCrop(self):
        """
        Align and crop a datadoc, returning path to new datadoc.
        """
        print "TODO: implement alignAndCrop"

    def autoAlign(self):
        """
        Find alignment parameters relative to a reference channel.
        """
        print "TODO: implement Auto-align runner"

    def batchAlignAndCrop(self):
        """
        Align and crop a list of datadocs, returning list of new paths.
        """
        print "TODO: implement batch batchAlignAndCrop"


#############################################################
# this function is used when OMXeditor is invoked as a script
#############################################################
if __name__ == '__main__':
    """
    OMXeditor can be invoked as a script, passing in Mrc file paths 
    and flags to run specific jobs.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--files', action="store", type=str, 
        help="comma-separated list of files to process")
    parser.add_argument('-a', '--align', action="store", type=int, 
        help="use this channel to auto-align Mrc file(s) and save parameters")
    parser.add_argument('-b', '--batch-align', action="store", type=str, 
        help="batch-align Mrc file(s) according to this parameter file")
    parser.add_argument('-c', '--crop', action="store", type=str,
        help="crop the file(s) using comma-separated xmin,xmax,ymin,ymax")
    parser.add_argument('-sc', '--split-channels', action="store_true", 
        help="split the file(s) into one file per channel")
    parser.add_argument('-st', '--split-timepoints', action="store_true", 
        help="split the file(s) into one file per timepoint")
    parser.add_argument('-m', '--merge', action="store_true",
        help="merge the files into a single file by appending channels")
    parser.add_argument('-r', '--reorder', action="store", type=str,
        help="reorder channels 0,1,..N to the new order given, e.g. 3,2,1")
    parser.add_argument('-p', '--project', action="store_true",
        help="project phases and angles for the raw SI data file(s)")
    parser.add_argument('-i', '--info', action="store_true",
        help="display header info in the Mrc file(s)")
    args = parser.parse_args()
    
    print args.files.split(',')
    if args.info:
        print("TODO: display Mrc file info")
    if isinstance(args.align, int):
        print("TODO: align these files using channel %d" % args.align)
    # FIXME, not implemented
    #editor = Editor(mrcFiles)
