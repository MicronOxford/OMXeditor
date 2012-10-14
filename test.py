import sys
import Priithon.Mrc
import datadoc
import numpy

file = Priithon.Mrc.bindFile(sys.argv[1])
doc = datadoc.DataDoc(file)

data = doc.imageArray[0]
out = numpy.zeros(data.shape)
for t in xrange(data.shape[0]):
    for z in xrange(data.shape[1]):
        print "Time %d Z %d" % (t, z)
        out[t, z] = numpy.flipud(numpy.rot90(data[t, z], 3))
doc.imageArray[0] = out
doc.alignAndCrop(savePath = "%s-fixed.mrc" % sys.argv[1])
