#Standard library imports
from copy import deepcopy

#External library imports
import numpy as np

#Internal imports
from Atoms import Atoms
from Box import Box
from atomman.tools import nlist, dvect
     
class System(object):
    """Class for representing an atomic system."""
    
    def __init__(self, atoms=Atoms(), box=Box(), pbc=(True, True, True), scale=False, prop={}):
        """
        Initilize a System by joining an Atoms and Box instance.
        
        Keyword Arguments:
        atoms -- Instance of Atoms to include.
        box -- Instance of Box to include.
        pbc -- Tuple of three booleans where True indicates a given box dimension is periodic. Default is all True.
        scale -- If True, atoms' pos will be scaled relative to the box.  Default is False.
        prop -- Dictionary of free-form system-wide properties.
        """
                
        assert isinstance(box, Box), 'Invalid box entry'
        self.__box = box
        
        assert isinstance(atoms, Atoms), 'Invalid atoms entry'
        self.__atoms = atoms
        
        if scale is True:
            self.atoms.view['pos'][:] = self.unscale(atoms.view['pos'])
        
        self.pbc = pbc
        
        assert isinstance(prop, dict), 'invalid prop dictionary'
        self.__prop = prop

    @property    
    def atoms(self): 
        """The Atoms instance within the System."""
        return self.__atoms
        
    def atoms_prop(self, a_id=None, key=None, value=None, dtype=None, scale=False):
        """
        Extends atoms.prop() with a scale argument.
        
        Keyword Arguments:
        a_id -- atom index.
        key -- atom property name.
        value -- value(s) to assign to properties associated with a_id and/or term.
        dtype -- data type to explicitly set or retrieve value as. 
        scale -- boolean indicating if property is a 3D vector to be scaled relative to the box vectors.

        If no arguments given, returns a list of the assigned property keys. Otherwise, a_id and/or key must be specified. The key specifies which property, and the a_id which atom(s) to access. With no value argument, prop() returns which value(s) are associated with the given a_id and/or key. With a value argument, the value is saved according to the given a_id and/or key. The positions are stored in absolute coordinates, but the scale argument allows for pos (and other 3D vectors) in box-scaled units to be converted during assignment and retrieval.
        """   
  
        #No scaling is identical to atoms.prop()
        if scale is False:
            return self.__atoms.prop(a_id=a_id, key=key, value=value, dtype=dtype)
                
        #Unscale value before assigning
        elif value is not None:
            value = self.unscale(value)
            self.__atoms.prop(a_id=a_id, key=key, value=value, dtype=dtype)
        
        #Call atoms.prop() and scale values being returned 
        else:
            value = self.__atoms.prop(a_id=a_id, key=key, dtype=dtype)
            if value is None:
                return None
            else:
                return self.scale(value)              
    @property
    def natoms(self):
        """The number of atoms."""
        return self.__atoms.natoms
    
    @property
    def natypes(self):
        """The maximum atype value."""
        return self.__atoms.natypes
    
    @property
    def box(self):
        """The Box instance within the system"""
        return self.__box
    
    def box_set(self, **kwargs): 
        """
        Extends box.set() with a scale argument.
        
        If no arguments (excluding scale) given, box is set to square unit box with origin = [0,0,0].
        Otherwise, must give one of the following sets:
        - vects, (and origin).
        - avect, bvect, cvect, (and origin).
        - a, b, c, (alpha, beta, gamma, and origin).
        - lx, ly, lz, (xy, xz, yz, and origin).
        - xlo, xhi, ylo, yhi, zlo, zhi, (xy, xz, and yz).
        
        The scale keyword argument affects how the atom positions are handled when the box is changed.
        scale = False (default). The absolute atom positions remain unchanged.
        scale = True. The scaled (box-relative) positions remain unchanged.
        """
        
        scale = kwargs.pop('scale', False)
        if not 'scale':
            self.__box.set(**kwargs)
        else:
            spos = self.scale(self.atoms.view['pos'])
            self.__box.set(**kwargs)
            self.atoms.view['pos'][:] = self.unscale(spos)
    
    def box_normalize(self):
        """Extends box.normalize()."""
        
        spos = self.scale(self.atoms.view['pos'])
        self.__box.normalize()
        self.atoms.view['pos'][:] = self.unscale(spos)
    
    @property
    def pbc(self):
        """The periodic boundary condition settings for the System."""
        return self.__pbc
        
    @pbc.setter
    def pbc(self, value):
        pbc = np.asarray(value, dtype=bool)
        assert pbc.shape == (3L,), 'invalid pbc entry' 
        self.__pbc = pbc
    
    @property
    def prop(self):
        """OrderedDict of free-form System properties"""
        return self.__prop
    
    def scale(self, value):
        """Converts 3D vectors from absolute to scaled box coordinates."""

        value = np.asarray(value)
        vects = self.box.vects
        inverse = np.linalg.inv(vects)
        origin = self.box.origin
        
        return (value - origin).dot(inverse)
          
    def unscale(self, value):
        """Converts 3D vectors from scaled box to absolute coordinates."""

        value = np.asarray(value)
        vects = self.box.vects
        origin = self.box.origin
        
        return value.dot(vects) + origin
    
    def dvect(self, pos_0, pos_1):
        """Computes the shortest distance between two (sets of) positions taking self system's pbc information into account.
        
        The arguments pos_0 and pos_1 can either be atom index values for the current system, a single position, or a list of positions.
        Note that numpy broadcasting rules apply to the treatment of the arguments.
        """
        
        pos_0 = np.asarray(pos_0)
        #if pos_0 is integer(s), use as atom indexes of self system 
        if pos_0.dtype == int:
            pos_0 = self.atoms.view['pos'][pos_0]
        
        pos_1 = np.asarray(pos_1)
        #if pos_1 is integer(s), use as atom indexes of self system
        if pos_1.dtype == int:
            pos_1 = self.atoms.view['pos'][pos_1]
        
        #call atomman.tools.dvect using self system's box and pbc
        return dvect(pos_0, pos_1, self.box, self.pbc)
        
    def wrap(self):
        """Wrap atoms around periodic boundaries and extend non-periodic boundaries such that all atoms are within the box."""
        
        mins = np.array([0.0, 0.0, 0.0])
        maxs = np.array([1.0, 1.0, 1.0])
        spos = self.scale(self.atoms.view['pos'])
        
        for i in xrange(3):
            if self.pbc[i]:
                spos[:, i] -= np.floor(spos[:, i])
            else:
                min = spos[:, i].min()
                max = spos[:, i].max()
                if min < 0.0: mins[i] = min - 0.001
                if max > 1.0: maxs[i] = max + 0.001             
                        
        self.atoms.view['pos'][:] = self.unscale(spos)        
        
        origin = self.box.origin + mins.dot(self.box.vects) 
        avect = self.box.avect * (maxs[0] - mins[0])
        bvect = self.box.bvect * (maxs[1] - mins[1])
        cvect = self.box.cvect * (maxs[2] - mins[2])
        self.box_set(avect=avect, bvect=bvect, cvect=cvect, origin=origin)          
    
    def nlist(self, cutoff, cmult=1):
        """Build neighbor list for all atoms based on a cutoff.
        
        Keyword Arguments:
        cutoff -- radial cutoff distance for including atoms as neighbors.
        cmult -- int factor that changes the underlying binning algorithm. Default is 1, which should be the fastest. 
        """
        self.prop['nlist'] = nlist(self, cutoff, cmult)