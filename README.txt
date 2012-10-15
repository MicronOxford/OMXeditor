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


Modifications made by graemeball@googlemail.com (Micron Oxford)                 
===============================================================                 
                                                                                
2012                                                                            
----                                                                            
                                                                                
Bufixes                                                                         
~~~~~~~                                                                         
* fixed realign.py for correct application of Z-alignment correction            
                                                                                
Customization                                                                   
~~~~~~~~~~~~~                                                                   
* some renaming & re-tooling:-                                                  
** removed "Preview crop" & "Swap" buttons from cropControlPanel.py             
** "wavelengths" renamed to channels, and "Crop controls" to "Crop parameters"  
* changed save convention from new folder/ to new file with three-letter code:- 
** _EAL = Editor ALigned                                                        
** _ECR = Editor CRopped                                                        
** _EPJ = Editor ProJected (SI raw => "widefield" by averaging phases/angles)   
** _ERS = Editor ReSized                                                        
** _ERO = Editor ReOrdered                                                      
** _EMG = Editor MerGed (i.e. from previously split channels)                   
* splitting time-points/channels saves files in a new folder (FileRoot_ESP):-   
** FileRoot_C{c}.ext where c=channel number                                     
** FileRoot_T{t}.ext where t=timepoint                                          
                                                                                
Feature additions                                                               
~~~~~~~~~~~~~~~~~                                                               
* projection SI raw -> widefield                                                
* resizing/resampling                                                           
* channel re-ordering                                                           
* channel merging                                                               
* channel splitting                                                             
                                                                                
TODO                                                                            
----                                                                            
* test: alignment correctness and perfomance                                    
** do alignment parameters apply across different image sizes?                  
** effect of edges, and max alignment search window?                            
** reproducibility / accuracy?                                                  
* test: metadata population and copying                                         
** is all metadata updated upon channel swap?                                   
* test: scalability                                                             
** size at which speed and/or memory become limiting?                           
* bugfix: YZ view panel controls / projection not working properly
* refactor: move non-interactive editing procedures to mrcEditor.py where possible  
* refactor: remove all wx GUI stuff from datadoc                                
* refactor: merge datadoc and MRC, remove other unnecessary Priithon            
* refactor: add docstrings and try to improve adherence to conventions          
* new feature:non-interactive editing operations to be run headless w/o GUI     
* new feature: split/merge and proj/resize features (TODO: add to mainWindow)   
* new feature: average phases+angles for pseudo-widefield (+resizing)           
* new feature: add information about operations carried out to MRC title fields 
* optimization: auto-alignment speed                                            
** multithread => multiprocess?                                                 
** FFT pre-align? (and/or search constraints?)                                  
** downsampling? (resampling? bit-depth?)
