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
import argparse

RESULT_TAG = {'saveAlignParameters': "EAL-PAR.txt",
              'alignAndCrop': "EAL.dv",
              'project': "EPJ.dv",
              'splitTimepoints': "EST.dv",
              'splitChannels': "ESC.dv",
              'mergeChannels': "EMG.dv",
              'reorderChannels': "ERO.dv"}
# TODO: split crop into separate operation


def resultName(dataDoc, operation):
    """
    Generate result filename based on input and tagged by operation.
    """
    basename = os.path.splitext(os.path.basename(dataDoc.filePath))[0]
    return basename + "_" + RESULT_TAG[operation]


def autoAlign(dataDoc, logfileFullpath=None):
    """
    Find alignment parameters relative to a reference channel,
    printing alignment progress info (optionally to logfile),
    and set these parameters in the dataDoc,
    """
    print "TODO: implement Auto-align runner"


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
    for channel in xrange(dataDoc.numWavelengths):
        alignParams = dataDoc.alignParams[channel]
        alignParams[:3] = dataDoc.convertToMicrons(alignParams[:3])
        for label, value in zip(['dx', 'dy', 'dz', 'angle', 'zoom'],
                                alignParams):
            handle.write("align-%d-%s: %s\n" % (channel, label, value))
    handle.close()


def alignAndCrop(dataDoc, fullpath=None):
    """
    Align and crop a DataDoc using its align and crop params, write Mrc file,
    return path to new DataDoc.
    """
    print "TODO: implement alignAndCrop"


def project(dataDoc):
    """
    Write a new Mrc file consisting of projected raw SI data,
    giving a pseudo-widefield image. Return a new DataDoc.
    """
    # 1. set up a new ndarray to hold the result
    ndIn = dataDoc.getImageArray()
    ndOut = numpy.ndarray(shape=ndIn.shape, dtype=ndIn.dtype)


    # 2. iterate through output Z, filling with averaged result
    #    assuming Phase and Angle are part of Z - i.e. PZA

    # 3. create a new Mrc and DataDoc / save the result


def splitTimepoints(dataDoc, timePoints, fullpath=None):
    """
    Write new Mrc file for a subset of timepoints (zero-based index),
    return a new DataDoc for the file.
    """
    print "TODO: implement SplitTimepoints"


def splitChannels(doc, channels):
    """
    Write new Mrc file for a subset of channels (zero-based index),
    return a new DataDoc for the file.
    """
    print "TODO: implement SplitChannels"


def reorderChannels(doc, newMap):
    """
    Write a new Mrc file with Re-ordered channels according to list mapping
    old->new; e.g. newMap = [2, 0, 1] means 0->2, 1->0, 2->1
    and return a new DataDoc for the file.
    """
    pathBase = os.path.splitext(doc.filePath)[0]
    tags = '_ERO'
    fileExt = ".dv"
    targetFilename = pathBase + tags + fileExt
    doc.saveSelection(savePath=targetFilename, wavelengths=newMap)
    # TODO, get new datadoc & return
    return True


def mergeChannels(docs):
    """
    Write a new Mrc file consisting of merged input DataDocs by appending
    channels in the order passed. It is assumed that for each DataDoc
    the non-channel dimensions are equal.
    Return a new DataDoc for the Mrc file.
    """
    return "mergeChannels returned"   # FIXME, incomplete below
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
    ndOut = numpy.ndarray(shape=shapeOut, dtype=docs[0].image.Mrc.dtype)
    print "NEW ARRAY SHAPE:-"
    print ndOut.shape
    # 3. Save resulting datadoc, return a ref to it, and add to our list


def printDocsInfo(dataDoc):
    """
    Print header info for an Mrc file.
    """
    print dataDoc.filePath
    print dataDoc.image.Mrc.info()


##########################################################
# this function is used when editor is invoked as a script
##########################################################
if __name__ == '__main__':
    """
    editor can be invoked as a script, passing in Mrc file paths
    and flags to run specific jobs.
    """
    ARGS = [('-f', '--files', "store", str,
             "comma-separated list of files to process"),
            ('-a', '--align', "store", int,
             "use this channel to auto-align Mrc file(s) and save parameters"),
            ('-b', '--batch-align', "store", str,
             "batch-align Mrc file(s) according to this parameter file"),
            ('-c', '--crop', "store", str,
             "crop the file(s) using comma-separated xmin,xmax,ymin,ymax"),
            ('-sc', '--split-channels', "store_true",
             "split the file(s) into one file per channel"),
            ('-st', '--split-timepoints', "store_true",
             "split the file(s) into one file per timepoint"),
            ('-m', '--merge', "store_true",
             "merge the files into a single file by appending channels"),
            ('-r', '--reorder', "store", str,
             "reorder channels 0,1,..N to the new order given, e.g. 3,2,1"),
            ('-p', '--project', "store_true",
             "project phases and angles for the raw SI data file(s)"),
            ('-i', '--info', "store_true",
             "display header info in the Mrc file(s)")]

    parser = argparse.ArgumentParser()
    for arg in ARGS:
        if arg[2] == "store_true":
            parser.add_argument(*arg[0:2], action=arg[2], help=arg[3])
        else:
            parser.add_argument(*arg[0:2], action=arg[2], type=arg[3],
                                help=arg[4])
    args = parser.parse_args()

    print args.files.split(',')
    if args.info:
        print("TODO: display Mrc file info")
    if isinstance(args.align, int):
        print("TODO: align these files using channel %d" % args.align)
    # FIXME, not implemented
