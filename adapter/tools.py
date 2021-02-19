import numpy as np

WATER_UNIT_DENOMINATIONS = ['gal','gal.','gln','gallon','gals','gals.','gallons','m3','m^3']
WATER_UNIT_DENOMINATIONS += [x.title() for x in WATER_UNIT_DENOMINATIONS] + [x.upper() for x in WATER_UNIT_DENOMINATIONS]

ENERGY_UNIT_DENOMINATIONS = ['kwh','KWh','twh','TWh','mwh','MWh','gwh','GWh','quad','quads','mmbtu','MMBtu','kj','mj']
ENERGY_UNIT_DENOMINATIONS += [x.title() for x in ENERGY_UNIT_DENOMINATIONS] + [x.upper() for x in ENERGY_UNIT_DENOMINATIONS] + ['wh','WH','Wh'] + ['btu','BTU','BTu'] + ['j','J'] # small units go at the end so that 'wh' doesn't get stripped from 'kwh', e.g.

DOLLAR_UNIT_DENOMINATIONS = ['dollars','dols','dol']
DOLLAR_UNIT_DENOMINATIONS += [x.title() for x in DOLLAR_UNIT_DENOMINATIONS] + [x.upper() for x in DOLLAR_UNIT_DENOMINATIONS]
DOLLAR_UNIT_DENOMINATIONS = ['$'] + DOLLAR_UNIT_DENOMINATIONS

def convert_units(x,unit_in, unit_out):
    '''
    For converting x, which is in <unit_in> units, to <unit_out> units. Returns a value that represents x in <unit_out> units.
    '''
    
    parsed_in, parsed_out = parse_units(unit_in), parse_units(unit_out)

    if (parsed_in["denominator"][1] is not None and parsed_out["denominator"][1] is None) or (parsed_in["denominator"][1] is None and parsed_out["denominator"][1] is not None):
        raise Exception(f"Right now convert_units does not support translation between explicit unit quotients and singular unit designations (E.g. J/s and W)")

    if parsed_in["denominator"][1] is None and parsed_out["denominator"][1] is None:
        return x * unit_converter(1,parsed_in['numerator'][1],parsed_out['numerator'][1]) * (parsed_in['numerator'][0]/parsed_out['numerator'][0])
    # Convert numerator to numerator  X <B> = X <A> * <B>/<A>
    # Convert denominator to denominator (1/ X <B>) = (1 / X<A>) * <A>/<B>
    # Convert amounts:
    #       numerator:      N <B> = M <B> * N/M
    #       denominator:    (1/N <B>) = (1/M <B>) * M/N
    return x * unit_converter(1,parsed_in['numerator'][1],parsed_out['numerator'][1]) * unit_converter(1,parsed_out['denominator'][1],parsed_in['denominator'][1]) * (parsed_in['numerator'][0]/parsed_out['numerator'][0]) * (parsed_out['denominator'][0]/parsed_in['denominator'][0])

def parse_units(given_unit):
    '''
    For turning generic units (N_x <x> / N_y <y>) into normalized objects. When a non-quotient product is given, will return (1,None) as denominator.
    {
        'numerator':(amount,unit),
        'denominator':(amount,unit)
    }
    '''
    given_unit = given_unit.strip()
    for delineator in ["/","per"]:
        if delineator in given_unit.lower():
            numerator, denominator = given_unit.lower().split(delineator)
            return {
                'numerator':parse_single_unit(numerator),
                'denominator':parse_single_unit(denominator)
            }
    
    return {
        'numerator':parse_single_unit(given_unit),
        'denominator':(1,None)
    }

def parse_single_unit(given_unit):
    '''
    For turning something like "1000 gal" into (1000,'gal'), and 'kwh' into (1,'kwh')
    '''
    unit_denominations = ENERGY_UNIT_DENOMINATIONS + WATER_UNIT_DENOMINATIONS + DOLLAR_UNIT_DENOMINATIONS

    for u in unit_denominations:
        if given_unit.strip().endswith(u):
            amount = given_unit.strip().strip(u).strip().replace(',','') # '1,000 gal' -> '1000' or 'kwh' -> ''
            if not amount:
                amount = 1 # e.g. original unit was given as "kwh" -> means 1 kwh
            elif amount.isdigit():
                amount = int(amount) # E.g. '1000' -> 1000
            else:
                amount = string_multiplier(amount) # E.g. 'billion' -> 1e9
                
            return amount, u.lower() # 'MMBtu' -> 'mmbtu'

def unit_converter(x, unit_in, unit_out):
    '''Function to convert between different units.
    
    Args:
        x (int, float, long): value to convert
        unit_in (str): unit in which `x` is given
        unit_out (str): unit in which `x` should be converted
    
    Returns:
        `unit of x`: converted value
    '''
    energy_unit_dict = {
        'wh': 1e3,
        'kwh': 1, # kwh -> quad with 3.4095106405145E-12
        'twh': 1e-9,
        'mwh': 1e-3,
        'gwh': 1e-6,
        'quad': 3.4095106405145E-12,#3.412e-12,
        'quads': 3.4095106405145E-12,#3.412e-12,
        'btu': 3412.14,
        'mmbtu': 0.0034095106405145, # mmbtu -> quad with 10^-9
        'j': 3.6e6,
        'kj': 3.6e3,
        'mj':3.6
        }

    vol_unit_dict = {
        'gal': 1,
        'gals': 1,
        'gallons': 1,
        'm3': 1/264.172,
        'm^3': 1/264.172,
        'cubic meter': 1/264.172,
        'cubic meters': 1/264.172,
        'cubic feet': 1/7.48052,
        'cubic ft': 1/7.48052,
        'ft3': 1/7.48052,
        'ft^3': 1/7.48052,
    }

    dol_unit_dict = {
        '$':1,
        'dollars':1,
        'dol':1,
        'dols':1,
    }
    
    conversion_dicts = [energy_unit_dict, vol_unit_dict, dol_unit_dict]

    unit_in, unit_out = unit_in.strip().replace('.','').lower(), unit_out.strip().replace('.','').lower()

    convert = np.nan
    for conversion_dict in conversion_dicts:
        if unit_in in conversion_dict.keys() and unit_out in conversion_dict.keys():
            convert = conversion_dict[unit_out]/conversion_dict[unit_in]
    
    return convert * x

def string_multiplier(string_in):
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
        raise Exception(f"Quantity '{string_in}' is not recognized as a numerical string.")