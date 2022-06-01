# coding: utf-8

# Standard Python libraries
import datetime
import io
from typing import Generator, Optional, Union, Tuple

# https://github.com/usnistgov/DataModelDict
from DataModelDict import DataModelDict as DM

# https://numpy.org/
import numpy as np
import numpy.typing as npt

# https://pandas.pydata.org/
import pandas as pd

# https://matplotlib.org/
import matplotlib.pyplot as plt

# atomman imports 
from .. import Atoms, Box, System
from ..tools import aslist
import atomman.unitconvert as uc

class BondAngleMap():
    """
    Class for generating and analyzing energies of three atom clusters that
    explore a range of interatomic distances and bond angles.  Can be used to
    characterize the 3 atom bond nature of interatomic potentials.
    """
    
    def __init__(self,
                 model: Union[str, io.IOBase, DM, None] = None,
                 rmin: Optional[float] = None,
                 rmax: Optional[float] = None,
                 rnum: Optional[int] = None,
                 thetamin: Optional[float] = None,
                 thetamax: Optional[float] = None,
                 thetanum: Optional[int] = None,
                 r_ij: Optional[npt.ArrayLike] = None,
                 r_ik: Optional[npt.ArrayLike] = None,
                 theta: Optional[npt.ArrayLike] = None,
                 energy: Optional[npt.ArrayLike] = None,
                 symbols: Union[str, list, None] = None):
        """
        Class initializer.  The cluster coordinates (r distances and theta
        angles) are required and can be specified in one of three ways.
        - A data model containing all the information.
        - Input ranges (rmin, rmax, rnum, thetamin, thetamax, thetanum).  The r
          range parameters will be used to generate values for both r_ij and
          r_ik.
        - Explicitly giving r_ij, r_ik and theta values.

        Parameters
        ----------
        model : str, path-like object or DataModelDict, optional
            Collected data model results from a series of runs.  Contains both
            coordinate information and energy values.
        rmin : float, optional
            The minimum value used for the r_ij and r_ik spacings.
        rmax : float, optional
            The maximum value used for the r_ij and r_ik spacings.
        rnum : float, optional
            The number of values used for the r_ij and r_ik spacings.
        thetamin : float, optional
            The minimum value used for the theta angles.
        thetamax : float, optional
            The maximum value used for the theta angles.
        thetanum : float, optional
            The number of values used for the theta angles.
        r_ij : array-like, optional
            All r_ij values used.  If given, the lengths of r_ij, r_ik and
            theta need to be the same.
        r_ik : array-like, optional
            All r_ik values used.  If given, the lengths of r_ij, r_ik and
            theta need to be the same.
        theta : array-like, optional
            All theta values used.  If given, the lengths of r_ij, r_ik and
            theta need to be the same.
        energy : array-like, optional
            All measured energies.  If r_ij, r_ik and theta are given then
            all should be the same length.  If the coordinate range parameters
            are given, then the energies should be of length rnum*rnum*thetanum
            and ordered to correspond to three embedded loops with r_ij
            iterating in the outside loop, r_ik in the middle and theta in the
            inside.  If energy is not given, then all values will initially be
            set to np.nan.
        symbols : str or list, optional
            Element model symbol(s) to associate with the three atoms if/when
            systems are created.  Can either be a single symbol to assign to 
            all atoms, or three symbols to assign to atoms i, j, and k
            individually.  Not needed if systems are not generated by this
            class.
        """
        self.symbols = symbols
        if model is not None:
            try:
                assert rmin is None and rmax is None and rnum is None
                assert thetamin is None and thetamax is None and thetanum is None
                assert r_ij is None and r_ik is None and theta is None
                assert energy is None
            except AssertionError as e:
                raise ValueError('model cannot be given energy or coordinate parameters') from e
            self.model(model)
        else:
            self.set(energy=energy, rmin=rmin, rmax=rmax, rnum=rnum,
                     thetamin=thetamin, thetamax=thetamax, thetanum=thetanum,
                     r_ij=r_ij, r_ik=r_ik, theta=theta)

    @property
    def rmin(self) -> Optional[float]:
        """float or None: The minimum value used for the r_ij and r_ik spacings."""
        return self.__rmin

    @property
    def rmax(self) -> Optional[float]:
        """float or None: The maximum value used for the r_ij and r_ik spacings."""
        return self.__rmax

    @property
    def rnum(self) -> Optional[int]:
        """int or None: The number of values used for the r_ij and r_ik spacings."""
        return self.__rnum

    @property
    def thetamin(self) -> Optional[float]:
        """float or None: The minimum value used for the theta angles."""
        return self.__thetamin

    @property
    def thetamax(self) -> Optional[float]:
        """float or None: The maximum value used for the theta angles."""
        return self.__thetamax

    @property
    def thetanum(self) -> Optional[int]:
        """int or None: The number of values used for the theta angles."""
        return self.__thetanum

    @property
    def df(self) -> pd.DataFrame:
        """pandas.Dataframe : The cluster coordinates and energies."""
        return self.__df

    @property
    def symbols(self) -> Optional[list]:
        """list or None: the atomic symbols associated with the three atoms"""
        return self.__symbols
    
    @symbols.setter
    def symbols(self, value: Union[str, list]):
        
        if value is not None:
            value = aslist(value)
            if len(value) != 1 and len(value) != 3:
                raise ValueError('Number of symbols must be 1 or 3')
        
        self.__symbols = value

    def model(self,
              model: Union[str, io.IOBase, DM, None] = None,
              length_unit: str = 'angstrom',
              energy_unit: str = 'eV') -> Optional[DM]:
        """
        Loads or generates a bond angle map data model.

        Note: Generating data models is currently limited to regular values,
        i.e. ones which the coordinates correspond to embedded loops with
        r_ij iterating in the outside loop, r_ik in the middle loop and 
        theta in the inside loop.

        Parameters
        ----------
        model : str, file-like object or DataModelDict, optional
            The data model content or file containing the bond angle map data.
            If given, the content will be read in and set to the current object.
            If not given, then a data model will be returned for the object.
        length_unit : str, optional
            The unit of length to save the rmin and max values in when
            generating a data model.  Default is 'angstrom'.
            value
        energy_unit : str, optional
            The unit of energy to save the energy values in when generating a
            data model.  Default value is 'eV'.
        
        Returns
        -------
        DataModelDict.DataModelDict
            The data model containing the bond angle map coordinate information
            and measured energies.  Only returned if model is not given as a
            parameter.

        Raises
        ------
        ValueError
            If the data is irregular, i.e. coordinates do not conform to
            embedded loops with r_ij in the outer loop, r_ik in the middle loop
            and theta in the inside loop.
        """
        # Read in a data model
        if model is not None:
            cluster = DM(model).find('bond-angle-map')
            
            rmin = uc.value_unit(cluster['minimum-r-spacing'])
            rmax = uc.value_unit(cluster['maximum-r-spacing'])
            rnum = int(cluster['number-of-r-spacings'])

            thetamin = float(cluster['minimum-angle'])
            thetamax = float(cluster['maximum-angle'])
            thetanum = int(cluster['number-of-angles'])

            energy = uc.value_unit(cluster['energy'])

            self.set(energy=energy, rmin=rmin, rmax=rmax, rnum=rnum, 
                     thetamin=thetamin, thetamax=thetamax, thetanum=thetanum)
        
        else:
            if self.rnum is None:
                raise ValueError('model does not support irregular measurements')
            
            model = DM()
            model['bond-angle-map'] = cluster = DM()
            
            cluster['minimum-r-spacing'] = uc.model(self.rmin, length_unit)
            cluster['maximum-r-spacing'] = uc.model(self.rmax, length_unit)
            cluster['number-of-r-spacings'] = self.rnum

            cluster['minimum-angle'] = self.thetamin
            cluster['maximum-angle'] = self.thetamax
            cluster['number-of-angles'] = self.thetanum

            cluster['energy'] = uc.model(self.df.energy, energy_unit)

            return model

    def set(self,
            rmin: Optional[float] = None,
            rmax: Optional[float] = None,
            rnum: Optional[int] = None,
            thetamin: Optional[float] = None,
            thetamax: Optional[float] = None,
            thetanum: Optional[int] = None,
            r_ij: Optional[npt.ArrayLike] = None,
            r_ik: Optional[npt.ArrayLike] = None,
            theta: Optional[npt.ArrayLike] = None,
            energy: Optional[npt.ArrayLike] = None):
        """
        Sets the bond angle coordinates and the associated energies, if given.

        Parameters
        ----------
        energy : array-like, optional
            All measured energies.  If r_ij, r_ik and theta are given then
            all should be the same length.  If the range parameters are given
            then the length should be thetanum*rnum*rnum.  If not given, then
            a new array of nan values will be constructed.
        rmin : float, optional
            The minimum value used for the r_ij and r_ik spacings.
        rmax : float, optional
            The maximum value used for the r_ij and r_ik spacings.
        rnum : float, optional
            The number of values used for the r_ij and r_ik spacings.
        thetamin : float, optional
            The minimum value used for the theta angles.
        thetamax : float, optional
            The maximum value used for the theta angles.
        thetanum : float, optional
            The number of values used for the theta angles.
        r_ij : array-like, optional
            All r_ij values used.  If given, the lengths of r_ij, r_ik and
            theta need to be the same.
        r_ik : array-like, optional
            All r_ik values used.  If given, the lengths of r_ij, r_ik and
            theta need to be the same.
        theta : array-like, optional
            All theta values used.  If given, the lengths of r_ij, r_ik and
            theta need to be the same.
        energy : array-like, optional
            All measured energies.  If r_ij, r_ik and theta are given then
            all should be the same length.  If the coordinate range parameters
            are given, then the energies should be of length rnum*rnum*thetanum
            and ordered to correspond to three embedded loops with r_ij
            iterating in the outside loop, r_ik in the middle and theta in the
            inside.  If energy is not given, then all values will initially be
            set to np.nan.
        """

        # Set coordinate values based on ranges
        if rmin is not None:
            if r_ij is not None or r_ik is not None or theta is not None:
                raise ValueError('range parameters and explicit values cannot be mixed')
            try:
                rvals = np.linspace(rmin, rmax, rnum)
                tvals = np.linspace(thetamin, thetamax, thetanum)
            except Exception as e:
                raise ValueError('Invalid range parameters') from e

            # Set range parameters as class properties
            self.__rmin = rmin
            self.__rmax = rmax
            self.__rnum = rnum
            self.__thetamin = thetamin
            self.__thetamax = thetamax
            self.__thetanum = thetanum

            # Generate the input parameters
            r_ij, r_ik, theta = np.meshgrid(rvals, rvals, tvals, indexing='ij')
            r_ij = r_ij.flatten()
            r_ik = r_ik.flatten()
            theta = theta.flatten()

        # Explicitly set coordinate values
        else:
            try:
                assert rmax is None and rnum is  None
                assert thetamin is None and thetamax is None and thetanum is None
            except AssertionError as e:
                raise ValueError('range parameters and explicit values cannot be mixed') from e
            try:
                if len(r_ij) != len(r_ik) or len(r_ij) != len(theta):
                    raise ValueError('Equal numbers of r_ij, r_ik, and theta values must be given')
            except Exception as e:
                raise ValueError('Invalid parameters') from e

            r_ij = np.asarray(r_ij)
            r_ik = np.asarray(r_ik)
            theta = np.asarray(theta)
            
            # Try to extract range parameters
            rmin = r_ij.min()
            rmax = r_ij.max()
            rnum = len(np.unique(r_ij))

            thetamin = theta.min()
            thetamax = theta.max()
            thetanum = len(np.unique(theta))

            try:
                assert len(r_ij) == thetanum * rnum * rnum
                rvals = np.linspace(rmin, rmax, rnum)
                tvals = np.linspace(thetamin, thetamax, thetanum)
                r_ij_test, r_ik_test, theta_test = np.meshgrid(rvals, rvals, tvals, indexing='ij')
                assert np.allclose(r_ij, r_ij_test.flatten())
                assert np.allclose(r_ik, r_ik_test.flatten())
                assert np.allclose(theta, theta_test.flatten())
            except:
                # Set range parameters as None to indicate not correctly ordered
                self.__rmin = None
                self.__rmax = None
                self.__rnum = None
                self.__thetamin = None
                self.__thetamax = None
                self.__thetanum = None
            else:
                # Set range parameters
                self.__rmin = rmin
                self.__rmax = rmax
                self.__rnum = rnum
                self.__thetamin = thetamin
                self.__thetamax = thetamax
                self.__thetanum = thetanum
        
        # Check energy values
        if energy is None:
            energy = np.full(len(r_ij), np.nan)
        elif len(energy) != len(r_ij):
            raise ValueError('Mismatch between number of energies given and expected')

        # Compute r_jk values
        r_jk = np.sqrt(r_ij**2 + r_ik**2 - r_ij * r_ik * 2 * np.cos(np.radians(theta)))

        # Build DataFrame
        df = {}
        df['r_ij'] = r_ij
        df['r_ik'] = r_ik
        df['r_jk'] = r_jk
        df['theta'] = theta
        df['energy'] = energy
        self.__df = pd.DataFrame(df)

    def itercoords(self) -> Generator[Tuple[float, float, float, float], None, None]:
        """
        Iterates through the three-body coordinates, which can be used as inputs for
        computing energies.

        Yields
        ------
        r_ij : float
            The radial distance between atoms i and j.
        r_ik : float
            The radial distance between atoms i and k.
        r_jk : float
            The radial distance between atoms j and k.
        theta : float
            The angle between i-j and i-k in degrees.
        """
        for i in self.df.index:
            series = self.df.loc[i]
            yield series.r_ij, series.r_ik, series.r_jk, series.theta

    def itersystem(self,
                   symbols: Union[str, list, None] = None,
                   copy: bool = False
                   ) -> Generator[System, None, None]:
        """
        Iterates through the three-body coordinates and returns a System for each.
        Useful for generating configuration files for simulators.  The atom
        coordinates will be set such that atom 0 is at [0,0,0], atom 1 at
        [r_ij,0,0] and atom 2 is in the xy plane based on r_ik and theta.

        Parameters
        ----------
        symbols : str or list, optional
            The element model symbols to assign to the atoms.  Can either be
            one value for all atoms, or three values for each atom individually.
            If not given here, will use the values set during class
            initialization.
        copy : bool, optional
            If False (default), then the yielded system is the same object with
            the coordinates shifted.  If True, each yielded system is a new object.

        Yields
        ------
        atomman.System
            The atomic system containing the three-body cluster.
        """
        # Set symbols
        if symbols is not None:
            self.symbols = symbols 
        symbols = self.symbols

        # Identify box bounds based on r_ij values
        rhi = 3 * self.df.r_ij.max()
        rlo = - rhi
        
        # Identify atypes from symbols
        if symbols is None or len(symbols) == 1:
            atype = np.array([1,1,1])
        elif len(symbols) == 3:
            symbols, atype = np.unique(symbols, return_inverse=True)
        else:
            print(symbols)
            raise ValueError('Invalid symbols somehow...')

        # Copy = True means generate new system each iteration
        if copy:
            for r_ij, r_ik, r_jk, theta in self.itercoords():

                # Build the pos array
                j_x = r_ij
                k_x = r_ik * np.cos(np.radians(theta))
                k_y = r_ik * np.sin(np.radians(theta))
                pos = np.array([[0.0, 0.0, 0.0],
                                [j_x, 0.0, 0.0],
                                [k_x, k_y, 0.0]])

                # Build and yield a new system
                box = Box(xlo=rlo, xhi=rhi, ylo=rlo, yhi=rhi, zlo=-1.0, zhi=1.0)
                atoms = Atoms(atype=atype, pos=pos)
                yield System(atoms=atoms, box=box, symbols=symbols, pbc=[False, False, False])

        # Copy = False means only generate one system and modify pos
        else:
            # Build system with all coordinates at [0,0,0]
            box = Box(xlo=rlo, xhi=rhi, ylo=rlo, yhi=rhi, zlo=-1.0, zhi=1.0)
            atoms = Atoms(atype=atype, pos=np.zeros([3,3]))
            system = System(atoms=atoms, box=box, symbols=symbols, pbc=[False, False, False])
        
            for r_ij, r_ik, r_jk, theta in self.itercoords():
                
                # Modify the three non-zero coordinates
                system.atoms.pos[1,0] = r_ij
                system.atoms.pos[2,0] = r_ik * np.cos(np.radians(theta))
                system.atoms.pos[2,1] = r_ik * np.sin(np.radians(theta))

                yield system
            
    def save_table(self,
                   filename: str,
                   include_header: bool = True):
        """
        Saves a tabulated representation of the coordinates and energy values to a file.

        Parameters
        ----------
        filename : str
            The path to the file where the table will be saved.
        include_header : bool
            If True (default) then header comments will be listed at the top of the file.
        """
        with open(filename, 'w', encoding='UTF-8') as f:

            if include_header:
                emin = self.df.energy.min()

                # Create the header comment lines
                f.write(f'# Comment: this is a file containing an r12, r13, theta - energy-block E(r12, r13, theta) E_min={emin:18.14} eV\n')
                f.write('# File format: After 9 comment lines (starting with #) there are three lines with (angle in degrees):\n')
                f.write('# r12_min, r12_max, n_bins_r12; r13_min, r13_max, n_bins_r13, theta_min, theta_max, n_bins_theta followed by\n')
                f.write('# the data block in the format index_r12, index_r13_ index_theta, E(i_r12,i_r13,i_theta) [eV] one per line.\n')   
                f.write('# Conversion from index to value: val = val_min + (index-1)*(val_max - val_min)/(n_bins-1)\n')
                f.write(f'# file created by xxx via code atomman on date {datetime.date.today}\n')
                #f.write(f'# This is an example for 3-body MD-potential C-W; Reference: J. Jones, CPPC 34, p.123-432 (2019)\n')
                #f.write(f'# Atom 1: C, Atom 2: W, Atom 3: W\n')
                #f.write(f'# Version 0.2 (2021-02-15) by U v. Toussaint (IPP)\n')
                f.write(f'{self.rmin:18.14} {self.rmax:18.14} {self.rnum}\n')
                f.write(f'{self.rmin:18.14} {self.rmax:18.14} {self.rnum}\n')
                f.write(f'{self.thetamin:18.14} {self.thetamax:18.14} {self.thetanum}\n')

            l = 0
            for i in range(self.rnum):
                for j in range(self.rnum):
                    for k in range(self.thetanum):
                        f.write(f'{i+1:6} {j+1:6} {k+1:6} {self.df.energy.values[l]:18.14}\n')
                        l += 1

    def load_table(self,
                   filename: str,
                   length_unit: str = 'angstrom',
                   energy_unit: str = 'eV'):
        """
        Loads a tabulated representation of the coordinates and energy values
        from a file.

        Parameters
        ----------
        filename : str
            The path to the file where the tabulated data is stored.
        length_unit : str, optional
            The units of length used in the file.  Default value is 'angstrom'.
        energy_unit : str, optional
            The units of energy used in the file.  Default value is 'eV'.
        """

        with open(filename, encoding='UTF-8') as f:
            lines = f.readlines()

        count = 0
        energies = []
        i = 1
        j = 1
        k = 1
        for line in lines:
            terms = line.split()
            if line.strip()[0] == '#' or len(terms) == 0:
                continue
            
            # Get r_ij min, max, num 
            if count == 0:
                rmin = float(terms[0])
                rmax = float(terms[1])
                rnum = int(terms[2])
                count += 1
            
            # Check r_ik min, max, num 
            elif count == 1:
                assert np.isclose(rmin, float(terms[0])), 'only identical rij and rik ranges currently supported'
                assert np.isclose(rmax, float(terms[1])), 'only identical rij and rik ranges currently supported'
                assert np.isclose(rnum, int(terms[2])), 'only identical rij and rik ranges currently supported'
                count += 1

            # Get theta min, max, num 
            elif count == 2:
                thetamin = float(terms[0])
                thetamax = float(terms[1])
                thetanum = int(terms[2])
                count += 1
                energies = np.empty(rnum*rnum*thetanum)
            
            # Get energies
            else:
                i = int(terms[0]) - 1
                j = int(terms[1]) - 1
                k = int(terms[2]) - 1
                index = k + j * thetanum + i * rnum * thetanum
                energies[index] = float(terms[3])
        
        # Convert units 
        rmin = uc.set_in_units(rmin, length_unit)
        rmax = uc.set_in_units(rmax, length_unit)  
        energies = uc.set_in_units(energies, energy_unit)
        
        self.set(rmin=rmin, rmax=rmax, rnum=rnum, thetamin=thetamin,
                 thetamax=thetamax, thetanum=thetanum, energy=energies)

    def pdf(self,
            nbins: int = 301,
            energymin: float = -15.0,
            energymax: float = 15.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the probability density function for the energy
        
        Parameters
        ----------
        nbins : int, optional
            The number of histogram bins to use.  Default value is 301.
        energymin : float, optional
            The minimum energy bound to consider.  Default value is -15.0.
        energymax : float, optional
            The maximum energy bound to consider.  Default value is 15.0.

        Returns
        -------
        pdf : numpy.NDArray
            The probability density function associated with each bin.
        centers : numpy.NDArray
            The center values for each bin.
        """

        hist, edges = np.histogram(self.df.energy, bins=nbins, range=(energymin, energymax))

        # Divide the historgram count by total number of measurements
        pdf = hist/len(self.df)

        # Average the bin edges to get the bin centers
        centers = (edges[:-1] + edges[1:]) / 2

        return pdf, centers

    def cumulative_pdf(self, 
                       nbins: int = 301,
                       energymin: float = -15.0,
                       energymax: float = 15.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the cumulative probability density function for the energy.
        
        Parameters
        ----------
        nbins : int, optional
            The number of histogram bins to use.  Default value is 301.
        energymin : float, optional
            The minimum energy bound to consider.  Default value is -15.0.
        energymax : float, optional
            The maximum energy bound to consider.  Default value is 15.0.

        Returns
        -------
        cum_pdf : numpy.NDArray
            The cumulative probability density function associated with each bin.
        centers : numpy.NDArray
            The center values for each bin.
        """

        # Get pdf and centers in the range
        pdf, centers = self.pdf(nbins=nbins, energymin=energymin, energymax=energymax)

        # Calculate cumulative pdf below energymin
        shift = np.sum(self.df.energy < energymin) / len(self.df)

        # Calculate the cumulative sum of pdf and apply the shift
        cum_pdf = np.cumsum(pdf) + shift

        return cum_pdf, centers

    def plot_pdf(self,
                 nbins: int = 301,
                 energymin: float = -15.0,
                 energymax: float = 15.0,
                 matplotlib_axes: Optional[plt.axes] = None,
                 **kwargs) -> Optional[plt.figure]:
        """
        Generates a plot of the probability density function of the energy.

        Parameters
        ----------
        nbins : int, optional
            The number of histogram bins to use.  Default value is 301.
        energymin : float, optional
            The minimum energy bound to consider.  Default value is -15.0.
        energymax : float, optional
            The maximum energy bound to consider.  Default value is 15.0.
        matplotlib_axes : matplotlib.Axes.axes, optional, optional
            An existing plotting axis to add the pdf plot to.  If not given,
            a new figure object will be generated.
        **kwargs : any, optional
            Any additional key word arguments will be passed to
            matplotlib.pyplot.figure for generating a new figure object (if
            axis is not given).
        
        Returns
        -------
        matplotlib.Figure
            The generated figure.  Not returned if matplotlib_axes is given.
        """
        # Get pdf and centers in the range
        pdf, centers = self.pdf(nbins=nbins, energymin=energymin, energymax=energymax)

        # Initial plot setup and parameters
        if matplotlib_axes is None:
            fig = plt.figure(**kwargs)
            ax1 = fig.add_subplot(111)
        else:
            ax1 = matplotlib_axes
            
        ax1.plot(centers, pdf)
        ax1.set_xlim(energymin, energymax)

        ax1.set_xlabel('Potential Energy [eV]')
        ax1.set_ylabel('pdf(E)')

        if matplotlib_axes is None:
            return fig

    def plot_cumulative_pdf(self,
                            nbins: int = 301,
                            energymin: float = -15.0,
                            energymax: float = 15.0,
                            matplotlib_axes: Optional[plt.axes] = None,
                            **kwargs) -> Optional[plt.figure]:
        """
        Generates a plot of the cumulative probability density function of the energy.

        Parameters
        ----------
        nbins : int, optional
            The number of histogram bins to use.  Default value is 301.
        energymin : float, optional
            The minimum energy bound to consider.  Default value is -15.0.
        energymax : float, optional
            The maximum energy bound to consider.  Default value is 15.0.
        matplotlib_axes : matplotlib.Axes.axes, optional, optional
            An existing plotting axis to add the pdf plot to.  If not given,
            a new figure object will be generated.
        **kwargs : any, optional
            Any additional key word arguments will be passed to
            matplotlib.pyplot.figure for generating a new figure object (if
            axis is not given).
        
        Returns
        -------
        matplotlib.Figure
            The generated figure.  Not returned if matplotlib_axes is given.
        """
        # Get pdf and centers in the range
        cum_pdf, centers = self.cumulative_pdf(nbins=nbins, energymin=energymin, energymax=energymax)

        # Initial plot setup and parameters
        if matplotlib_axes is None:
            fig = plt.figure(**kwargs)
            ax1 = fig.add_subplot(111)
        else:
            ax1 = matplotlib_axes
            
        ax1.plot(centers, cum_pdf)
        ax1.set_xlim(energymin, energymax)

        ax1.set_xlabel('Potential Energy [eV]')
        ax1.set_ylabel('cumulative pdf(E)')

        if matplotlib_axes is None:
            return fig