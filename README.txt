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
