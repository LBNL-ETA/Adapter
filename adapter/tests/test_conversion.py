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

        assert(round(value,8)==1.)

    def test_volume_conversion_fullcircle(self):
        '''
        Take the value 1 and go through all of the unit designations listed for unit conversion. Assert that the result is 1 when converted back to original first unit.
        '''
        value = 1.
        first_unit = VOL_UNIT_DENOMINATIONS[0]
        for (unit_in, unit_out) in zip(VOL_UNIT_DENOMINATIONS[:-1], VOL_UNIT_DENOMINATIONS[1:]):
            value = convert_units(value,unit_in,unit_out)
        
        value = convert_units(value,VOL_UNIT_DENOMINATIONS[-1],first_unit)

        assert(round(value,8)==1.)

    def test_mass_conversion_fullcircle(self):
        '''
        Take the value 1 and go through all of the unit designations listed for unit conversion. Assert that the result is 1 when converted back to original first unit.
        '''
        value = 1.
        first_unit = MASS_UNIT_DENOMINATIONS[0]
        for (unit_in, unit_out) in zip(MASS_UNIT_DENOMINATIONS[:-1], MASS_UNIT_DENOMINATIONS[1:]):
            value = convert_units(value,unit_in,unit_out)
        
        value = convert_units(value,MASS_UNIT_DENOMINATIONS[-1],first_unit)

        assert(round(value,8)==1.)

    def test_energy_conversion_fullcircle(self):
        '''
        Take the value 1 and go through all of the unit designations listed for unit conversion. Assert that the result is 1 when converted back to original first unit.
        '''
        value = 1.
        first_unit = ENERGY_UNIT_DENOMINATIONS[0]
        for (unit_in, unit_out) in zip(ENERGY_UNIT_DENOMINATIONS[:-1], ENERGY_UNIT_DENOMINATIONS[1:]):
            value = convert_units(value,unit_in,unit_out)
        
        value = convert_units(value,ENERGY_UNIT_DENOMINATIONS[-1],first_unit)

        assert(round(value,8)==1.)

    def test_time_conversion_fullcircle(self):
        '''
        Take the value 1 and go through all of the unit designations listed for unit conversion. Assert that the result is 1 when converted back to original first unit.
        '''
        value = 1.
        first_unit = TIME_UNIT_DENOMINATIONS[0]
        for (unit_in, unit_out) in zip(TIME_UNIT_DENOMINATIONS[:-1], TIME_UNIT_DENOMINATIONS[1:]):
            value = convert_units(value,unit_in,unit_out)
        
        value = convert_units(value,TIME_UNIT_DENOMINATIONS[-1],first_unit)

        assert(round(value,8)==1.)