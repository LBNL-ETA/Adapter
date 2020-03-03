# Adapter

Data loader from various format such as xlsx, csv, db. Converts all to db and from db to pandas dataframes. Can account for different OSs. It serves analytical tools such as Generic LCC and Shipments with inputs.

## Usage

Please read the [Use cases provided in the Functional Requirements](https://bitbucket.org/eetd-ees/adapter/wiki/Functional%20Requirements) to see how to structure the main input file such that you can fetch either all the data from that file or, in addition to those, fetch data from other input files.

The examples on how to conveniently utilize adapter as your IO tool can be found in [the tests for the `to_python` module](https://bitbucket.org/eetd-ees/adapter/src/master/adapter/tests/test_to_python.py). For example, if
you'd like to load all data as specified in some main input file as a
dictionary of pandas dataframes you would :

```
input_loader = Excel(r'fullpath_to_input_file')
df_of_input_dataframes = input_loader.load()
```

Some test input files are also [provided in that test folder](https://bitbucket.org/eetd-ees/adapter/src/master/adapter/tests/).
