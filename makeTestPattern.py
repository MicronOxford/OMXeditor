import datadoc
import numpy as N
import scipy.ndimage
import Priithon.Mrc
import util

import sys
doc = datadoc.DataDoc(Priithon.Mrc.bindFile(sys.argv[1]))
doc.size = (doc.size[0], 1, doc.size[1] * doc.size[2], doc.size[3], doc.size[4])
data = N.array(doc.imageArray).reshape(doc.size)
doc.imageArray = data

doc.cropMax = N.array(doc.size, N.int)
print "Changed cropMax to",doc.cropMax

doc.alignAndCrop(savePath = 'out.mrc')
