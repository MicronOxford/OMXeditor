==============================================================================
Introduction
==============================================================================

This file is a short guide to using the OMX image-editing program. This
program should be used to preview, crop, and align data that has been collected
on OMX, prior to running more in-depth postprocessing techniques.


==============================================================================
Basic use
==============================================================================

To open a file, click on the leftmost icon in the upper-left corner, which looks
like an opening folder. Each file you open is added in a new tab, allowing you
to switch back and forth freely.

The program shows each file in three different views: an XY view, an XZ view
underneath, and a YZ view on the right. Each also includes a large grey 
crosshairs (which may be dragged about), which modifies which slice the XZ and
YZ views show. On the main panel are histograms for each wavelength. By clicking
the button next to a histogram, you can toggle display of the corresponding
wavelength.

The main panel also has cropping and alignment controls, which are covered in
more detail further down.

Once you have cropped or aligned data, you can save the resulting file using
either the Save button or Save As button, in the upper-left of the main panel.
You can also apply the cropping and alignment to other files using the Batch
Process button (see below).

Align and crop parameters can be saved and loaded using the "Export parameters"
and "Load parameters" buttons. The resulting parameter file can also be used
by the OMX Processor program's "Align and crop" mode.


==============================================================================
Cropping
==============================================================================

Cropping can be useful to limit the amount of data that later programs must
manipulate. This can greatly speed up postprocessing. You can crop with either
the mouse or the keyboard. To change the cropbox with the mouse, move the 
mouse to the corners of one of the displays until the mouse icon changes to a 
diagonal dragging one, then click and drag to move that corner of the box. To
crop with the keyboard, simply type in the crop min/max parameters in the 
"Crop controls" section. 

Cropping will be applied to your data if you save it, causing pixels outside of 
the cropbox to be truncated off. Until you do save, those pixels are not lost. 
You can preview what the crop will look like by clicking on the "Preview crop"
button.


==============================================================================
Alignment
==============================================================================

Because of minor variations in the positions of the different cameras and 
mirrors in OMX, the four cameras are all slightly offset with respect to 
each other. This program provides an automatic Simplex-based alignment system 
to modify image files so that all wavelengths are properly aligned. 

Follow the below general steps to align your data:

1. Image a bead slide that uses the same wavelengths as your sample.
2. Open the bead slide file in the editor.
3. Bring the different wavelengths of the beads into rough alignment using the 
mouse. You can left-click on the 2D view to translate one wavelength with 
respect to the others, and right-click (or control-click) to rotate. You can
change which wavelength(s) are modified by the mouse by clicking on the 
"Control with mouse" checkboxes on the right. Manipulate the image until the 
beads are more or less aligned. This step is necessary because the Simplex
alignment method does not work if it does not have a good starting point.
4. If you have noisy data, then you may want to adjust the histograms before
aligning. Cleaner images will provide better alignments. 
5. Click on the "Auto-align" button. This will run the Simplex process, which
may take a long time. Once the status text says "Completed all alignments", 
alignment is complete. The various "Align parameters" text boxes now have the
transformation parameters needed to align each wavelength with the others. 

At this point you may save the file (which will apply the alignment 
transformations), or you may apply the transformations to other files using 
the Batch Process button. You can also save just the alignment and cropping
parameters using the "Export parameters" button, so that they can later be 
loaded for a different file using the "Load parameters" button.



==============================================================================
Batch processing
==============================================================================

Batch processing allows you to apply a single set of cropping or alignment
parameters to a large number of files. The "Batch process" button, to the 
right of the "Auto-align" button, provides access to this mode. From here you 
can choose to apply either cropping or alignment, or both, to the files you 
want to modify. 

Cropping will truncate all of the input files to the same XY size and number
of slices. It requires that all files have the same XY size. In the event
that the file being processed has a different number of Z slices than the
file you used to construct the cropbox, the program will center the cropbox,
such that the distance from the top of the Z stack to the top of the
cropbox is proportionate to the distance in the original file. 

For example, if the original file has 20 slices and is cropped to 10, with the 
crop box top at 15 (thus the upper and lower 5 slices are excluded), and the
new file has 40 slices, then the crop box in the new file will have a top at
25 (with the upper and lower 15 slices excluded). 

Alignment will simply apply the alignment transformations acquired in the 
original file to the new file. All files must have the same number of
wavelengths.
