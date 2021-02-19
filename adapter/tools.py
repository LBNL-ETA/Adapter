import numpy as np

VOL_UNIT_DENOMINATIONS = ['gal','gal.','gln','gallon','gals','gals.','gallons','m3','m^3','ft3','ft^3']
VOL_UNIT_DENOMINATIONS += [x.title() for x in VOL_UNIT_DENOMINATIONS] + [x.upper() for x in VOL_UNIT_DENOMINATIONS]

ENERGY_UNIT_DENOMINATIONS = ['kwh','kWh','KWh','twh','TWh','mwh','MWh','gwh','GWh','quad','quads','therm','mmbtu','MMBtu','kj','mj']
ENERGY_UNIT_DENOMINATIONS += [x.title() for x in ENERGY_UNIT_DENOMINATIONS] + [x.upper() for x in ENERGY_UNIT_DENOMINATIONS] + ['wh','WH','Wh'] + ['btu','BTU','BTu'] + ['j','J'] # small units go at the end so that 'wh' doesn't get stripped from 'kwh', e.g.

DOLLAR_UNIT_DENOMINATIONS = ['dollars','dols','dol']
DOLLAR_UNIT_DENOMINATIONS += [x.title() for x in DOLLAR_UNIT_DENOMINATIONS] + [x.upper() for x in DOLLAR_UNIT_DENOMINATIONS]
DOLLAR_UNIT_DENOMINATIONS = ['$'] + DOLLAR_UNIT_DENOMINATIONS

TEMP_UNIT_DENOMINATIONS = ['celsius','fahrenheit','kelvin','degF','degC','degK']
TEMP_UNIT_DENOMINATIONS += [x.title() for x in TEMP_UNIT_DENOMINATIONS] + [x.upper() for x in TEMP_UNIT_DENOMINATIONS] + ['C','F','K'] # Excluding lowercase c,f,k 

MASS_UNIT_DENOMINATIONS = ['kg','kilogram','kilo','kilos','tonne','tonnes','tons','ton','gram','gramme','grammes','grams']
MASS_UNIT_DENOMINATIONS += [x.title() for x in MASS_UNIT_DENOMINATIONS] + [x.upper() for x in MASS_UNIT_DENOMINATIONS] + ['g','t']

TIME_UNIT_DENOMINATIONS = ['minute','minutes','min','mins','day','days','hour','hr','hr.','hours','hrs','year','yr','years','yrs','yr.']
TIME_UNIT_DENOMINATIONS += [x.title() for x in TIME_UNIT_DENOMINATIONS] + [x.upper() for x in TIME_UNIT_DENOMINATIONS] + ['h','s']

def convert_units(x,unit_in, unit_out):
    '''
    For converting x, which is in <unit_in> units, to <unit_out> units. Returns a value that represents x in <unit_out> units, maintaining the type of x.
    There is no support for converting unit aliases right now (E.g. 1 J/s = 1 W)

    Inputs:
        x (numeric,pd.Series,np.array): a number or collection of numbers defined in units designated by 'unit_in'. Requires that it can be manipulated with native *, +, and / operators
        unit_in (str):  unit designation of x, can be a quotient designated with '/' or 'per'
        unit_out (str): unit designation of desired representation of x. Can be a quotient designated with '/' or 'per'.

    Outputs:
        type(x): Returns x in the same type, but whose value has been manipulated to correspond to 'unit_out'

    Examples:
        > convert_units(1,'kWh','quad')
        > 3.41214e-12

        > convert_units(1,'$/kwh','$/mwh')
        > 1000

        > convert_units(1,'$/1000 gal','million $/1000 m3') # or convert_units(1,'$/1000 gallons','mln $/1000 m^3')
        > 0.000264172

        > convert_units(32,'F','C')                         # or convert_units(32,'fahrenheit','celsius')
        > 0.0

        > price = pd.Series([.15,.16,.17])
        > convert_units(price,'$/kwh','thousand $/mmbtu')
        > 0     0.043961
          1     0.046891
          2     0.049822
          dtype: float64
    '''
    
    parsed_in, parsed_out = _parse_units(unit_in), _parse_units(unit_out)

    if (parsed_in["denominator"][1] is not None and parsed_out["denominator"][1] is None) or (parsed_in["denominator"][1] is None and parsed_out["denominator"][1] is not None):
        raise Exception(f"Right now convert_units does not support translation between explicit unit quotients and singular unit designations (E.g. J/s and W)")

    if parsed_in["denominator"][1] is None and parsed_out["denominator"][1] is None:
        return _converter(x,parsed_in['numerator'][1],parsed_out['numerator'][1]) * (parsed_in['numerator'][0]/parsed_out['numerator'][0])
    
    # Convert numerator to numerator  X <B> = X <A> * [<B>/<A>]
    # Convert denominator to denominator (1/ X <B>) = (1 / X<A>) * [<A>/<B>]
    # Convert amounts:
    #       numerator:      N <B> = M <B> * [N/M]
    #       denominator:    (1/N <B>) = (1/M <B>) * [M/N]
    if parsed_in['denominator'][1].title() in TEMP_UNIT_DENOMINATIONS or parsed_out['denominator'][1].title() in TEMP_UNIT_DENOMINATIONS:
        raise Exception(f"Temperature (given {parsed_in['denominator'][1]} and {parsed_out['denominator'][1]}) in denominator is undefined behavior.")
    return _converter(x,parsed_in['numerator'][1],parsed_out['numerator'][1]) * _converter(1,parsed_out['denominator'][1],parsed_in['denominator'][1]) * (parsed_in['numerator'][0]/parsed_out['numerator'][0]) * (parsed_out['denominator'][0]/parsed_in['denominator'][0])

