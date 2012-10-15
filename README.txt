Editor 2.2.0 comments by Chris Weisiger, received Sept2012
==========================================================

This directory contains the imaginatively-named "OMX Editor" program, which
provides the following features:

 * Multi-channel image visualization
 * Automatic wavelength alignment
 * Image cropping

The latter two can also be automated using its batch processing mode, or by 
using the OMX Processor program -- the Editor can export align/crop parameter
files that the Processor can import. 

The Editor includes its own fairly-minimal copy of Priithon, largely because
it needs to be standalone and I couldn't rely on my users having Priithon 
installed. Currently it depends on only two things in Priithon: the Mrc and 
histogram modules. It should be possible to replace the latter with new code
that accomplishes the same thing, and I've been wanting to write my own MRC
loader/unloader for awhile now, but I can't really justify the effort 
expenditure. 

There's precisely one feature that depends on Priism (not Priithon): the 
stereo-pair generation, accessible via the File menu. If Priism isn't 
present in the build, then that option won't be shown -- the program checks for
the presence of the PriismX directory on startup. Most builds won't include
Priism because that limits our ability to distribute this program; Priism
contains licensed code that we can't give out.

The Editor began life as "auidemo.py", but has been extensively modified
since then. Very little of the original code remains.


-------------------------------------------------------------------------------


Modifications made by graemeball@googlemail.com
===============================================

2012
~~~~
* changed save convention from new folder/ to new file with three-letter code
* fixed realign.py for correct application of Z-alignment correction
* removed "Preview crop" & "Swap" buttons from cropControlPanel.py 
* some renaming & re-tooling:-
** "wavelengths" ranmed to channels, and "Crop controls" to "Crop 
** Dice Dialog => Edit Dims dialog 
** new SItoWF dialog


TODO
----
* test: whether alignment parameters apply across different image sizes
* test: effect of edges, and max alignment search window
* new feature: average phases and angles for pseudo-widefield (+resize 2x) _EWF
* alter feature: "Swap" buttons confusing - create a better interface for 
    choosing dimension order of image versus parameter file (see below)
* alter feature: "Dice file" - "Edit Dims" with more options would be 
    more useful - i.e. re-order, split, & merge channels: _ERE, _ESP_CHX, _EMG
* refactor - remove obsolete diceDialog.py
* refactor / new feature: ensure all operations can be run headless w/o GUI
** refactor datadoc to remove all wx GUI stuff
* refactor: datadoc and MRC, remove other unnecessary Priithon

Edit Dims design
~~~~~~~~~~~~~~~~
* separate Re-order, Split and Merge operations to keep design simple
* Re-order: old to new dimension mapping (old fixed, specify new)
* Split: boxes for Channel, Angle, Time ranges
* Join: up to 4 files in the order chosen (one or more channels/file)
