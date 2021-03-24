import unittest

import numpy as np

from adapter.tools import convert_units
from adapter.tools import VOL_UNIT_DENOMINATIONS, ENERGY_UNIT_DENOMINATIONS, DOLLAR_UNIT_DENOMINATIONS, TEMP_UNIT_DENOMINATIONS, MASS_UNIT_DENOMINATIONS, TIME_UNIT_DENOMINATIONS

class ConversionTests(unittest.TestCase):

    def test_temperature_conversion_fullcircle(self):
        '''
        Take the value 1 and go through all of the unit designations listed for unit conversion. Assert that the result is 1 when converted back to original first unit.
        '''
        value = 1.
        first_unit = TEMP_UNIT_DENOMINATIONS[0]
        for (unit_in, unit_out) in zip(TEMP_UNIT_DENOMINATIONS[:-1], TEMP_UNIT_DENOMINATIONS[1:]):
            value = convert_units(value,unit_in,unit_out)
        
        value = convert_units(value,TEMP_UNIT_DENOMINATIONS[-1],first_unit)

        assert(round(value,9)==1.)

    def test_volume_conversion_fullcircle(self):
        '''
        Take the value 1 and go through all of the unit designations listed for unit conversion. Assert that the result is 1 when converted back to original first unit.
        '''
        value = 1.
        first_unit = VOL_UNIT_DENOMINATIONS[0]
        for (unit_in, unit_out) in zip(VOL_UNIT_DENOMINATIONS[:-1], VOL_UNIT_DENOMINATIONS[1:]):
            value = convert_units(value,unit_in,unit_out)
        
        value = convert_units(value,VOL_UNIT_DENOMINATIONS[-1],first_unit)

        assert(round(value,9)==1.)

    def test_mass_conversion_fullcircle(self):
        '''
        Take the value 1 and go through all of the unit designations listed for unit conversion. Assert that the result is 1 when converted back to original first unit.
        '''
        value = 1.
        first_unit = MASS_UNIT_DENOMINATIONS[0]
        for (unit_in, unit_out) in zip(MASS_UNIT_DENOMINATIONS[:-1], MASS_UNIT_DENOMINATIONS[1:]):
            value = convert_units(value,unit_in,unit_out)
        
        value = convert_units(value,MASS_UNIT_DENOMINATIONS[-1],first_unit)

        assert(round(value,9)==1.)

    def test_energy_conversion_fullcircle(self):
        '''
        Take the value 1 and go through all of the unit designations listed for unit conversion. Assert that the result is 1 when converted back to original first unit.
        '''
        value = 1.
        first_unit = ENERGY_UNIT_DENOMINATIONS[0]
        for (unit_in, unit_out) in zip(ENERGY_UNIT_DENOMINATIONS[:-1], ENERGY_UNIT_DENOMINATIONS[1:]):
            value = convert_units(value,unit_in,unit_out)
        
        value = convert_units(value,ENERGY_UNIT_DENOMINATIONS[-1],first_unit)

        assert(round(value,9)==1.)

    def test_time_conversion_fullcircle(self):
        '''
        Take the value 1 and go through all of the unit designations listed for unit conversion. Assert that the result is 1 when converted back to original first unit.
        '''
        value = 1.
        first_unit = TIME_UNIT_DENOMINATIONS[0]
        for (unit_in, unit_out) in zip(TIME_UNIT_DENOMINATIONS[:-1], TIME_UNIT_DENOMINATIONS[1:]):
            value = convert_units(value,unit_in,unit_out)
        
        value = convert_units(value,TIME_UNIT_DENOMINATIONS[-1],first_unit)

        assert(round(value,9)==1.)

    def test_energy_conversions(self):
        '''
        Ensure that a selection of units are being converted correctly to several different common output units
        '''
        value = 1
        unit_in = 'kwh'
        
        assert(convert_units(value, unit_in, 'quads')==3.41214/1e12) # from ASHRAE, the value that should used by our conversion tools
        assert(convert_units(value, unit_in, 'twh')==1e-9)
        assert(convert_units(value, unit_in, 'gwh')==1e-6)
        assert(convert_units(value, unit_in, 'mwh')==1e-3)

        value = 1
        unit_in = 'MJ'

        self.assertAlmostEqual(convert_units(value,unit_in,'therms'),value/105.5,17) # from ASHRAE: 1 therm = 105.5 MJ

    def test_volume_conversions(self):
        '''
        Ensure that 1 gallon is being converted correctly to several different common volume (water) units
        '''
        value = 1
        unit_in = 'gal'

        assert(convert_units(value, unit_in, 'billion gallons')==1e-9)
        assert(convert_units(value, unit_in, 'million gallons')==1e-6)
        assert(convert_units(value, unit_in, 'm3')==0.0037854)
        assert(convert_units(value, unit_in, 'ft3')==0.13368)

    def test_temp_conversions(self):
        '''
        Ensure that freezing and boiling point conversions are correct
        '''
        value = 0.
        unit_in = 'C'

        assert(convert_units(value, unit_in, 'F')==32.)
        assert(convert_units(value, unit_in, 'K')==273.15)

        value = 100.
        unit_in = 'C'

        assert(convert_units(value, unit_in, 'F')==212.)
        assert(convert_units(value, unit_in, 'K')==373.15)

        value = 212.
        unit_in = 'F'

        assert(convert_units(value, unit_in, 'C')==100.)
        assert(convert_units(value, unit_in, 'K')==373.15)

        value = 32.
        unit_in = 'F'

        assert(convert_units(value, unit_in, 'C')==0.)
        assert(convert_units(value, unit_in, 'K')==273.15)

    def test_mass_conversions(self):
        '''
        Ensure that mass conversions are exactly as expected
        '''
        value = 1.
        unit_in = 'kg'

        assert(convert_units(value, unit_in, 'short ton')==.001/.907184)
        assert(convert_units(value, unit_in, 'long ton')==.001/1.016046)
        assert(convert_units(value, unit_in, 'ton')==.001)

    def test_time_conversions(self):
        '''
        Ensure that time conversions are as expected
        '''
        value = 1.
        unit_in = 'day'

        assert(convert_units(value,unit_in,'hours')==24)
        assert(convert_units(value,unit_in,'seconds')==24*3600)
        assert(convert_units(value,unit_in,'year')==1/365)


    def test_ashrae_handbook(self):
        '''
        Test every relevant conversion listed in the ASHRAE handbook
        Precisions are about as best as can be gathered from combining the listed ASHRAE conversion factors.

        Some conversions are altered to be translatable by the code (E.g instead of 'btu/h' to 'W', 'btu/h' to 'J/s')

        In general, ft^3 -> m^3 conversions are the poorest (~.1% off when in the denominator), though it may only have to do with the choice of gallons as a central unit.
        Some of these conversions have been excluded, but should be re-introduced if they become part of regular use.
        '''

        assert(abs(convert_units(1,'Btu','J') -  1055.056)/1055.056 < 1e-5)            # ("International Table" listing rather than thermochemical)
        assert(abs(convert_units(1,'Btu/ft^3','J/m^3') -  37258.951)/37258.951 < 1e-5)
        assert(abs(convert_units(1,'Btu/gal','J/m^3') -  278717.1765)/278717.1765 < 1e-5)
        assert(abs(convert_units(1,'Btu/h','J/sec') -  0.2930711)/0.2930711 < 1e-5)
        assert(abs(convert_units(1,'Btu/lb','kJ/kg') -  2.326)/2.326 < 1e-5)

        assert(abs(convert_units(1,'gal','liter') - 3.785412)/3.785412 < 1e-5)
        assert(abs(convert_units(1,'ft^3','liter') - 28.316846)/28.316846 < 1e-5)
        assert(abs(convert_units(1,'ft^3','m^3') - .02832)/.02832 < 1e-3)

        assert(abs(convert_units(1,'gal/min','liter/sec') - 0.0631)/0.0631 < 1e-3)

        assert(abs(convert_units(1,'kwh','MJ') - 3.60)/3.60 < 1e-5)

        assert(abs(convert_units(1,'litre','m^3') - .001)/.001 < 1e-5)

        assert(abs(convert_units(1,'lb','kg') -  .453592)/.453592 < 1e-5)

        assert(abs(convert_units(1,'lb/h','kg/sec') - 0.000126)/.000126 < 1e-4)
        assert(abs(convert_units(1,'lb/min','kg/sec') - 0.007559)/.007559 < 1e-3)

        assert(abs(convert_units(1,'quad','EJ') - 1.055)/1.055 < 1e-4)

        assert(abs(convert_units(1,'therm','MJ') - 105.5)/105.5 < 1e-5)

        assert(abs(convert_units(1,'short ton','t') - 0.907184)/0.907184 < 1e-5)
        assert(abs(convert_units(1,'long ton','t') - 1.0160046)/1.0160046 < 1e-4)
        