def _parse_units(given_unit):
    '''
    For parsing a generic unit represented as a string, for example 'kwh','1000 $', or '$/MMBtu'

    Inputs:
        given_unit (str): String form of generic unit, which may be a quotient designated with "/" or "per".

    Returns:
        dict:   'numerator' and 'denominator' keys to specify amount of base unit and base unit. If there is no denominator, that key is associated to (1,None)

    Example:    
    For turning generic units (N_x <x> / N_y <y>) into normalized objects. When a non-quotient product is given, will return (1,None) as denominator.
    {
        'numerator':(amount,unit),
        'denominator':(amount,unit)
    }
    '''
    given_unit = given_unit.strip()
    for delineator in ["/","per"]:
        if delineator in given_unit:
            numerator, denominator = given_unit.split(delineator)
            return {
                'numerator': _parse_single_unit(numerator),
                'denominator': _parse_single_unit(denominator)
            }
    
    return {
        'numerator': _parse_single_unit(given_unit),
        'denominator':(1,None)
    }

def _parse_single_unit(given_unit):
    '''
    For turning something like "1000 gal" into (1000,'gal'), and 'kwh' into (1,'kwh')

    Returns:
        tuple:     A two-tuple with the 0th index being the amount of the base unit (int), and the 1st index being the base unit (str)
    '''
    unit_denominations = ENERGY_UNIT_DENOMINATIONS +\
        VOL_UNIT_DENOMINATIONS + \
        DOLLAR_UNIT_DENOMINATIONS + \
        TEMP_UNIT_DENOMINATIONS + \
        MASS_UNIT_DENOMINATIONS + \
        TIME_UNIT_DENOMINATIONS

    for u in unit_denominations:
        if given_unit.strip().endswith(u):
            amount = given_unit.strip().strip(u).strip().replace(',','') # '1,000 gallons' -> '1000' or 'kwh' -> '' or 'million $' -> 'million'
            if not amount:
                amount = 1 # e.g. original unit was given as "kwh" -> means 1 kwh
            elif amount.isdigit():
                amount = int(amount) # E.g. '1000' -> 1000
            else:
                amount = _string_multiplier(amount) # E.g. 'billion' -> 1e9
                
            return amount, u.lower() # (1000,'gal')

