#/usr/bin/env python
# -*- coding: ascii -*-

"""
cmos_stripe_filter
------------------

Simple python2 CLI script to Fourier Filter CMOS camera Stripes.

Requires DeltaVision data as input, writes filename_FFS.dv output.
"""

__author__ = "Graeme Ball (graemeball@googlemail.com)"
__copyright__ = "Copyright (c) 2014 Graeme Ball"
__license__ = "GPL v3"  # http://www.gnu.org/licenses/gpl.txt

import sys
import os
import shutil
import numpy as np
from Priithon import Mrc


def main():
    """Collect input filename, create output file, and filter each slice"""

    input_path = sys.argv[1]
    print "arg0: " + input_path
    if not os.path.isabs(input_path):
        print "You must give a full path to the input file"
        sys.exit()
    else:
        # Fourier Filter Stripes: copy to new file (data will be overwritten)
        output_path = addTag(input_path, "FFS")
        shutil.copy2(input_path, output_path)
        # NB. Mrc is a special numpy ndarray with extra metadata attached
        fMrc = Mrc.bindFile(output_path, writable=1)
        # make a view of the data ndarray that is a flat list of XY slices
        nplanes = reduce(lambda x, y: x * y, fMrc.shape[:-2])
        ny, nx = fMrc.shape[-2:]
        xy_slices = fMrc.reshape((nplanes, ny, nx))
        # filter out stripes from each slice of the whole stack (in-place)
        for p in range(nplanes):
            xy_slices[p,:,:] = filter_stripes(xy_slices[p,:,:])


def addTag(file_path, tag):
    """Create new file path including tag before .extension"""
    path, ext = os.path.splitext(file_path)
    return path + "_" + tag + ext


def filter_stripes(yx_slice, horizontal=True):
    """Filter out (remove) horizontal or vertical stripes in 2D image data.

    Parameters
    ----------
    yx_slice : numpy.ndarray
        An 2D image data slice, dimension order Y then X
        
    horizontal : boolean
        Stripes are horizontal? (else vertical)

    Returns
    ------
    numpy.ndarray
        The filtered 2D image data slice

    """
    img_f = np.fft.fftshift(np.fft.fft2(yx_slice.copy()))
    if horizontal:
        xc = img_f.shape[1] / 2  # x center in freq space (zero x freq / offset)
        img_f[:, xc:xc+1] = 1.0  # suppress vertical stripe in *freq* space
    else:
        yc = img_f.shape[0] / 2  # y center in freq space (zero y freq / offset)
        img_f[yc:yc+1, :] = 1.0  # suppress horizontal stripe in *freq* space
    img_filtered = abs(np.fft.ifft2(np.fft.ifftshift(img_f)))
    residual = yx_slice - img_filtered
    # add offset back to filtered image to prevent negative intensities
    return img_filtered + residual.mean()


if __name__ == '__main__':
    main()
