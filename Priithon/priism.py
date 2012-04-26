# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.
# This file is compatible with both classic and new-style classes.

import _priism

def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
    if (name == "this"):
        if isinstance(value, class_type):
            self.__dict__[name] = value.this
            if hasattr(value,"thisown"): self.__dict__["thisown"] = value.thisown
            del value.thisown
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    if (not static) or hasattr(self,name) or (name == "thisown"):
        self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)

def _swig_setattr(self,class_type,name,value):
    return _swig_setattr_nondynamic(self,class_type,name,value,0)

def _swig_getattr(self,class_type,name):
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError,name

import types
try:
    _object = types.ObjectType
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0
del types


class IW_MRC_HEADER(_object):
    """Proxy of C++ IW_MRC_HEADER class"""
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, IW_MRC_HEADER, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, IW_MRC_HEADER, name)
    def __repr__(self):
        return "<%s.%s; proxy of C++ IW_MRC_HEADER instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    __swig_setmethods__["nx"] = _priism.IW_MRC_HEADER_nx_set
    __swig_getmethods__["nx"] = _priism.IW_MRC_HEADER_nx_get
    if _newclass:nx = property(_priism.IW_MRC_HEADER_nx_get, _priism.IW_MRC_HEADER_nx_set)
    __swig_setmethods__["ny"] = _priism.IW_MRC_HEADER_ny_set
    __swig_getmethods__["ny"] = _priism.IW_MRC_HEADER_ny_get
    if _newclass:ny = property(_priism.IW_MRC_HEADER_ny_get, _priism.IW_MRC_HEADER_ny_set)
    __swig_setmethods__["nz"] = _priism.IW_MRC_HEADER_nz_set
    __swig_getmethods__["nz"] = _priism.IW_MRC_HEADER_nz_get
    if _newclass:nz = property(_priism.IW_MRC_HEADER_nz_get, _priism.IW_MRC_HEADER_nz_set)
    __swig_setmethods__["mode"] = _priism.IW_MRC_HEADER_mode_set
    __swig_getmethods__["mode"] = _priism.IW_MRC_HEADER_mode_get
    if _newclass:mode = property(_priism.IW_MRC_HEADER_mode_get, _priism.IW_MRC_HEADER_mode_set)
    __swig_setmethods__["nxst"] = _priism.IW_MRC_HEADER_nxst_set
    __swig_getmethods__["nxst"] = _priism.IW_MRC_HEADER_nxst_get
    if _newclass:nxst = property(_priism.IW_MRC_HEADER_nxst_get, _priism.IW_MRC_HEADER_nxst_set)
    __swig_setmethods__["nyst"] = _priism.IW_MRC_HEADER_nyst_set
    __swig_getmethods__["nyst"] = _priism.IW_MRC_HEADER_nyst_get
    if _newclass:nyst = property(_priism.IW_MRC_HEADER_nyst_get, _priism.IW_MRC_HEADER_nyst_set)
    __swig_setmethods__["nzst"] = _priism.IW_MRC_HEADER_nzst_set
    __swig_getmethods__["nzst"] = _priism.IW_MRC_HEADER_nzst_get
    if _newclass:nzst = property(_priism.IW_MRC_HEADER_nzst_get, _priism.IW_MRC_HEADER_nzst_set)
    __swig_setmethods__["mx"] = _priism.IW_MRC_HEADER_mx_set
    __swig_getmethods__["mx"] = _priism.IW_MRC_HEADER_mx_get
    if _newclass:mx = property(_priism.IW_MRC_HEADER_mx_get, _priism.IW_MRC_HEADER_mx_set)
    __swig_setmethods__["my"] = _priism.IW_MRC_HEADER_my_set
    __swig_getmethods__["my"] = _priism.IW_MRC_HEADER_my_get
    if _newclass:my = property(_priism.IW_MRC_HEADER_my_get, _priism.IW_MRC_HEADER_my_set)
    __swig_setmethods__["mz"] = _priism.IW_MRC_HEADER_mz_set
    __swig_getmethods__["mz"] = _priism.IW_MRC_HEADER_mz_get
    if _newclass:mz = property(_priism.IW_MRC_HEADER_mz_get, _priism.IW_MRC_HEADER_mz_set)
    __swig_setmethods__["xlen"] = _priism.IW_MRC_HEADER_xlen_set
    __swig_getmethods__["xlen"] = _priism.IW_MRC_HEADER_xlen_get
    if _newclass:xlen = property(_priism.IW_MRC_HEADER_xlen_get, _priism.IW_MRC_HEADER_xlen_set)
    __swig_setmethods__["ylen"] = _priism.IW_MRC_HEADER_ylen_set
    __swig_getmethods__["ylen"] = _priism.IW_MRC_HEADER_ylen_get
    if _newclass:ylen = property(_priism.IW_MRC_HEADER_ylen_get, _priism.IW_MRC_HEADER_ylen_set)
    __swig_setmethods__["zlen"] = _priism.IW_MRC_HEADER_zlen_set
    __swig_getmethods__["zlen"] = _priism.IW_MRC_HEADER_zlen_get
    if _newclass:zlen = property(_priism.IW_MRC_HEADER_zlen_get, _priism.IW_MRC_HEADER_zlen_set)
    __swig_setmethods__["alpha"] = _priism.IW_MRC_HEADER_alpha_set
    __swig_getmethods__["alpha"] = _priism.IW_MRC_HEADER_alpha_get
    if _newclass:alpha = property(_priism.IW_MRC_HEADER_alpha_get, _priism.IW_MRC_HEADER_alpha_set)
    __swig_setmethods__["beta"] = _priism.IW_MRC_HEADER_beta_set
    __swig_getmethods__["beta"] = _priism.IW_MRC_HEADER_beta_get
    if _newclass:beta = property(_priism.IW_MRC_HEADER_beta_get, _priism.IW_MRC_HEADER_beta_set)
    __swig_setmethods__["gamma"] = _priism.IW_MRC_HEADER_gamma_set
    __swig_getmethods__["gamma"] = _priism.IW_MRC_HEADER_gamma_get
    if _newclass:gamma = property(_priism.IW_MRC_HEADER_gamma_get, _priism.IW_MRC_HEADER_gamma_set)
    __swig_setmethods__["mapc"] = _priism.IW_MRC_HEADER_mapc_set
    __swig_getmethods__["mapc"] = _priism.IW_MRC_HEADER_mapc_get
    if _newclass:mapc = property(_priism.IW_MRC_HEADER_mapc_get, _priism.IW_MRC_HEADER_mapc_set)
    __swig_setmethods__["mapr"] = _priism.IW_MRC_HEADER_mapr_set
    __swig_getmethods__["mapr"] = _priism.IW_MRC_HEADER_mapr_get
    if _newclass:mapr = property(_priism.IW_MRC_HEADER_mapr_get, _priism.IW_MRC_HEADER_mapr_set)
    __swig_setmethods__["maps"] = _priism.IW_MRC_HEADER_maps_set
    __swig_getmethods__["maps"] = _priism.IW_MRC_HEADER_maps_get
    if _newclass:maps = property(_priism.IW_MRC_HEADER_maps_get, _priism.IW_MRC_HEADER_maps_set)
    __swig_setmethods__["amin"] = _priism.IW_MRC_HEADER_amin_set
    __swig_getmethods__["amin"] = _priism.IW_MRC_HEADER_amin_get
    if _newclass:amin = property(_priism.IW_MRC_HEADER_amin_get, _priism.IW_MRC_HEADER_amin_set)
    __swig_setmethods__["amax"] = _priism.IW_MRC_HEADER_amax_set
    __swig_getmethods__["amax"] = _priism.IW_MRC_HEADER_amax_get
    if _newclass:amax = property(_priism.IW_MRC_HEADER_amax_get, _priism.IW_MRC_HEADER_amax_set)
    __swig_setmethods__["amean"] = _priism.IW_MRC_HEADER_amean_set
    __swig_getmethods__["amean"] = _priism.IW_MRC_HEADER_amean_get
    if _newclass:amean = property(_priism.IW_MRC_HEADER_amean_get, _priism.IW_MRC_HEADER_amean_set)
    __swig_setmethods__["ispg"] = _priism.IW_MRC_HEADER_ispg_set
    __swig_getmethods__["ispg"] = _priism.IW_MRC_HEADER_ispg_get
    if _newclass:ispg = property(_priism.IW_MRC_HEADER_ispg_get, _priism.IW_MRC_HEADER_ispg_set)
    __swig_setmethods__["inbsym"] = _priism.IW_MRC_HEADER_inbsym_set
    __swig_getmethods__["inbsym"] = _priism.IW_MRC_HEADER_inbsym_get
    if _newclass:inbsym = property(_priism.IW_MRC_HEADER_inbsym_get, _priism.IW_MRC_HEADER_inbsym_set)
    __swig_setmethods__["nDVID"] = _priism.IW_MRC_HEADER_nDVID_set
    __swig_getmethods__["nDVID"] = _priism.IW_MRC_HEADER_nDVID_get
    if _newclass:nDVID = property(_priism.IW_MRC_HEADER_nDVID_get, _priism.IW_MRC_HEADER_nDVID_set)
    __swig_setmethods__["nblank"] = _priism.IW_MRC_HEADER_nblank_set
    __swig_getmethods__["nblank"] = _priism.IW_MRC_HEADER_nblank_get
    if _newclass:nblank = property(_priism.IW_MRC_HEADER_nblank_get, _priism.IW_MRC_HEADER_nblank_set)
    __swig_setmethods__["ntst"] = _priism.IW_MRC_HEADER_ntst_set
    __swig_getmethods__["ntst"] = _priism.IW_MRC_HEADER_ntst_get
    if _newclass:ntst = property(_priism.IW_MRC_HEADER_ntst_get, _priism.IW_MRC_HEADER_ntst_set)
    __swig_setmethods__["ibyte"] = _priism.IW_MRC_HEADER_ibyte_set
    __swig_getmethods__["ibyte"] = _priism.IW_MRC_HEADER_ibyte_get
    if _newclass:ibyte = property(_priism.IW_MRC_HEADER_ibyte_get, _priism.IW_MRC_HEADER_ibyte_set)
    __swig_setmethods__["nint"] = _priism.IW_MRC_HEADER_nint_set
    __swig_getmethods__["nint"] = _priism.IW_MRC_HEADER_nint_get
    if _newclass:nint = property(_priism.IW_MRC_HEADER_nint_get, _priism.IW_MRC_HEADER_nint_set)
    __swig_setmethods__["nreal"] = _priism.IW_MRC_HEADER_nreal_set
    __swig_getmethods__["nreal"] = _priism.IW_MRC_HEADER_nreal_get
    if _newclass:nreal = property(_priism.IW_MRC_HEADER_nreal_get, _priism.IW_MRC_HEADER_nreal_set)
    __swig_setmethods__["nres"] = _priism.IW_MRC_HEADER_nres_set
    __swig_getmethods__["nres"] = _priism.IW_MRC_HEADER_nres_get
    if _newclass:nres = property(_priism.IW_MRC_HEADER_nres_get, _priism.IW_MRC_HEADER_nres_set)
    __swig_setmethods__["nzfact"] = _priism.IW_MRC_HEADER_nzfact_set
    __swig_getmethods__["nzfact"] = _priism.IW_MRC_HEADER_nzfact_get
    if _newclass:nzfact = property(_priism.IW_MRC_HEADER_nzfact_get, _priism.IW_MRC_HEADER_nzfact_set)
    __swig_setmethods__["min2"] = _priism.IW_MRC_HEADER_min2_set
    __swig_getmethods__["min2"] = _priism.IW_MRC_HEADER_min2_get
    if _newclass:min2 = property(_priism.IW_MRC_HEADER_min2_get, _priism.IW_MRC_HEADER_min2_set)
    __swig_setmethods__["max2"] = _priism.IW_MRC_HEADER_max2_set
    __swig_getmethods__["max2"] = _priism.IW_MRC_HEADER_max2_get
    if _newclass:max2 = property(_priism.IW_MRC_HEADER_max2_get, _priism.IW_MRC_HEADER_max2_set)
    __swig_setmethods__["min3"] = _priism.IW_MRC_HEADER_min3_set
    __swig_getmethods__["min3"] = _priism.IW_MRC_HEADER_min3_get
    if _newclass:min3 = property(_priism.IW_MRC_HEADER_min3_get, _priism.IW_MRC_HEADER_min3_set)
    __swig_setmethods__["max3"] = _priism.IW_MRC_HEADER_max3_set
    __swig_getmethods__["max3"] = _priism.IW_MRC_HEADER_max3_get
    if _newclass:max3 = property(_priism.IW_MRC_HEADER_max3_get, _priism.IW_MRC_HEADER_max3_set)
    __swig_setmethods__["min4"] = _priism.IW_MRC_HEADER_min4_set
    __swig_getmethods__["min4"] = _priism.IW_MRC_HEADER_min4_get
    if _newclass:min4 = property(_priism.IW_MRC_HEADER_min4_get, _priism.IW_MRC_HEADER_min4_set)
    __swig_setmethods__["max4"] = _priism.IW_MRC_HEADER_max4_set
    __swig_getmethods__["max4"] = _priism.IW_MRC_HEADER_max4_get
    if _newclass:max4 = property(_priism.IW_MRC_HEADER_max4_get, _priism.IW_MRC_HEADER_max4_set)
    __swig_setmethods__["file_type"] = _priism.IW_MRC_HEADER_file_type_set
    __swig_getmethods__["file_type"] = _priism.IW_MRC_HEADER_file_type_get
    if _newclass:file_type = property(_priism.IW_MRC_HEADER_file_type_get, _priism.IW_MRC_HEADER_file_type_set)
    __swig_setmethods__["lens"] = _priism.IW_MRC_HEADER_lens_set
    __swig_getmethods__["lens"] = _priism.IW_MRC_HEADER_lens_get
    if _newclass:lens = property(_priism.IW_MRC_HEADER_lens_get, _priism.IW_MRC_HEADER_lens_set)
    __swig_setmethods__["n1"] = _priism.IW_MRC_HEADER_n1_set
    __swig_getmethods__["n1"] = _priism.IW_MRC_HEADER_n1_get
    if _newclass:n1 = property(_priism.IW_MRC_HEADER_n1_get, _priism.IW_MRC_HEADER_n1_set)
    __swig_setmethods__["n2"] = _priism.IW_MRC_HEADER_n2_set
    __swig_getmethods__["n2"] = _priism.IW_MRC_HEADER_n2_get
    if _newclass:n2 = property(_priism.IW_MRC_HEADER_n2_get, _priism.IW_MRC_HEADER_n2_set)
    __swig_setmethods__["v1"] = _priism.IW_MRC_HEADER_v1_set
    __swig_getmethods__["v1"] = _priism.IW_MRC_HEADER_v1_get
    if _newclass:v1 = property(_priism.IW_MRC_HEADER_v1_get, _priism.IW_MRC_HEADER_v1_set)
    __swig_setmethods__["v2"] = _priism.IW_MRC_HEADER_v2_set
    __swig_getmethods__["v2"] = _priism.IW_MRC_HEADER_v2_get
    if _newclass:v2 = property(_priism.IW_MRC_HEADER_v2_get, _priism.IW_MRC_HEADER_v2_set)
    __swig_setmethods__["min5"] = _priism.IW_MRC_HEADER_min5_set
    __swig_getmethods__["min5"] = _priism.IW_MRC_HEADER_min5_get
    if _newclass:min5 = property(_priism.IW_MRC_HEADER_min5_get, _priism.IW_MRC_HEADER_min5_set)
    __swig_setmethods__["max5"] = _priism.IW_MRC_HEADER_max5_set
    __swig_getmethods__["max5"] = _priism.IW_MRC_HEADER_max5_get
    if _newclass:max5 = property(_priism.IW_MRC_HEADER_max5_get, _priism.IW_MRC_HEADER_max5_set)
    __swig_setmethods__["num_times"] = _priism.IW_MRC_HEADER_num_times_set
    __swig_getmethods__["num_times"] = _priism.IW_MRC_HEADER_num_times_get
    if _newclass:num_times = property(_priism.IW_MRC_HEADER_num_times_get, _priism.IW_MRC_HEADER_num_times_set)
    __swig_setmethods__["interleaved"] = _priism.IW_MRC_HEADER_interleaved_set
    __swig_getmethods__["interleaved"] = _priism.IW_MRC_HEADER_interleaved_get
    if _newclass:interleaved = property(_priism.IW_MRC_HEADER_interleaved_get, _priism.IW_MRC_HEADER_interleaved_set)
    __swig_setmethods__["tilt_x"] = _priism.IW_MRC_HEADER_tilt_x_set
    __swig_getmethods__["tilt_x"] = _priism.IW_MRC_HEADER_tilt_x_get
    if _newclass:tilt_x = property(_priism.IW_MRC_HEADER_tilt_x_get, _priism.IW_MRC_HEADER_tilt_x_set)
    __swig_setmethods__["tilt_y"] = _priism.IW_MRC_HEADER_tilt_y_set
    __swig_getmethods__["tilt_y"] = _priism.IW_MRC_HEADER_tilt_y_get
    if _newclass:tilt_y = property(_priism.IW_MRC_HEADER_tilt_y_get, _priism.IW_MRC_HEADER_tilt_y_set)
    __swig_setmethods__["tilt_z"] = _priism.IW_MRC_HEADER_tilt_z_set
    __swig_getmethods__["tilt_z"] = _priism.IW_MRC_HEADER_tilt_z_get
    if _newclass:tilt_z = property(_priism.IW_MRC_HEADER_tilt_z_get, _priism.IW_MRC_HEADER_tilt_z_set)
    __swig_setmethods__["num_waves"] = _priism.IW_MRC_HEADER_num_waves_set
    __swig_getmethods__["num_waves"] = _priism.IW_MRC_HEADER_num_waves_get
    if _newclass:num_waves = property(_priism.IW_MRC_HEADER_num_waves_get, _priism.IW_MRC_HEADER_num_waves_set)
    __swig_setmethods__["iwav1"] = _priism.IW_MRC_HEADER_iwav1_set
    __swig_getmethods__["iwav1"] = _priism.IW_MRC_HEADER_iwav1_get
    if _newclass:iwav1 = property(_priism.IW_MRC_HEADER_iwav1_get, _priism.IW_MRC_HEADER_iwav1_set)
    __swig_setmethods__["iwav2"] = _priism.IW_MRC_HEADER_iwav2_set
    __swig_getmethods__["iwav2"] = _priism.IW_MRC_HEADER_iwav2_get
    if _newclass:iwav2 = property(_priism.IW_MRC_HEADER_iwav2_get, _priism.IW_MRC_HEADER_iwav2_set)
    __swig_setmethods__["iwav3"] = _priism.IW_MRC_HEADER_iwav3_set
    __swig_getmethods__["iwav3"] = _priism.IW_MRC_HEADER_iwav3_get
    if _newclass:iwav3 = property(_priism.IW_MRC_HEADER_iwav3_get, _priism.IW_MRC_HEADER_iwav3_set)
    __swig_setmethods__["iwav4"] = _priism.IW_MRC_HEADER_iwav4_set
    __swig_getmethods__["iwav4"] = _priism.IW_MRC_HEADER_iwav4_get
    if _newclass:iwav4 = property(_priism.IW_MRC_HEADER_iwav4_get, _priism.IW_MRC_HEADER_iwav4_set)
    __swig_setmethods__["iwav5"] = _priism.IW_MRC_HEADER_iwav5_set
    __swig_getmethods__["iwav5"] = _priism.IW_MRC_HEADER_iwav5_get
    if _newclass:iwav5 = property(_priism.IW_MRC_HEADER_iwav5_get, _priism.IW_MRC_HEADER_iwav5_set)
    __swig_setmethods__["zorig"] = _priism.IW_MRC_HEADER_zorig_set
    __swig_getmethods__["zorig"] = _priism.IW_MRC_HEADER_zorig_get
    if _newclass:zorig = property(_priism.IW_MRC_HEADER_zorig_get, _priism.IW_MRC_HEADER_zorig_set)
    __swig_setmethods__["xorig"] = _priism.IW_MRC_HEADER_xorig_set
    __swig_getmethods__["xorig"] = _priism.IW_MRC_HEADER_xorig_get
    if _newclass:xorig = property(_priism.IW_MRC_HEADER_xorig_get, _priism.IW_MRC_HEADER_xorig_set)
    __swig_setmethods__["yorig"] = _priism.IW_MRC_HEADER_yorig_set
    __swig_getmethods__["yorig"] = _priism.IW_MRC_HEADER_yorig_get
    if _newclass:yorig = property(_priism.IW_MRC_HEADER_yorig_get, _priism.IW_MRC_HEADER_yorig_set)
    __swig_setmethods__["nlab"] = _priism.IW_MRC_HEADER_nlab_set
    __swig_getmethods__["nlab"] = _priism.IW_MRC_HEADER_nlab_get
    if _newclass:nlab = property(_priism.IW_MRC_HEADER_nlab_get, _priism.IW_MRC_HEADER_nlab_set)
    __swig_setmethods__["label"] = _priism.IW_MRC_HEADER_label_set
    __swig_getmethods__["label"] = _priism.IW_MRC_HEADER_label_get
    if _newclass:label = property(_priism.IW_MRC_HEADER_label_get, _priism.IW_MRC_HEADER_label_set)
    def SWAP_VARS(*args): 
        """SWAP_VARS(self)"""
        return _priism.IW_MRC_HEADER_SWAP_VARS(*args)

    def __init__(self, *args):
        """__init__(self) -> IW_MRC_HEADER"""
        _swig_setattr(self, IW_MRC_HEADER, 'this', _priism.new_IW_MRC_HEADER(*args))
        _swig_setattr(self, IW_MRC_HEADER, 'thisown', 1)
    def allString(*args): 
        """allString(self) -> string"""
        return _priism.IW_MRC_HEADER_allString(*args)

    def niceString(*args): 
        """niceString(self) -> string"""
        return _priism.IW_MRC_HEADER_niceString(*args)

    def byteOrderIsSwapped(*args): 
        """byteOrderIsSwapped(self) -> bool"""
        return _priism.IW_MRC_HEADER_byteOrderIsSwapped(*args)

    def init_simple(*args): 
        """
        init_simple(self, int the_mode, int the_nx, int the_ny, int the_nz=1)
        init_simple(self, int the_mode, int the_nx, int the_ny)
        """
        return _priism.IW_MRC_HEADER_init_simple(*args)

    def addTitle(*args): 
        """
        addTitle(self, char s, int n=-1)
        addTitle(self, char s)
        """
        return _priism.IW_MRC_HEADER_addTitle(*args)

    def __del__(self, destroy=_priism.delete_IW_MRC_HEADER):
        """__del__(self)"""
        try:
            if self.thisown: destroy(self)
        except: pass


