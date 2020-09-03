# Adapter

Data loader from various format such as `xlsx`, `csv`, `db`. Converts all to `db` and from `db` to pandas dataframes. Can be used at a variety of OSs. Its purpose is to serve analytical tools such as Generic LCC, Shipments and NIA codebases with inputs.

## Installation

To install the package use:
```
pip install git+https://{your bitbucket username}@bitbucket.org/eetd-ees/adapter.git@v0.1.3
```
To check versions please use `git tag -n`.

## Usage

Please read the [Use cases provided in the Functional Requirements](https://bitbucket.org/eetd-ees/adapter/wiki/Functional%20Requirements) to see how to structure the main input file such that you can fetch either all the data from that file or, in addition to those, fetch data from other input files.

The examples on how to conveniently utilize adapter as your IO tool can be found in [the tests for the `i_o.py` module](https://bitbucket.org/eetd-ees/adapter/src/master/adapter/tests/test_i_o.py). For example, if
you'd like to load all data as specified in some main input file as a
dictionary of pandas dataframes you would type:

```
from adapter.i_o import IO

input_loader = IO(r'fullpath_to_main_input_file')
df_of_input_dataframes = input_loader.load()
```

Some test input files are also [provided in that test folder](https://bitbucket.org/eetd-ees/adapter/src/master/adapter/tests/).
