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

Bufixes
~~~~~~~
* fixed realign.py for correct application of Z-alignment correction
* fixed bug in SimplexAlign.getOffset() for non-square images

Customization
~~~~~~~~~~~~~
* some renaming & re-tooling:-
** removed "Preview crop" & "Swap" buttons from cropControlPanel.py
** "wavelengths" renamed to channels, and "Crop controls" to "Crop parameters"
* changed save convention from new folder/ to new file with three-letter code:-
** _EAL = Editor ALigned
* splitting time-points/channels saves files in a new folder (FileRoot_ESP):-
** FileRoot_C{c}.dv where c=channel number
** FileRoot_T{t}.dv where t=timepoint
* refactored modules, and added editor.py for headless / CLI usage

TODO
----
* refactor: split combined editing function dialogs into individual dialogs & finish
* refactor: add docstrings and try to improve adherence to conventions
* document: project history, licensing, READMEs
* document: tidy user guide
* test / document: test cross-platform, tidy git branches & tag stable versions
* bugfix: YZ view panel controls / projection not working properly
* test: unit tests for non-interactive code (auto-alignment etc.)
* refactor: merge datadoc / MRC, remove Priithon dependency
* enhancement: auto-alignment speed (parameters, algorithm, multiprocess)
* enhancement: pre-align with downsampling and/or FFT
* test: do alignment parameters apply across different image sizes?
* test: effect of edges, and max alignment search window?
* test: test data & evaluate vs. competing alignment algorithms
* test: metadata population and copying
* test: size at which speed and/or memory become limiting?
* enhancement: average phases+angles for pseudo-widefield (+resizing)
* enhancement: add information about operations carried out to MRC title fields
* document: API docs
