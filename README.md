# Adapter

The `Adapter Python IO` software provides a convenient data table loader from various formats such as `xlsx`, `csv`, `db (sqlite database)`, and `sqlalchemy`. Its main feature is the ability to convert data tables identified in one main and optionally one or more additional input files into `database tables` and `Pandas DataFrames` for downstream usage in any compatible software.

`Adapter` builds upon the existing Python packages that allow for the communication between `Python` and `MS Excel`, as well as `databases` and `csv` files. It provides inbuilt capabilities to specify the output location path, as well as a version identifier for a research code run. 

In addition to the loading capability, an instance of the `Adapter` `IO` object has the write capability. If invoked, all loaded tables are written as either a single `database` or a set of `csv` files, or both.

The purpose of this software is to support the development of research and analytical software through allowing for a simple multi-format IO with versioning and output path specification in the input data itself.

The package is supported on `Windows` and `macOS`, as well as for `Linux` for the utilization without any `xlsx` inputs. 


## Installation

To install the package use:
```
pip install git+https://github.com/LBNL-ETA/Adapter.git@vX.Y.Z
```
where `@X.Y.Z` is optional and represents the tag version. Available tags can be listed using a command `git tag -n` from the repo root folder or one can see them on the github repo.

Alternatively, you may clone the repository and from its root folder run:
```
python setup.py
```

To use the `sqlalchemy` connections to remote server(s) you must edit the example secret file located in `adapter\Secret_example.py` for your database credentials and save it as `adapter\Secret.py`.


## Usage

The examples on how to conveniently utilize adapter as your IO tool can be found in [the tests for the `i_o.py` module](https://github.com/LBNL-ETA/Adapter/blob/master/adapter/tests/test_i_o.py). The same examples are provided below. We assume that the user is running the commands from the repo root folder.

The simplest example of how to use the package is:
```python
from adapter.i_o import IO

input_loader = IO(<fullpath_to_the_main_input_file>)
data = input_loader.load()
```

To automatically convert paths between platforms, for example if you are using a VPN connection to access input data files, use the mapping argument:
```python
from adapter.i_o import IO

input_loader = IO(<fullpath_to_the_main_input_file>, 
                               os_mapping={'win32': 'C:', 'darwin': '/Volumes/A', 'linux': '/media/A'})
data = input_loader.load()
```
where `data` is a dictionary with the following keys:
```python
    'tables_as_dict_of_dfs' - all input tables loaded in python as dictionary of dataframes
    'outpath' - output folder path
    'run_tag' - version + analysis start time

    If one choses to initiate a db at read-in (to add results to the inputs later and have one compiled analysis db):

    'db_path' - database fullpath
    'db_conn' - database connection
```

The input tables may be specified in a single `xlsx`, a `database` file, or a `csv` file, or any combination of those. The `Adapter` standardizes the way to provide inputs from additional files through using either a table named `inputs_from_files`, or by having the string `inputs_from_files` be the start of the main `csv` input file name. The example inputs files, also used in the unit tests, are located in [the test suite folder](https://github.com/LBNL-ETA/Adapter/tree/master/adapter/tests). One can take the test input files as examples and guides on how to structure the main input file such that one can fetch either all the data from the main input file or, in addition to those, fetch data from other input files as specified in the standardized `inputs_from_files` table.

For example, to load all objects defined as data tables and named ranges specified in an excel input file, as a
`Python dictionary` of `Pandas DataFrames`:

```python
path = os.path.join(
    os.getcwd(), r"adapter/tests/test_w_inputs_from_files_table.xlsx"
)

i_o = IO(path)

res = i_o.load()
```

where the `res` output is a dictionary with the same keys as in the example above (`data` dictionary).

An another example especially useful for `Linux` users would be to provide several or all inputs as `csv` files through listing their paths in the main `csv` input file. The `Adapter` can then be used to load all inputs at once. This can be done as follows:
```python
path = os.path.join(
    os.getcwd(), r"adapter/tests/inputs_from_files_vTest.csv"
)
i_o = IO(path)
data_conn = i_o.load()
```

If one of the input tables is named `run_parameters` and contains columns `Output Path` and `Version`, the code will create a unique run tag at the point of data loading and use the provided output path to store any output should the user utilize the writing functionality of `Adapter`.

To write the loaded data into either a single `db` and a number of `csv` files the user can run:
```python
i_o.write(
    type='db&csv',
    data_connection=data_conn
)
```
Depending on the `type` flag, there is an option to writhe only a `db` or a `csv` formatted output.

The `Adapter` also provides an option to only establish a `db` connection to certain tables that are for example large and the user would 
rather query them instead of having them be loaded as a `Pandas DataFrame`. An example of how to provide such information through the input file is 
provided in this example input file [`adapter/tests/inputs_from_files_vTest.csv`](https://github.com/LBNL-ETA/Adapter/blob/master/adapter/tests/inputs_from_files_vTest.csv).

Those with LBNL VPN access can also use [`API documentation`](https://atcd.lbl.gov/source/adapter.html) to explore the functionality of the modules.  


## Testing

As already mentioned in the Usage section, the example input files are [provided in the `test` folder](https://github.com/LBNL-ETA/Adapter/blob/master/adapter/tests/).

To run tests it is recommended to use the [`unittest` framework](https://docs.python.org/3/library/unittest.html). All test modules have names that start with `test_`.

Individual test module can be run with the following command, for example the `test_i_o` module:
```
python -m unittest adapter.tests.test_i_o
```


## Contributing

Guidelines for contributors are provided [here](https://github.com/LBNL-ETA/Adapter/blob/master/contributing.md).


## Acknowledgements

The initial purpose of this software was to serve certain `Python` analytical tools used in DOE Energy Conservation Standards analysis such as Life-Cycle Cost, Shipments, and National Impact Analyses with inputs.


## Developers

The codebase was developed at the Energy Efficiency Standards Department by Milica Grahovac, Youness Bennani, Thomas 
Burke, Katie Coughlin, Mohan Ganeshalingam, Akhil Mathur, Evan Neill, and Akshay Sharma, Zheng He and Lyra Lan.
