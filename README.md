# Adapter

The `Adapter` software builds upon the existing Python packages that allow for the communication between `Python` and `MS Excel`, as well as `databases` and `csv` files. `Adapter` provides a convenient data table loader from various format such as `xlsx`, `csv`, and `db`. It has the ability to convert all the data tables that it was pointed to through one or many input files into `db tables` and `pandas dataframes`. It comes with a support for `Windows` and `macOS`. 


## Installation

To install the package use:
```
pip install git+https://{your bitbucket username}@bitbucket.org/eetd-ees/adapter.git@v0.1.3
```
To check versions please use `git tag -n`.


## Usage

The examples on how to conveniently utilize adapter as your IO tool can be found in [the tests for the `i_o.py` module](https://bitbucket.org/eetd-ees/adapter/src/master/adapter/tests/test_i_o.py). The same examples are provided below. We assume that the user is running the commands from the repo root folder.

To load all data tables and named ranges specified in an excel input file as a
dictionary of pandas dataframes:
```
from adapter.i_o import IO

input_loader = IO(r'fullpath_to_main_input_file')
df_of_input_dataframes = input_loader.load()
```

The example inputs files, also used in the unit tests, are located in [the test suite folder](https://bitbucket.org/eetd-ees/adapter/src/master/adapter/tests/). You can look at those to see how to structure the main input file such that you can fetch either all the data from that input file or, in addition to those, fetch data from other input files as specified in the `inputs_from_files` table.

To learn more about how to user the `adapter` software it may be useful to read the [Use cases provided in the Functional Requirements](https://bitbucket.org/eetd-ees/adapter/wiki/Functional%20Requirements).



## Testing

As already mentioned in the Usage section, the example input files are [provided in the `test` folder](https://bitbucket.org/eetd-ees/adapter/src/master/adapter/tests/).

To run tests it is recommended to use the [`unittest` framework](https://docs.python.org/3/library/unittest.html). All test modules have names that start with `test_`.

Individual test module can be run with the following command, for example the `test_i_o` module:
```
python -m unittest adapter.tests.test_i_o
```

## Contributing

Guidelines for contributors are provided [here](https://bitbucket.org/eetd-ees/adapter/src/master/adapter/contributing.md).


## Acknowledgements

The initial purpose of this software was to serve certain `Python` analytical tools used in DOE Energy Conservation Standards analysis such as Life-Cycle Cost, Shipments, and National Impact Analyses with inputs.


## Developers

The codebase was developed at the Energy Efficiency Standards Department by Milica Grahovac, Youness Bennani, Thomas Burke, Akhil Mathur, Evan Neil, and Akshay Sharma.