def _converter(x, unit_in, unit_out):
    '''Function to convert between different units.
    Factors come from ASHRAE retrieved Feb 19, 2021 
    https://www.ashrae.org/technical-resources/ashrae-handbook/the-si-guide
    
    Args:
        x (numeric, pd.Series, np.array): value to convert. Must be compatible with native *, + operations
        unit_in (str): unit in which `x` is given
        unit_out (str): unit to which `x` should be converted
    
    Returns:
        `unit of x`: converted value
    '''
    kwh = 1.    # Use kwh as the base
    mj = 3.6            # 1 wh = 3600 j ->      1000 wh = 3600 * 1000 / 1e6 (million joules)
    btu = 3.41214e3     # 1 wh = 3.41214 btu -> 1000 wh = 3.41214*1000 btu
    energy_unit_dict = {
        'quad':     btu/1e15,
        'quads':    btu/1e15,
        'mmbtu':    btu/1e6,
        'btu':      btu,
        'twh':      kwh/1.e9,
        'gwh':      kwh/1.e6,
        'mwh':      kwh/1.e3,
        'kwh':      kwh,
        'wh':       kwh*1.e3,
        'mj':       mj,
        'kj':       mj*1e3,
        'j':        mj*1e6,
        'therm':    105.5/mj,       # 1 MJ = 105.5 therm (ASHRAE)
        }
    
    gal = 1.    # Use gallon as base unit
    m3, ft3 = 0.0037854, 0.13368
    vol_unit_dict = {
        'm3':           m3,
        'm^3':          m3,
        'cubic meter':  m3,
        'cubic meters': m3,
        'cubic feet':   ft3,
        'cubic ft':     ft3,
        'ft3':          ft3,
        'ft^3':         ft3,
        'gal':          gal,
        'gals':         gal,
        'gallon':       gal,
        'gallons':      gal,
    }

    dollar = 1.  # Use dollar as the base
    cent = 100.
    dol_unit_dict = {
        # This should only ever hold designations for US currency. Not meant to convert currency. No £, €, ¥, etc. 
        '$':        dollar,
        'dollars':  dollar,
        'dol':      dollar,
        'dols':     dollar,
        'cents':    cent,
        '¢':        cent,
    }

    # (freezing point of water at atmospheric pressure, boiling point of water at atmospheric pressure)
    celsius =       (0., 100.)
    fahrenheit =    (32., 212.)
    kelvin =        (273.15, 373.15)
    temp_unit_dict = {
        'c':            celsius,
        'f':            fahrenheit,
        'k':            kelvin,
        'celsius':      celsius,
        'fahrenheit':   fahrenheit,
        'kelvin':       kelvin,
    }
    
    kg = 1. # Use kg as base
    gram = 1000. 
    ton = .001
    mass_unit_dict = {
        # NOTE: Imperial notion of "ton" not included, though this is perhaps a bad idea? Unclear.
        'gram':     gram,
        'gramme':   gram,
        'grams':    gram,
        'grammes':  gram,
        'g':        gram,
        'kg':       kg,
        'kilogram': kg,
        'kilo':     kg,
        'kilos':    kg,
        'tonne':    ton,
        'tonnes':   ton,
        'tons':     ton, 
        'ton':      ton,
        't':        ton,
    }

    hour = 1.   # Use hour as base
    minute = 1/60. 
    day = 24.
    year = 365.
    time_unit_dict = {
        'minute':   minute,
        'minutes':  minute,
        'min':      minute,
        'mins':     minute,
        'hour':     hour,
        'hr':       hour,
        'hr.':      hour,
        'hours':    hour,
        'hrs':      hour,
        'day':      day,
        'days':     day,
        'year':     year,
        'yr':       year,
        'years':    year,
        'yrs':      year,
        'yr.':      year,
    }


    conversion_dicts = [energy_unit_dict, vol_unit_dict, dol_unit_dict, temp_unit_dict, mass_unit_dict, time_unit_dict]

    unit_in, unit_out = unit_in.strip().replace('.','').lower(), unit_out.strip().replace('.','').lower()

    for conversion_dict in conversion_dicts:
        if unit_in in conversion_dict.keys() and unit_out in conversion_dict.keys():
            if isinstance(conversion_dict[unit_out],float) and isinstance(conversion_dict[unit_in],float):
                convert = conversion_dict[unit_out]/conversion_dict[unit_in]
                return convert * x
            else:
                in_freeze, in_boil, out_freeze, out_boil = (
                    conversion_dict[unit_in][0],
                    conversion_dict[unit_in][1],
                    conversion_dict[unit_out][0],
                    conversion_dict[unit_out][1],
                )
                # E.g. For Fahrenheit -> C
                # (x - 32) * (5/9) + 0
                # E.g. For K -> Fahrenheit
                # (x - 273.15) * (212 - 32)/(373.15 - 273.15) + 32
                return (x - in_freeze) * (out_boil - out_freeze)/(in_boil - in_freeze) + out_freeze

    return np.nan

def _string_multiplier(string_in):
    string_in = string_in.strip().lower()

    d = {'mil':1e6,
         'mln':1e6,
         'mlns':1e6,
         'mill':1e6,
         'million':1e6,
         'millions':1e6,
         'bil':1e9,
         'bln':1e9,
         'blns':1e9,
         'bill':1e9,
         'billion':1e9,
         'billions':1e9,
         'quadrillion':1e12,
         'thou':1e3,
         'thsnd':1e3,
         'thousand':1e3,
         'thousands':1e3,
         'one':1,
         'ones':1}

    if string_in in d.keys():
        return d[string_in]
    else:
        try:
            out = int(string_in)
            return out
        except:
            raise Exception(f"Quantity '{string_in}' is not recognized as a numerical string.")