==============================================================================
Introduction
==============================================================================

This file is a short guide to using the OMX image-editing program. This
program should be used to preview, crop, and align data that has been collected
on OMX, prior to running more in-depth postprocessing techniques.


==============================================================================
Basic use
==============================================================================

You can open, save, and save-as files via the File menu. Each open file 
appears as a separate tab in the main window. By default, when you open a file
you will be shown the XY, XZ, and YZ views (only the XY view for 2D files). 


You can see other views (e.g. timewise views) by choosing the "Show view 
controls" option from the File menu. Here you can also project views across
axes -- for example, show an XY view taking a max-intensity projection across
Z or time. 

Each view includes a large grey crosshairs that marks a specific pixel. This
pixel is the one that slices are made through. For example, in a 512x512x40
image the crosshairs start out at (256, 256, 20) -- which means that the XY 
view is showing you Z slice 20, the XZ view is showing you Y slice 256, and
the YZ view is showing you X slice 256. The crosshairs can be dragged with
the mouse, or set directly from the view controls window. 

Moving to the main window now, in the upper-left corner are cropping controls,
allowing you to exclude pixels from the file. Most of the rest of the window
is taken up by per-wavelength controls -- a histogram for controlling the 
brightness of pixels, and the alignment transformation that causes this 
wavelength to align with the others. The "Swap" button allows you to exchange
alignment parameters across wavelengths. The "Control with mouse" checkbox
indicates which wavelengths are transformed when you click and drag in the 
image views. Left-click and drag will translate a wavelength, while right-click
and drag will rotate it. These allow you to manually align your wavelengths
in preparation for auto-alignment.

By clicking on the "Auto-align" button, the program will use the Simplex
method to find a set of transformations that best align your wavelengths
together. For this to work properly, the same information needs to be 
present in both wavelengths (for example, by using a bead slide). One
wavelength is held fixed (the one marked with the "Use as auto-alignment
reference" radio button), and the others are transformed to match it as closely
as possible. While alignment is running, a graph will be displayed showing
how closely the different wavelengths match after each iteration of the 
process. 

The result of alignment is a set of transformation parameters, which you can
then export for use on other files by clicking on the "Export parameters"
button. You can also load a parameters file by clicking on the "Load 
parameters" button. The "Batch process" button allows you to apply alignment
and/or cropping to large numbers of files automatically.

When batch processing, cropping will truncate all of the input files to the
same XY size and number of slices. All files must have the same initial XY
size. In the event that the file being processed has a different number of Z
slices than the file you used to construct the cropbox, the program will 
center the cropbox, such that the distance from the top of the Z stack to the 
top of the cropbox is proportionate to the distance in the original file. 

For example, if the original file has 20 slices and is cropped to 10, with the 
crop box top at 15 (thus the upper and lower 5 slices are excluded), and the
new file has 40 slices, then the crop box in the new file will have a top at
25 (with the upper and lower 15 slices excluded). 

Alignment will simply apply the alignment transformations acquired in the 
original file to the new file. All files must have the same number of
wavelengths.
