"access to double and single prec SWIG wrapped FFTW3 module"

__author__  = "Sebastian Haase <haase@msg.ucsf.edu> \n Lin Shao"
__license__ = "BSD license - see LICENSE file"

import fftw3 as _fftw3
import numpy as _N

_splans = {}
_dplans = {}

_fftw3.fftwf_init_threads()
_fftw3.fftw_init_threads()

def rfft(a, af=None, inplace=0, _measure = _fftw3.FFTW_ESTIMATE):
    '''
    _measure = _fftw3.FFTW_ESTIMATE will not overwrite the input array
    '''

    if a.dtype.name.find('float') < 0:
        if a.dtype.name.find('complex') < 0:
            a = _N.asarray(a, _N.float32)
            print 'Warning: a temporary copy of inarray is made to satisfy type check'
        else:
            raise TypeError, 'a cannot be complex'

    if inplace:
        ## the real shape is supposed to be ...
        shape = a.shape[:-1]+(a.shape[-1]-2,)
    else:
        shape = a.shape

    ashape = _N.array(shape, dtype=_N.int32)
    s2 = shape[:-1]+(shape[-1]//2+1,)  # shape of the complex output array

    if a.dtype == _N.float32:
        key = ("sr%d"%inplace, shape)

        ## if the kind of plan doesn't exist, make one
        try:
            p = _splans[ key ]
        except:
            if inplace:
                af = _N.ndarray(buffer=a, shape=s2, dtype=_N.complex64)
            else:
                if af is None:
                    af = _N.empty(shape=s2, dtype=_N.complex64)
                elif af.dtype != _N.complex64 or af.shape != s2 or not af.flags.carray:
                    raise ValueError, 'outarray has to be of complex64 and the right shape'
            p = _fftw3.fftwf_plan_dft_r2c(len(shape), ashape, a, af, _measure)

            if p == 0:
                raise RuntimeError, "could not create plan"
            _splans[ key ] = p
            
        if inplace:  ## ignore the passed-in af
            af = _N.ndarray(buffer=a, shape=s2, dtype=_N.complex64)
        elif af is None:
            af = _N.empty(shape=s2, dtype=_N.complex64)
        elif af.dtype != _N.complex64 or af.shape != s2 or not af.flags.carray:
            raise ValueError, 'outarray must be of complex64 and the right shape'

        _fftw3.fftwf_execute_dft_r2c(p, a, af)
        return af

    elif a.dtype == _N.float64:
        key = ("dr%d"%inplace, shape)

        try:
            p = _dplans[ key ]
        except:
            if inplace:
                af = _N.ndarray(buffer=a, shape=s2, dtype=_N.complex128)
            else:
                if af is None:
                    af = _N.empty(shape=s2, dtype=_N.complex128)
                elif af.dtype != _N.complex128 or af.shape != s2 or not af.flags.carray:
                    raise ValueError, 'outarray must be of complex64 and the right shape'
            p = _fftw3.fftw_plan_dft_r2c(len(shape), ashape, a, af, _measure)

            if p == 0:
                raise RuntimeError, "could not create plan"
            _dplans[ key ] = p

        if inplace:  ## ignore the passed-in af
            af = _N.ndarray(buffer=a, shape=s2,dtype=_N.complex128)
        elif af is None:
            af = _N.empty(shape=s2, dtype=_N.complex128)
        elif af.dtype != _N.complex128 or af.shape != s2 or not af.flags.carray:
            raise ValueError, 'outarray has to be of complex128 and the right shape'

        _fftw3.fftw_execute_dft_r2c(p, a, af)
        return af

    else:
        raise TypeError, "(c)float32 and (c)float64 must be used consistently (%s %s)"%\
              ((a is None and "a is None" or "a.dtype=%s"%a.dtype),
               (af is None and "af is None" or "af.dtype=%s"%af.dtype))

def irfft(af, a=None, inplace=0, _measure = _fftw3.FFTW_ESTIMATE):
    """
    In FFTW3, inverse DFT doesn't overwrite the input array like FFTW2.
    Correct me if I'm wrong.
    """

    if af.dtype.name.find('complex') < 0:
        raise TypeError, 'inarray must be complex(32 or 64)'
    
    shape = af.shape[:-1] + ((af.shape[-1]-1)*2,)

    ashape = _N.array(shape, dtype=_N.int32)
    s2 = af.shape[:-1] + (af.shape[-1]*2,)  ## the shape of the output if in-place FFT

    if af.dtype == _N.complex64:
        key = ("sir%d"%inplace, shape)

        try:
            p = _splans[ key ]
        except:
            
            if inplace:
                a = _N.ndarray(buffer=af, shape=s2, dtype=_N.float32)
            else:
                if a is None:
                    a = _N.empty(shape=shape, dtype=_N.float32)
                elif a.dtype != _N.float32 or a.shape != shape or not a.flags.carray:
                    raise ValueError, 'outarray must be of float32 and the right shape'
            p = _fftw3.fftwf_plan_dft_c2r(len(shape), ashape, af, a, _measure)
            if p == 0:
                raise RuntimeError, "could not create plan"
            _splans[ key ] = p

        if inplace:  ## ignore the passed-in a
            a = _N.ndarray(buffer=af, shape=s2, dtype=_N.float32)
        elif a is None:
            a = _N.empty(shape=shape, dtype=_N.float32)
        elif a.dtype != _N.float32 or a.shape != shape or not a.flags.carray:
            raise ValueError, 'outarray must be of float32 and the right shape'

        _fftw3.fftwf_execute_dft_c2r(p, af, a)
        return a
            
    elif af.dtype == _N.complex128:
        key = ("dir%d"%inplace, shape )

        try:
            p = _dplans[ key ]
        except:
            
            if inplace:
                a = _N.ndarray(buffer=af, shape=s2, dtype=_N.float64)
            else:
                if a is None:
                    a = _N.empty(shape=shape, dtype=_N.float64)
                elif a.dtype != _N.float64 or a.shape != shape or not a.flags.carray:
                    raise ValueError, 'a has to be of float64 and the right shape'
            p = _fftw3.fftw_plan_dft_c2r(len(shape), ashape, af, a, _measure)
            if p == 0:
                raise RuntimeError, "could not create plan"
            _dplans[ key ] = p

        if inplace:  ## ignore the passed-in a
            a = _N.ndarray(buffer=af, shape=s2, dtype=_N.float64)
        elif a is None:
            a = _N.empty(shape=shape, dtype=_N.float64)
        elif a.dtype != _N.float64 or a.shape != shape or not a.flags.carray:
            raise ValueError, 'a has to be of float64 and the right shape'

        _fftw3.fftw_execute_dft_c2r(p, af, a)
        return a
            
    else:
        raise TypeError, "(c)float32 and (c)float64 must be used consistently (%s %s)"%\
              ((a is None and "a is None" or "a.dtype=%s"%a.dtype),
               (af is None and "af is None" or "af.dtype=%s"%af.dtype))


def destroy_plans():
    for k in _splans.keys():
        _fftw3.fftwf_destroy_plan( _splans[ k ] )
        del _splans[ k ]

    for k in _dplans.keys():
        _fftw3.fftw_destroy_plan( _dplans[ k ] )
        del _dplans[ k ]


def fft(a, af=None, inplace=0, _measure = _fftw3.FFTW_ESTIMATE):

    if a.dtype.name.find('complex') < 0:
        raise TypeError, 'inarray must be complex(32 or 64)'

    shape = a.shape
    ashape = _N.array(shape, dtype=_N.int32)
    
    if a.dtype == _N.complex64:
        key = ("s%d"%inplace, shape )

        try:
            p = _splans[ key ]
        except:
            if inplace:
                af = _N.ndarray(buffer=a, shape=shape, dtype=_N.complex64)
            else:
                if af is None:
                    af = _N.empty(shape=shape, dtype=_N.complex64)
                elif af.dtype != _N.complex64 or af.shape != shape or not af.flags.carray:
                    raise ValueError, 'outarray must be of complex64 and the right shape'
            p = _fftw3.fftwf_plan_dft(len(shape), ashape, a, af, _fftw3.FFTW_FORWARD, _measure)

            if p == 0:
                raise RuntimeError, "could not create plan"
            _splans[ key ] = p

        if inplace:  ## ignore the passed-in af
            af = _N.ndarray(buffer=a, shape=shape, dtype=_N.complex64)
        elif af is None:
            af = _N.empty(shape=shape, dtype=_N.complex64)
        elif af.dtype != _N.complex64 or af.shape != shape or not af.flags.carray:
            raise ValueError, 'outarray must be of complex64 and the right shape'

        _fftw3.fftwf_execute_dft(p, a, af)
        return af

    elif a.dtype == _N.complex128:
        key = ("d%d"%inplace, shape )

        try:
            p = _dplans[ key ]
        except:
            if inplace:
                af = _N.ndarray(buffer=a, shape=shape, dtype=_N.complex128)
            else:
                if af is None:
                    af = _N.empty(shape=shape, dtype=_N.complex128)
                elif af.dtype != _N.complex128 or af.shape != shape or not af.flags.carray:
                    raise ValueError, 'outarray must be of complex128 and the right shape'
            p = _fftw3.fftw_plan_dft(len(shape), ashape, a, af, _fftw3.FFTW_FORWARD, _measure)

            if p == 0:
                raise RuntimeError, "could not create plan"
            _dplans[ key ] = p

        if inplace:  ## ignore the passed-in af
            af = _N.ndarray(buffer=a, shape=shape, dtype=_N.complex128)
        elif af is None:
            af = _N.empty(shape=shape, dtype=_N.complex128)
        elif af.dtype != _N.complex128 or af.shape != shape or not af.flags.carray:
            raise ValueError, 'outarray must be of complex128 and the right shape'

        _fftw3.fftw_execute_dft(p, a, af)
        return af

    else:
        raise TypeError, "complex64 and complex128 must be used consistently (%s %s)"%\
              ((a is None and "a is None" or "a.dtype=%s"%a.dtype),
               (af is None and "af is None" or "af.dtype=%s"%af.dtype))

def ifft(af, a=None, inplace=0):

    if af.dtype.name.find('complex') < 0:
        raise TypeError, 'inarray must be complex(32 or 64)'

    shape = af.shape
    ashape = _N.array(shape, dtype=_N.int32)

    if af.dtype == _N.complex64:
        key = ("si%d"%inplace, shape )

        try:
            p = _splans[ key ]
        except:
            if inplace:
                a = _N.ndarray(buffer=af, shape=shape, dtype=_N.complex64)
            else:
                if a is None:
                    a = _N.empty(shape=shape, dtype=_N.complex64)
                elif a.dtype != _N.complex64 or a.shape != shape or not a.flags.carray:
                    raise ValueError, 'outarray must be of complex64 and the right shape'
            p = _fftw3.fftwf_plan_dft(len(shape), ashape, af, a, _fftw3.FFTW_BACKWARD, _measure)

            if p == 0:
                raise RuntimeError, "could not create plan"
            _splans[ key ] = p

        if inplace:  ## ignore the passed-in a
            a = _N.ndarray(buffer=af, shape=shape, dtype=_N.complex64)
        elif a is None:
            a = _N.empty(shape=shape, dtype=_N.complex64)
        elif a.dtype != _N.complex64 or a.shape != shape or not a.flags.carray:
            raise ValueError, 'outarray must be of complex64 and the right shape'

        _fftw3.fftwf_execute_dft(p, af, a)
        return a


    elif af.dtype == _N.complex128:
        key = ("di%d"%inplace, shape )

        try:
            p = _dplans[ key ]
        except:
            if inplace:
                a = _N.ndarray(buffer=af, shape=shape, dtype=_N.complex128)
            else:
                if a is None:
                    a = _N.empty(shape=shape, dtype=_N.complex128)
                elif a.dtype != _N.complex128 or a.shape != shape or not a.flags.carray:
                    raise ValueError, 'outarray must be of complex64 and the right shape'
            p = _fftw3.fftw_plan_dft(len(shape), ashape, af, a, _fftw3.FFTW_BACKWARD, _measure)

            if p == 0:
                raise RuntimeError, "could not create plan"
            _dplans[ key ] = p

        if inplace:  ## ignore the passed-in a
            a = _N.ndarray(buffer=af, shape=shape, dtype=_N.complex128)
        elif a is None:
            a = _N.empty(shape=shape, dtype=_N.complex128)
        elif a.dtype != _N.complex128 or a.shape != shape or not a.flags.carray:
            raise ValueError, 'outarray must be of complex128 and the right shape'

        _fftw3.fftw_execute_dft(p, af, a)
        return a

    else:
        raise TypeError, "complex64 and complex128 must be used consistently (%s %s)"%\
              ((a is None and "a is None" or "a.dtype=%s"%a.dtype),
               (af is None and "af is None" or "af.dtype=%s"%af.dtype))