class IW_MRC_HEADERPtr(IW_MRC_HEADER):
    def __init__(self, this):
        _swig_setattr(self, IW_MRC_HEADER, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, IW_MRC_HEADER, 'thisown', 0)
        _swig_setattr(self, IW_MRC_HEADER,self.__class__,IW_MRC_HEADER)
_priism.IW_MRC_HEADER_swigregister(IW_MRC_HEADERPtr)

class PriismFile(_object):
    """Proxy of C++ PriismFile class"""
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, PriismFile, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, PriismFile, name)
    def __repr__(self):
        return "<%s.%s; proxy of C++ PriismFile instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        """
        __init__(self, char filename, bool readable=1, bool writable=0) -> PriismFile
        __init__(self, char filename, bool readable=1) -> PriismFile
        __init__(self, char filename) -> PriismFile
        """
        _swig_setattr(self, PriismFile, 'this', _priism.new_PriismFile(*args))
        _swig_setattr(self, PriismFile, 'thisown', 1)
    def __del__(self, destroy=_priism.delete_PriismFile):
        """__del__(self)"""
        try:
            if self.thisown: destroy(self)
        except: pass

    __swig_setmethods__["header"] = _priism.PriismFile_header_set
    __swig_getmethods__["header"] = _priism.PriismFile_header_get
    if _newclass:header = property(_priism.PriismFile_header_get, _priism.PriismFile_header_set)
    __swig_setmethods__["ext_header"] = _priism.PriismFile_ext_header_set
    __swig_getmethods__["ext_header"] = _priism.PriismFile_ext_header_get
    if _newclass:ext_header = property(_priism.PriismFile_ext_header_get, _priism.PriismFile_ext_header_set)
    __swig_setmethods__["bytesSwapped"] = _priism.PriismFile_bytesSwapped_set
    __swig_getmethods__["bytesSwapped"] = _priism.PriismFile_bytesSwapped_get
    if _newclass:bytesSwapped = property(_priism.PriismFile_bytesSwapped_get, _priism.PriismFile_bytesSwapped_set)
    def allocExtHeader(*args): 
        """allocExtHeader(self, int nsecs, int nInt, int nReal)"""
        return _priism.PriismFile_allocExtHeader(*args)

    def setExtFloat(*args): 
        """setExtFloat(self, int sec, int n, float a)"""
        return _priism.PriismFile_setExtFloat(*args)

    def setExtInt(*args): 
        """setExtInt(self, int sec, int n, long a)"""
        return _priism.PriismFile_setExtInt(*args)

    def extFloat(*args): 
        """extFloat(self, int sec, int n) -> float"""
        return _priism.PriismFile_extFloat(*args)

    def extInt(*args): 
        """extInt(self, int sec, int n) -> long"""
        return _priism.PriismFile_extInt(*args)

    def readHeader(*args): 
        """readHeader(self)"""
        return _priism.PriismFile_readHeader(*args)

    def writeHeader(*args): 
        """writeHeader(self)"""
        return _priism.PriismFile_writeHeader(*args)

    def seekFirstSec(*args): 
        """seekFirstSec(self)"""
        return _priism.PriismFile_seekFirstSec(*args)

    def resetAppendStats(*args): 
        """resetAppendStats(self)"""
        return _priism.PriismFile_resetAppendStats(*args)

    def appendSec(*args): 
        """
        appendSec(self, unsigned char array2d)
        appendSec(self, short array2d)
        appendSec(self, float array2d)
        appendSec(self, complex32 array2d)
        appendSec(self, unsigned short array2d)
        appendSec(self, long array2d)
        """
        return _priism.PriismFile_appendSec(*args)

    def readSec(*args): 
        """
        readSec(self, unsigned char array2d)
        readSec(self, short array2d)
        readSec(self, float array2d)
        readSec(self, complex32 array2d)
        readSec(self, unsigned short array2d)
        readSec(self, long array2d)
        """
        return _priism.PriismFile_readSec(*args)

    def initHeaderFor(*args): 
        """
        initHeaderFor(self, unsigned char array3d)
        initHeaderFor(self, short array3d)
        initHeaderFor(self, float array3d)
        initHeaderFor(self, complex32 array3d)
        initHeaderFor(self, unsigned short array3d)
        initHeaderFor(self, long array3d)
        """
        return _priism.PriismFile_initHeaderFor(*args)

    def rewriteHeaderAndClose(*args): 
        """rewriteHeaderAndClose(self)"""
        return _priism.PriismFile_rewriteHeaderAndClose(*args)

    def close(*args): 
        """close(self)"""
        return _priism.PriismFile_close(*args)


class PriismFilePtr(PriismFile):
    def __init__(self, this):
        _swig_setattr(self, PriismFile, 'this', this)
        if not hasattr(self,"thisown"): _swig_setattr(self, PriismFile, 'thisown', 0)
        _swig_setattr(self, PriismFile,self.__class__,PriismFile)
_priism.PriismFile_swigregister(PriismFilePtr)

#######################################################################
#######################################################################
###
###   PriismFile class methods
###

def info(pf):
    """print usefull information from header"""
    
    print pf.header.niceString()
    # PriismFile.info = lambda (self,) : self.header.PrintNicely()
PriismFile.info = info
del info

def shape(pf):
    """(nz,ny,nx) from header"""
    return (pf.header.nz,pf.header.ny,pf.header.nx)
PriismFile.shape = shape
del shape

def type(pf):
    """numarray type that corresponds to MRC header 'mode'"""
    import numarray as na
    if   pf.header.mode == 0:
        return na.UInt8
    elif pf.header.mode == 1:
        return na.Int16
    elif pf.header.mode == 2:
        return na.Float32
    #      elif pf.header.mode == 3:
    #          return na.Complex32 ??
    elif pf.header.mode == 4:
        return na.Complex32
    elif pf.header.mode == 6:
        return na.UInt16
    elif pf.header.mode == 7:
        return na.Int32
    else:
        raise "** unknown type (mode: "+ pf.header.mode+ ") **"
        return None
    
PriismFile.type = type
del type

def setType(pf, ty):
    """set MRC header 'mode' from numarray type"""
    import numarray as na

    if   ty == na.UInt8:
        pf.header.mode = 0
    elif ty == na.Int16:
        pf.header.mode = 1
    elif ty == na.Float32:
        pf.header.mode = 2
    #      elif ty == na.Complex32 ??
    #          pf.header.mode = 3
    elif ty == na.Complex32:
        pf.header.mode = 4
    elif ty == na.UInt16:
        pf.header.mode = 6
    elif ty == na.Int32:
        pf.header.mode = 7
    else:
        print "** MRC doesn't know type ", ty, " **"
        return
PriismFile.setType = setType
del setType

def setTypeFrom(pf, arr):
    """set MRC header 'mode' from numarray type of array"""
    import numarray as na
    pf.setType( arr.type() )
PriismFile.setTypeFrom = setTypeFrom
del setTypeFrom


def emptyVol(pf):
    """allocates and returns (3D) array of size given by header (nz,ny,nx)"""
    import numarray as na
    return na.zeros(type=pf.type(), shape=pf.shape())

PriismFile.emptyVol = emptyVol
# del emptyVol


def emptySec(pf):
    """allocates and returns (2D) array of size given by header (ny,nx)"""
    
    import numarray as na
    return na.zeros(type=pf.type(), shape=(pf.header.ny,pf.header.nx))

PriismFile.emptySec = emptySec
# del emptySec




def getTilt(pf):
    "returns 1D numarray containing float #0 (1st float) from each z sec"
    
    import numarray as na
    tlt = na.array(type=na.Float32, shape=(pf.header.nz))
    for i in range(pf.header.nz):
        tlt[i] = pf.extFloat(i, 0)
    return tlt
PriismFile.getTilt = getTilt
del getTilt

def getExpTime(pf):
    "returns 1D numarray containing float #8 (9th float) from each z sec"
    import numarray as na
    exp = na.array(type=na.Float32, shape=(pf.header.nz))
    for i in range(pf.header.nz):
        exp[i] = pf.extFloat(i, 8)
    return exp
PriismFile.getExpTime = getExpTime
del getExpTime

def readVol(pf, a):
    """reads multiple (smallest: a.shape[0] or header.nz) sections into array a"""
    if len(a.shape) != 3:
        print "Error: array not 3d"

    z=0
    nz = a.shape[0] #read as many secs as 'a' has - or pf.header.nz
    if nz > pf.header.nz:
        nz = pf.header.nz
    while(z<nz):
        pf.readSec(a[z])
        z+=1
    
PriismFile.readVol = readVol
del readVol

def loadVol(pf, a):
    """reads multiple (smallest: a.shape[0] or header.nz) sections
    into array a - after seek to first section"""
    if len(a.shape) != 3:
        print "Error: array not 3d"
    # TODO check dims of a vs. pf.header

    pf.seekFirstSec();
    pf.readVol(a)
    
PriismFile.loadVol = loadVol
del loadVol


def load(pf):
    """allocates and returns array with all sections read in"""
    a = emptyVol(pf)
    pf.loadVol(a)
    return a
PriismFile.load = load
del load



def appendVol(pf, a):
    """appends all sections from array a to file"""
    if not 2<= len(a.shape) <= 3:
        print "Error: array not 3d (or 2d)"
        return

    if len(a.shape) == 2:
        pf.appendSec(a)
    else:
        nz = a.shape[0]
        z=0
        while(z<nz):
            pf.appendSec(a[z])
            z+=1
PriismFile.appendVol = appendVol
del appendVol

def saveVol(pf, a):
    """writes header and all sections from 'a' to file and closes it"""
    if not 2<= len(a.shape) <= 3:
        print "Error: array not 3d (or 2d)"
        return
    # TODO check dims of a vs. pf.header
    #see now save(arr,fn):    pf.initHeaderFor(a)
    
    pf.writeHeader()
    pf.appendVol(a)
    pf.rewriteHeaderAndClose()
    
PriismFile.saveVol = saveVol
del saveVol

def initHeaderFrom(pf, pfOrig, extHdr=0):
    """copy header info from pgOrig - w/ or w/o extended header"""
    
    pf.header = pfOrig.header
    if extHdr == 0:
        pf.header.inbsym = pf.header.nint = pf.header.nreal = 0
    else:
        pf.allocExtHeader(pfOrig.header.nz, pfOrig.header.nint, pfOrig.header.nreal)
        for z in range(pfOrig.header.nz):
            for i in range(pfOrig.header.nint):
                pf.setExtInt(z, i, pfOrig.extInt(z,i))
            for r in range(pfOrig.header.nreal):
                pf.setExtFloat(z, r, pfOrig.extFloat(z,r))
                
PriismFile.initHeaderFrom = initHeaderFrom
del initHeaderFrom




#######################################################################
#######################################################################
###
###   module function
###


def emptyArrS(shape):
    """allocates and returns 'signed short' array of given shape"""
    import numarray as na
    return na.zeros(type=na.Int16, shape=shape)
def emptyArrF(shape):
    """allocates and returns 'single prec. float' array of given shape"""
    import numarray as na
    return na.zeros(type=na.Float32, shape=shape)
def emptyArrU(shape):
    """allocates and returns 'unsigned short' array of given shape"""
    import numarray as na
    return na.zeros(type=na.UInt16, shape=shape)
def emptyArrC(shape):
    """allocates and returns 'single prec. complex' array of given shape"""
    import numarray as na
    return na.zeros(type=na.Complex32, shape=shape)


def load(fn):
    """allocates, loads and returns data array from MRC/Priism file"""
    pf = PriismFile(fn)
    a = emptyVol(pf)
    pf.loadVol(a)
    return a

def loadF(fn):
    """allocates, loads and returns data array from MRC/Priism file (convert to float if needed)"""
    pf = PriismFile(fn)
    a =  emptyArrF((pf.header.nz,pf.header.ny,pf.header.nx))
    pf.loadVol(a)
    return a

def save(arr, fn):
    """creates file "fn", uses simple header, saves (3D) data as Priism file"""
    pf = PriismFile(fn, 0, 1)
    pf.initHeaderFor(arr)
    pf.saveVol(arr)



