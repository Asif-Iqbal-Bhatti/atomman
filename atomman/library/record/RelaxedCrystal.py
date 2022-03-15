# coding: utf-8

# Standard Python imports
import io
from typing import Optional, Union, Tuple

# https://github.com/usnistgov/DataModelDict
from DataModelDict import DataModelDict as DM

# https://github.com/usnistgov/yabadaba
from yabadaba.record import Record
from yabadaba import load_query

# https://pandas.pydata.org/
import pandas as pd

# atomman imports
import atomman.unitconvert as uc
from ... import System

class RelaxedCrystal(Record):
    """
    Class for representing relaxed_crystal records that provide the structure
    information for crystal structures relaxed using a specific interatomic
    potential.
    """
    def __init__(self,
                 model: Union[str, io.IOBase, DM, None] = None,
                 name: Optional[str] = None):
        """
        Initializes a Record object for a given style.
        
        Parameters
        ----------
        model : str, file-like object, DataModelDict
            The contents of the record.
        name : str, optional
            The unique name to assign to the record.  If model is a file
            path, then the default record name is the file name without
            extension.
        """
        if model is not None:
            super().__init__(model=model, name=name)
        elif name is not None:
            self.name = name

    @property
    def style(self) -> str:
        """str: The record style"""
        return 'relaxed_crystal'

    @property
    def modelroot(self) -> str:
        """str: The root element of the content"""
        return 'relaxed-crystal'

    @property
    def xsd_filename(self) -> Tuple[str, str]:
        """tuple: The module path and file name of the record's xsd schema"""
        return ('atomman.library.xsd', f'{self.style}.xsd')

    def load_model(self,
                   model: Union[str, io.IOBase, DM],
                   name: Optional[str] = None):
        """
        Loads record contents from a given model.

        Parameters
        ----------
        model : str or DataModelDict
            The model contents of the record to load.
        name : str, optional
            The name to assign to the record.  Often inferred from other
            attributes if not given.
        """
        super().load_model(model, name=name)        
        crystal = self.model[self.modelroot]
        
        self.__key = crystal['key']
        self.__method = crystal['method']
        self.__standing = crystal['standing']

        self.__potential_LAMMPS_id = crystal['potential-LAMMPS']['id']
        self.__potential_LAMMPS_key = crystal['potential-LAMMPS']['key']
        self.__potential_id = crystal['potential-LAMMPS']['potential']['id']
        self.__potential_key = crystal['potential-LAMMPS']['potential']['key']

        self.__family = crystal['system-info']['family']
        self.__parent_key = crystal['system-info']['parent_key']
        self.__symbols = crystal['system-info'].aslist('symbol')
        self.__composition = crystal['system-info']['composition']
        self.__crystalfamily = crystal['system-info']['cell']['crystal-family']
        self.__natypes = crystal['system-info']['cell']['natypes']
        self.__a = crystal['system-info']['cell']['a']
        self.__b = crystal['system-info']['cell']['b']
        self.__c = crystal['system-info']['cell']['c']
        self.__alpha = crystal['system-info']['cell']['alpha']
        self.__beta = crystal['system-info']['cell']['beta']
        self.__gamma = crystal['system-info']['cell']['gamma']
        
        self.__natoms = crystal['atomic-system']['atoms']['natoms']

        self.__potential_energy = uc.value_unit(crystal['potential-energy'])
        self.__cohesive_energy = uc.value_unit(crystal['cohesive-energy'])
        
        self.__ucell = None

        # Set name as key if no name given
        try:
            self.name
        except:
            self.name = self.key

    @property
    def key(self) -> str:
        """str : A UUID4 key assigned to the record"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__key

    @property
    def method(self) -> str:
        """str : Indicates the relaxation method used: box, static or dynamic"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__method
    
    @property
    def standing(self) -> str:
        """str : 'good' or 'bad', with bad indicating it to be a duplicate or transformation"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__standing
    
    @property
    def family(self) -> str:
        """str : The associated prototype/reference crystal id that the relaxed crystal is based on"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__family

    @property
    def parent_key(self) -> str:
        """str : The key assigned to the record of the relaxation calculation used"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__parent_key

    @property
    def potential_LAMMPS_id(self) -> str:
        """str : The id of the LAMMPS implementation used to relax the crystal"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__potential_LAMMPS_id

    @property
    def potential_LAMMPS_key(self) -> str:
        """str : The key of the LAMMPS implementation used to relax the crystal"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__potential_LAMMPS_key

    @property
    def potential_id(self) -> str:
        """str : The id of the potential model used to relax the crystal"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__potential_id

    @property
    def potential_key(self) -> str:
        """str : The key of the potential model used to relax the crystal"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__potential_key

    @property
    def cohesive_energy(self) -> float:
        """float : The computed per-atom cohesive energy"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__cohesive_energy

    @property
    def potential_energy(self) -> float:
        """float : The measured per-atom potential energy"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__potential_energy

    @property
    def composition(self) -> str:
        """str : The crystal's composition"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__composition

    @property
    def symbols(self) -> list:
        """list : The list of element model symbols"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__symbols

    @property
    def natoms(self) -> int:
        """int : The number of atoms in the unit cell"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__natoms

    @property
    def natypes(self) -> int:
        """int : The number of atom types in the unit cell"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__natypes

    @property
    def crystalfamily(self) -> str:
        """str : The crystal's system family"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__crystalfamily

    @property
    def a(self) -> float:
        """float : The unit cell's a lattice parameter"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__a

    @property
    def b(self) -> float:
        """float : The unit cell's b lattice parameter"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__b

    @property
    def c(self) -> float:
        """float : The unit cell's c lattice parameter"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__c

    @property
    def alpha(self) -> float:
        """float : The unit cell's alpha lattice angle"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__alpha

    @property
    def beta(self) -> float:
        """float : The unit cell's beta lattice angle"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__beta

    @property
    def gamma(self) -> float:
        """float : The unit cell's gamma lattice angle"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.__gamma

    @property
    def ucell(self) -> System:
        """atomman.System : The unit cell system for the crystal"""
        if self.model is None:
            raise AttributeError('No model information loaded')
        if self.__ucell is None:
            self.__ucell = System(model=self.model)
        return self.__ucell

    def build_model(self) -> DM:
        if self.model is None:
            raise AttributeError('No model information loaded')
        return self.model

    def metadata(self) -> dict:
        """
        Generates a dict of simple metadata values associated with the record.
        Useful for quickly comparing records and for building pandas.DataFrames
        for multiple records of the same style.
        """
        params = {}
        params['name'] = self.name
        params['key'] = self.key
        params['method'] = self.method
        params['standing'] = self.standing
        params['family'] = self.family
        params['parent_key'] = self.parent_key
        
        params['potential_LAMMPS_id'] = self.potential_LAMMPS_id
        params['potential_LAMMPS_key'] = self.potential_LAMMPS_key
        params['potential_id'] = self.potential_id
        params['potential_key'] = self.potential_key
        
        params['crystalfamily'] = self.crystalfamily
        params['natypes'] = self.natypes
        params['symbols'] = self.symbols
        params['composition'] = self.composition

        params['a'] = self.a
        params['b'] = self.b
        params['c'] = self.c
        params['alpha'] = self.alpha
        params['beta'] = self.beta
        params['gamma'] = self.gamma
        params['natoms'] = self.natoms

        params['potential_energy'] = self.potential_energy
        params['cohesive_energy'] = self.cohesive_energy

        return params

    @property
    def queries(self) -> dict:
        """dict: Query objects and their associated parameter names."""
        return {
            'key': load_query(
                style='str_match',
                name='key', 
                path=f'{self.modelroot}.key'),
            'method': load_query(
                style='str_match',
                name='method',
                path=f'{self.modelroot}.id'),
            'standing': load_query(
                style='str_match',
                name='standing',
                path=f'{self.modelroot}.name'),
            'family': load_query(
                style='str_match',
                name='family',
                path=f'{self.modelroot}.prototype'),
            'parent_key': load_query(
                style='str_match',
                name='parent_key',
                path=f'{self.modelroot}.Pearson-symbol'),
            'potential_LAMMPS_id': load_query(
                style='str_match',
                name='potential_LAMMPS_id',
                path=f'{self.modelroot}.Strukturbericht'),
            'potential_LAMMPS_key': load_query(
                style='str_match',
                name='potential_LAMMPS_key',
                path=f'{self.modelroot}.space-group.number'),
            'potential_id': load_query(
                style='str_match',
                name='potential_id',
                path=f'{self.modelroot}.space-group.Hermann-Maguin'),
            'potential_key': load_query(
                style='str_match',
                name='potential_key',
                path=f'{self.modelroot}.space-group.Schoenflies'),
            'composition': load_query(
                style='str_match',
                name='composition',
                path=f'{self.modelroot}.system-info.cell.crystal-family'),
            'symbols': load_query(
                style='in_list',
                name='symbols',
                path=f'{self.modelroot}.system-info.cell.natypes'),
            'natoms': load_query(
                style='int_match',
                name='natoms',
                path=f'{self.modelroot}.system-info.cell.natypes'),
            'natypes': load_query(
                style='int_match',
                name='natypes',
                path=f'{self.modelroot}.system-info.cell.natypes'),
        }

    def pandasfilter(self,
                     dataframe: pd.DataFrame,
                     name: Union[str, list, None] = None,
                     key: Union[str, list, None] = None,
                     method: Union[str, list, None] = None,
                     standing: Union[str, list, None] = None,
                     family: Union[str, list, None] = None,
                     parent_key: Union[str, list, None] = None, 
                     potential_LAMMPS_id: Union[str, list, None] = None,
                     potential_LAMMPS_key: Union[str, list, None] = None,
                     potential_id: Union[str, list, None] = None,
                     potential_key: Union[str, list, None] = None,
                     crystalfamily: Union[str, list, None] = None,
                     composition: Union[str, list, None] = None,
                     symbols: Union[str, list, None] = None,
                     natoms: Union[int, list, None] = None,
                     natypes: Union[int, list, None] = None) -> pd.Series:
        """
        Filters a pandas.DataFrame based on kwargs values for the record style.
        
        Parameters
        ----------
        dataframe : pandas.DataFrame
            A table of metadata for multiple records of the record style.
        name : str or list
            The record name(s) to parse by.
        key : str or list
            The record key(s) to parse by.
        method : str, None or list
            The relaxation method(s) to parse by.  Default value is 'dynamic'.
            Set to None to access records for all relaxation methods.
        standing : str, None or list
            The standing status to parse by.  Default value is 'good'  Set to
            None to access records for all standings.
        family : str or list
            The prototype/reference id(s) that the relaxed crystals are based
            on to parse by.
        parent_key : str or list
            The key(s) of the relaxation calculation records to parse by.
        potential_LAMMPS_id : str or list
            LAMMPS potential implementation id(s) to parse by.
        potential_LAMMPS_key : str or list
            LAMMPS potential implementation keys(s) to parse by.
        potential_id : str or list
            Potential id(s) to parse by.
        potential_key : str or list
            Potential key(s) to parse by.
        crystalfamily : str or list
            Crystal structure families to parse by.
        composition : str or list
            Compositions to parse by.
        symbols : str or list
            Element model symbol(s) to parse by.
        natoms : int or list
            Number of atoms in the unit cell to parse by.
        natypes : int or list
            Number of atom types to parse by.
        
        Returns
        -------
        pandas.Series, numpy.NDArray
            Boolean map of matching values
        """
        matches = super().pandasfilter(dataframe, name=name, key=key,
                                       method=method, standing=standing,
                                       family=family, parent_key=parent_key, 
                                       potential_LAMMPS_id=potential_LAMMPS_id,
                                       potential_LAMMPS_key=potential_LAMMPS_key,
                                       potential_id=potential_id,
                                       potential_key=potential_key,
                                       crystalfamily=crystalfamily,
                                       composition=composition, symbols=symbols,
                                       natoms=natoms, natypes=natypes)
        return matches

    def mongoquery(self,
                   name: Union[str, list, None] = None,
                   key: Union[str, list, None] = None,
                   method: Union[str, list, None] = None,
                   standing: Union[str, list, None] = None,
                   family: Union[str, list, None] = None,
                   parent_key: Union[str, list, None] = None, 
                   potential_LAMMPS_id: Union[str, list, None] = None,
                   potential_LAMMPS_key: Union[str, list, None] = None,
                   potential_id: Union[str, list, None] = None,
                   potential_key: Union[str, list, None] = None,
                   crystalfamily: Union[str, list, None] = None,
                   composition: Union[str, list, None] = None,
                   symbols: Union[str, list, None] = None,
                   natoms: Union[int, list, None] = None,
                   natypes: Union[int, list, None] = None) -> dict:
        """
        Builds a Mongo-style query based on kwargs values for the record style.
        
        Parameters
        ----------
        name : str or list
            The record name(s) to parse by.
        key : str or list
            The record key(s) to parse by.
        method : str, None or list
            The relaxation method(s) to parse by.  Default value is 'dynamic'.
            Set to None to access records for all relaxation methods.
        standing : str, None or list
            The standing status to parse by.  Default value is 'good'  Set to
            None to access records for all standings.
        family : str or list
            The prototype/reference id(s) that the relaxed crystals are based
            on to parse by.
        parent_key : str or list
            The key(s) of the relaxation calculation records to parse by.
        potential_LAMMPS_id : str or list
            LAMMPS potential implementation id(s) to parse by.
        potential_LAMMPS_key : str or list
            LAMMPS potential implementation keys(s) to parse by.
        potential_id : str or list
            Potential id(s) to parse by.
        potential_key : str or list
            Potential key(s) to parse by.
        crystalfamily : str or list
            Crystal structure families to parse by.
        composition : str or list
            Compositions to parse by.
        symbols : str or list
            Element model symbol(s) to parse by.
        natoms : int or list
            Number of atoms in the unit cell to parse by.
        natypes : int or list
            Number of atom types to parse by.
        
        Returns
        -------
        dict
            The Mongo-style query
        """     
        mquery = super().mongoquery(name=name, key=key,
                                    method=method, standing=standing,
                                    family=family, parent_key=parent_key, 
                                    potential_LAMMPS_id=potential_LAMMPS_id,
                                    potential_LAMMPS_key=potential_LAMMPS_key,
                                    potential_id=potential_id,
                                    potential_key=potential_key,
                                    crystalfamily=crystalfamily,
                                    composition=composition, symbols=symbols,
                                    natoms=natoms, natypes=natypes)
        return mquery

    def cdcsquery(self,
                  key: Union[str, list, None] = None,
                  method: Union[str, list, None] = None,
                  standing: Union[str, list, None] = None,
                  family: Union[str, list, None] = None,
                  parent_key: Union[str, list, None] = None, 
                  potential_LAMMPS_id: Union[str, list, None] = None,
                  potential_LAMMPS_key: Union[str, list, None] = None,
                  potential_id: Union[str, list, None] = None,
                  potential_key: Union[str, list, None] = None,
                  crystalfamily: Union[str, list, None] = None,
                  composition: Union[str, list, None] = None,
                  symbols: Union[str, list, None] = None,
                  natoms: Union[int, list, None] = None,
                  natypes: Union[int, list, None] = None) -> dict:
        """
        Builds a CDCS-style query based on kwargs values for the record style.
        
        Parameters
        ----------
        key : str or list
            The record key(s) to parse by.
        method : str, None or list
            The relaxation method(s) to parse by.  Default value is 'dynamic'.
            Set to None to access records for all relaxation methods.
        standing : str, None or list
            The standing status to parse by.  Default value is 'good'  Set to
            None to access records for all standings.
        family : str or list
            The prototype/reference id(s) that the relaxed crystals are based
            on to parse by.
        parent_key : str or list
            The key(s) of the relaxation calculation records to parse by.
        potential_LAMMPS_id : str or list
            LAMMPS potential implementation id(s) to parse by.
        potential_LAMMPS_key : str or list
            LAMMPS potential implementation keys(s) to parse by.
        potential_id : str or list
            Potential id(s) to parse by.
        potential_key : str or list
            Potential key(s) to parse by.
        crystalfamily : str or list
            Crystal structure families to parse by.
        composition : str or list
            Compositions to parse by.
        symbols : str or list
            Element model symbol(s) to parse by.
        natoms : int or list
            Number of atoms in the unit cell to parse by.
        natypes : int or list
            Number of atom types to parse by.
        
        Returns
        -------
        dict
            The CDCS-style query
        """
        mquery = super().cdcsquery(key=key,
                                    method=method, standing=standing,
                                    family=family, parent_key=parent_key, 
                                    potential_LAMMPS_id=potential_LAMMPS_id,
                                    potential_LAMMPS_key=potential_LAMMPS_key,
                                    potential_id=potential_id,
                                    potential_key=potential_key,
                                    crystalfamily=crystalfamily,
                                    composition=composition, symbols=symbols,
                                    natoms=natoms, natypes=natypes)
        return mquery