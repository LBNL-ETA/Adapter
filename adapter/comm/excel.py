# -*- coding: utf-8 -*-
"""
Initial version created and documented by Youness Bennani.
"""

import xlwings as xw
import pandas as pd
import re
from glob import glob
from functools import reduce

import sys


class Name(xw.main.Name):
    """Class used in the definition of the class ```Names```."""

    def expand(self):
        create_named_range(self.wb, self, resize=True)

    @property
    def wb(self):
        full_address = str(self.refers_to_range)
        wb_name = re.search(r"\[(.*)\]", full_address).groups()[0]
        wb = Book(wb_name)
        return wb


class Names(xw.main.Names):
    """Class used in the definition of the class ```Book```."""

    def __call__(self, name_or_index):
        return Name(impl=self.impl(name_or_index))

    def add(self, name, **kwargs):
        return Name(create_named_range(self.wb, name, **kwargs).name)


class Table(object):
    """Class used in the definition of the class ```Book```."""

    def __init__(self, name, refers_to, wb=None):
        self.name = name
        if not wb:
            wb = xw.apps.active.books.active
        self.wb = wb
        sheet_name, range_address = _parse_address(refers_to)
        if not sheet_name:
            sheet_name = wb.sheets.active.name
        self.refers_to_range = wb.sheets(sheet_name).range(range_address)
        self.refers_to = self.refers_to_range.__str__().split("]")[1][:-1]

    def __repr__(self):
        return "<Table '%s': %s>" % (self.name, self.refers_to)


class BookDataFrames(dict):
    """Object used to store Excel named ranges converted to dataframes."""

    pass


class Book(xw.main.Book):
    """Improved version of xlwings' ```Book``` object. This class allows for the
    support of Excel data tables, and circumvents other limitations."""

    def __init__(self, fullname=None, impl=None):
        super(Book, self).__init__(fullname, impl)
        self.dfs = BookDataFrames()

    @property
    def tables(self):
        return get_tables(self)

    @property
    def names(self):
        names = Names(impl=self.impl.names)
        names.wb = self
        return names

    def create_name(self, range_name, **kwargs):
        return create_named_range(self, range_name, **kwargs)

    def add_sheet(self, sheet_name):
        """Add sheet or return it if it already exists."""
        if sheet_name.lower() in (s.name.lower() for s in self.sheets):
            print("Sheet {} exists. Assigning it".format(sheet_name))
            return self.sheets(sheet_name)
        else:
            print("Added sheet {}.".format(sheet_name))
            return self.sheets.add(sheet_name)

    def range(self, address, sheet_name=None, verbose=True):
        return get_range(self, address, sheet_name, verbose)

    def all_names_to_df(
        self, keep_sheet_name=False, verbose=True, header_row=1, index_col=0
    ):
        """Turn all names in an Excel workbook to pandas dataframes."""
        # Excel includes solver-type objects as named ranges. Those shouldn't be
        # read in.
        named_ranges = [
            name for name in self.names if "solver" not in name.name
        ] + list(self.tables.values())
        could_not_read = []
        for named_range in named_ranges:
            try:
                self.named_range_to_df(
                    named_range,
                    keep_sheet_name=keep_sheet_name,
                    header_row=header_row,
                    index_col=index_col,
                    verbose=verbose,
                )
            except:
                print("Warning: couldn't read name {}".format(named_range))
                could_not_read += [named_range]
        return set(named_ranges) - set(could_not_read)

    def named_range_to_df(
        self,
        named_range,
        keep_sheet_name=False,
        sheet_name=None,
        header_row=0,
        index_col=0,
        verbose=True,
    ):
        """Turns a named range in Excel into a pandas dataframe.
        Also adds the dataframe to the ```dfs``` attribute.

        Args:
            named_range (xlwings.main.Name or Table):
                The named range to transfer.
            keep_sheet_name (bool): Whether to keep the name of the sheet in the
                name of the variable created.
            sheet_name (str): The name of the worksheet from which we want to
                get the range. This is ignored if the address contains a sheet
                name.
            index_col (int or None): The column number that should be used to
                create an index for the Pandas dataframe If the first column is
                the index, then set index_col=1 (not zero) The default value is
                index_col=None: all columns are read in as data, and a separate
                index is created for the dataframe.
            header_row (int or None): The row number that should be used to
                create column headings. Has similar functionality to index_col.
            verbose (bool): Prints warning messages if certain issues are
                encountered.

        Returns:
            pd.DataFrame: The Excel data turned into a Pandas DataFrame.
        """
        if isinstance(type(named_range), str):
            named_range = Name(get_named_range(self, named_range, sheet_name))

        # Determine what the name should be.
        if keep_sheet_name:
            # Keep the sheet name in the name of the dataframe.
            name = named_range.name.replace("!", "_")
        else:
            name = (
                named_range.name.split("!")[1]
                if named_range.name.find("!") > 0
                else named_range.name
            )

        rg = named_range.refers_to_range
        # Determine whether there is a header and an index.
        df_content = rg.value
        # If the named_range is 2D, assume it has a header and no index.
        if type(df_content) == list and type(df_content[0]) == list:

            # Get dataframe using ```xl2pd```.
            df = xl2pd(self, rg, header_row=1, index_col=index_col)

        # If named range is 1D
        # assume the first value is a header if it is a string, and no index
        if type(df_content) == list:
            if type(df_content[0]) == str:
                df = pd.DataFrame(df_content[1:], columns=[df_content[0]])
            # Otherwise just treat 1D array as data
            elif type(df_content[0]) != list and type(
                df_content[0] in [float, int, bool]
            ):
                df = pd.DataFrame(df_content)

        # If named range is a single value, use name of the range as header
        if type(df_content) != list and type(df_content) in [
            str,
            float,
            int,
            bool,
        ]:
            df = pd.DataFrame({rg.name.name: [df_content]})

        # Assign the dataframe to the name.
        if verbose:
            print("Read in {}".format(named_range))  # mg changed assigning to
            # read in
        exec("self.dfs.{} = df".format(name))
        self.dfs[name] = df

        return df


def _parse_address(full_address):
    """Parse a string containing a range address.

    Parse an Excel range address into a sheet name and a range specification.

    Example:
        ```_parse_address("'my sheet'!A1:X100")``` would return
        ```("my_sheet", "A1:X100")```.
    """
    splitaddr = full_address.split("!")
    if len(splitaddr) == 1:
        sheet_name = None
        address = splitaddr[0]
    elif len(splitaddr) == 2:
        characters_to_strip = list("'<>=")
        sheet_name = reduce(
            lambda x, y: x.strip(y), characters_to_strip, splitaddr[0]
        )
        sheet_name = sheet_name.split("]")[-1]
        address = splitaddr[1].strip(">")
    else:
        raise ValueError(
            "Invalid address in _parse_address: "
            + 'cannot contain multiple "!" characters'
        )
    return (sheet_name, address)


def get_tables(wb):
    """Get all the table names in ```wb```.

    Args:
        wb : xlwings workbook object.

    Returns:
        dict: A dictionary of strings where the keys are all the table names in
        ```wb```, and the values are the corresponding sheet names.
    """

    if sys.platform.lower() == "darwin":
        # the `api` attribute acts differently for windows and osx. (Linux undeveloped).
        # On top of that, OSX excel tables that implicitly includes headers require an [#all] tag when grabbing the range for the Table. Otherwise the first row of data gets read as headers
        # This apparently ONLY works for excel tables, and NOT named ranges on OSX
        return_dict = dict()
        for ws in wb.sheets:
            objects = ws.api.list_objects()
            if (
                objects
            ):  # Can be a mysterious "k.missingvalue" when there are no excel tables, which gets interpreted as False by bool
                for obj in objects:
                    return_dict[obj.name()] = Table(
                        obj.name(),  # name of table
                        ws.name
                        + "!"
                        + ws.range(
                            obj.name() + "[#all]"
                            if not obj.name().endswith("[#all]")
                            else obj.name()
                        ).address,
                        wb,
                    )  # Windows: obj.Name, OSX: obj.name(), obj.Range.Address -> ws.range(obj.name()).address

        return return_dict
    elif sys.platform.lower().startswith("win"):
        return {
            obj.Name: Table(obj.Name, ws.name + "!" + obj.Range.Address, wb)
            for ws in wb.sheets
            for obj in ws.api.ListObjects
            if ws.api.ListObjects.Count > 0
        }


def get_range(wb, address, sheet_name=None, verbose=True):
    """Get a range identified by ```address``` from the workbook ```wb```.

    Returns an xlwings range object, given a workbook, an address,
    and optionally a worksheet.
    If the worksheet is not specified, then the address must
    contain the worksheet name explicitly.

    Args:
        wb (xw.main.Book): An xlwings Book object.

        address (str): A string containing an Excel address
            (either like 'A1:B5' or explicitly containing a worksheet
            name like "'My worksheet'!C5:X73").
        sheet_name (str): The name of the worksheet from which we want to get
            the range. This is ignored if the address contains a sheet name.
        verbose (bool): Prints warning messages if certain issues are
            encountered.

    Returns:
        xw.main.Range: The range that has been found.
    """

    # Determine if the address contains sheet information
    match = re.search(r"^=*(.*)!(.*)", address)
    if match:
        sheet_name, address = match.groups()
        sheet_name = sheet_name.strip("'")
    elif not sheet_name:
        if verbose:
            sheet_name = wb.sheets[0].name
            print(
                "Warning: no explicit sheet information"
                " was passed to get_range. Assuming the desired"
                ' sheet is "{}".'.format(sheet_name)
            )

    # Otherwise we use the sheet_name keyword to get the sheet.
    try:
        rng = wb.sheets(sheet_name).range(address)
    except:
        if verbose:
            print(
                'Warning: unable to find a range at "'
                + address
                + '" in sheet "'
                + sheet_name
                + '".'
            )
        rng = None

    return rng


def get_named_range(wb, range_name, sheet_name=None, verbose=True, **kwargs):
    """Get a named range and return it as an xlwings range object.

    Args:
        wb: an xlwings workbook object
        range_name: a string containing the range name to be accessed.
        sheet_name: optional specification of the worksheet where the named
            range lives (for locally defined names, for example).
            If sheet is not specified, the code searches globally for the
            range name.
        verbose: print warning messages. (default=True)

    Returns:
        xw.main.Range: An xlwings range corresponding to the range name
            provided.
    """
    if not sheet_name:
        sheet_name = kwargs.get(sheet_name)
    try:
        if sys.platform.lower().startswith("win"):
            if sheet_name:
                obj = wb.sheets(sheet_name)
            else:
                obj = wb
            return obj.names[range_name].refers_to_range
        elif sys.platform.lower() == "darwin":
            # This is a ridiculous way to do it, I know. But if you try to get a range from a workbook by name, or sheet that doesn't have it, it breaks
            for ws in wb.sheets:
                for obj in ws.api.list_objects():
                    if obj.name() == range_name:
                        return ws.range(
                            range_name + "[#all]"
                            if not range_name.endswith("[#all]")
                            else range_name
                        )
    except:
        if verbose:
            print("Warning: unable to find a range named " + range_name + ".")
        return None


def create_named_range(
    wb,
    range_name,
    address=None,
    sheet_name=None,
    local=False,
    resize=False,
    verbose=True,
):
    """Create a named range.

    Create a named range OR re-create an existing named range, extending
    or contracting it as appropriate to fit the area that is filled with data.
    Resize or make name local.

    Args:
        wb (xw.main.Book): An xlwings workbook object
        range_name (str): The range name to create (code will search for an
            existing range by this name)
        address (str): The address over which to create the named range.
            Can be omitted if the named range already exists.
        sheet_name (str): The name of the worksheet on which to create (or
            search for) the named range. ignored if an address is passed with
            a sheet name included.
        local (bool): If True, the name will be defined as a local name to the
            sheet.
        resize (bool): if True, resize the range to cover the full region
            containing data (uses VBA CurrentRegion property), and apply the
             name to that range. (Default: False.)

    Returns:
        xw.main.Range: An xlwings range corresponding to the range name
            created."""
    rg = None

    if type(range_name) in (str, unicode):
        rg = get_named_range(wb, range_name)
    elif type(range_name) == xw.main.Range:
        rg, range_name = range_name, None
    elif type(range_name) in (xw.main.Name, Name):
        rg = range_name.refers_to_range
        range_name = rg.name.name

    if address:
        if rg:
            print(
                "A named range was found, but an address was provided."
                " Deleting existing named range."
            )
            rg.name.delete()
        sheet_name_from_address, address = _parse_address(address)
        # Use the user-provided sheet if available.
        rg = get_range(wb, address, sheet_name or sheet_name_from_address)

    if not rg:
        print(
            "Please provide a valid value for ```range_name```. If you're "
            "providing a string, if the name does not already exist, please "
            "also provide a valid address."
        )
        return

    # This is needed if the named range is to be local.
    if not sheet_name:
        sheet_name = rg.sheet.name

    if resize:
        rg = rg.current_region

    # Create the named range.
    rg.name = (
        sheet_name + "!" if local and "!" not in range_name else ""
    ) + range_name

    if verbose:
        info_string = " as a named range local to sheet," if local else ""
        print(
            "Created named range {},{} in sheet {}, at address {}.".format(
                range_name, info_string, sheet_name, rg.address
            )
        )

    return rg


def xl2pd(
    workbook, myrange, index_col=0, header_row=0, formulas=False, **kwargs
):
    """Turn a named range from an Excel workbook into a Pandas dataframe.

    Args:
        workbook (str, Book or xw.main.Book): Either the filename of a workbook
            to be read, or an xlwings Book object. For example, this:

            ```
            xl2pd('filename.xlsx', 'A1:C3', 'SheetName')
            ```

            is equivalent to this:

            ```
            wb = xlwings.Book('filename.xlsx')
            xl2pd(wb, 'A1:C3', 'SheetName')
            ```

        myrange (str or xw.main.Range): A string containing either a range in
            the usual Excel format (e.g., 'A1:C3'), or the name of a named range
            in the workbook being read (The code searches for a
            colon character, ':', to determine which kind of range
            this is In the unlikely event that you have a named range
            whose name contains a colon, then set named_range=True
            to override this.)

        index_col (int ): The column number that should be used to create
            an index for the Pandas dataframe If the first column is the index,
            then set index_col=1 (not zero) The default value is
            index_col=0: all columns are read in as data, and a separate
            index is created for the dataframe.

        header_row (int): The row number that should be used to create
            column headings. Has similar functionality to index_col.

        formulas (bool): If True, read in Excel formulas as strings. Note that
            this will read in the *entire* data set (including index and
            column entries) as unicode, rather than numerical data.
            (default behavior is to read in the values generated by
            the formulas and coerce to appropriate data types.)

        **kwargs (dict): Keyword arguments passed through to get_range or
            get_named_range

    Returns:
        pd.DataFrame: A Pandas dataframe with the data retrieved.
    """
    if isinstance(workbook, str):
        # Load workbook from specified file
        workbook = xw.Book(workbook)
    # (otherwise assume a Book object was passed.)

    if isinstance(myrange, str):
        if ":" in myrange:
            rng = get_range(workbook, myrange, **kwargs)
        else:
            rng = get_named_range(workbook, myrange, **kwargs)
    else:
        rng = myrange

    if rng:
        if formulas:
            data = rng.formula  # This is a tuple of tuples.
            cols = list(data[0])
            cols[0] = "convert_to_index"
            ret_df = pd.DataFrame(list(data[1:]), columns=cols)
            ret_df.set_index("convert_to_index", drop=True, inplace=True)
        else:
            if sys.platform.startswith("win"):
                # Convert directly to dataframe using xlwings
                ret_df = rng.options(
                    pd.DataFrame, header=header_row, index=index_col
                ).value

            elif sys.platform == "darwin":
                ### >>>>> The following code (with a few trivial renamings) comes directly from xlwings source code,
                # and is subject to copyright <<<<<
                # Copyright (c) 2020, Zoomer Analytics LLC
                # Subject to BSD-3 License for above copyright holder: https://opensource.org/licenses/BSD-3-Clause
                if header_row == 1:
                    columns = pd.Index(rng.value[0])
                elif header_row > 1:
                    columns = pd.MultiIndex.from_arrays(rng.value[:header])
                else:
                    columns = None

                ret_df = pd.DataFrame(
                    rng.value[header_row:],
                    columns=columns,
                    dtype=None,
                    copy=False,
                )

                # handle index by resetting the index to the index first columns
                # and renaming the index according to the name in the last row
                if index_col > 0:
                    # rename uniquely the index columns to some never used name for column
                    # we do not use the column name directly as it would cause issues if several
                    # columns have the same name
                    ret_df.columns = pd.Index(range(len(ret_df.columns)))
                    ret_df.set_index(
                        list(ret_df.columns)[:index_col], inplace=True
                    )

                    ret_df.index.names = pd.Index(
                        value[header_row - 1][:index_col]
                        if header_row
                        else [None] * index_col
                    )

                    if header_row:
                        ret_df.columns = columns[index_row:]
                    else:
                        ret_df.columns = pd.Index(range(len(df.columns)))

                ### >>>>> End of snippet that comes directly from xlwings <<<<<
    else:
        ret_df = None

    return ret_df


def pd2xl(
    dataframe,
    workbook,
    path=None,
    sheet_name="Sheet1",
    start_cell="A1",
    create_sheet=True,
    header=False,
    index=False,
    range_name=None,
    save=False,
    close=False,
    clear=False,
    resize=False,
    **kwargs
):
    """Write a Pandas dataframe to an Excel workbook.

    Args:

        dataframe (pd.DataFrame): A pandas DataFrame to be written into Excel

        workbook (str, Book or xw.main.Book): Either the filename of a workbook
            to be read, or an xlwings Book object. For example, this:

            ```
            xl2pd('filename.xlsx', 'A1:C3', 'SheetName')
            ```

            is equivalent to this:

            ```
            wb = xlwings.Book('filename.xlsx')
            xl2pd(wb, 'A1:C3', 'SheetName')
            ```

        sheet_name (str, default = 'Sheet1'): The name of the worksheet to which
            the dataframe will be written. This is ignored if a named range is
            used (so the named range is assumed to be globally scoped).

        create_sheet (bool, default:False): If specified sheet does not exist,
            create it.

        start_cell (str): Upper leftmost cell where DataFrame will be written.
            If header and index are both True, start_cell will be empty with
            index titles starting one cell below, and header names starting one
            cell to the right. Default is cell A1. This parameter is
            ignored if range_name is given.

        header (bool, default = False): If True will print column headers (i.e.
            dataframe.columns).

        index (bool, default = False): If True will print row names
            (i.e. dataframe.index).

        range_name (str): Named excel range for dataframe to be written. If this
            keyword is passed, then the code first tries to find
            and overwrite a named range by this name, ignoring the
            start_cell value. If no such name exists, the code writes
            out to the start_cell location and creates a new named
            range covering the output region.

        clear (bool): If True, clear the range to be written before writing.
            The range cleared is either the current named range, or
            the full contiguous region containing values to the left
            of and below the start_cell.

        resize (bool, default= False): If True, resize the named range to match
            the data being written.

        save (bool): If True, save the workbook before returning.

        path (str): Path to the output file where this workbook should be saved.
            If save=False, this is ignored. If this is not set, then
            the save location will be the same as for the workbook that
            is passed in.

        close (bool): If True, close the workbook before returning.

        **kwargs (dict): Keyword arguments passed through to get_range or
            get_named_range

    Returns:
        xw.main.Book: The workbook where the dataframe was saved.
    """

    if isinstance(type(workbook), str):
        # If the workbook doesn't exist, create it.
        if not glob(workbook):
            wb = xw.Book()
            wb.save(workbook)
            workbook = wb
        else:
            # Load workbook from specified file
            workbook = xw.Book(workbook)
    # (otherwise assume a Book object was passed.)

    rg = None
    if range_name:
        rg = get_named_range(workbook, range_name, **kwargs)

    if not rg:
        if create_sheet:
            # Create the sheet if it's not there.
            try:
                workbook.sheets.add(sheet_name)
            except ValueError:
                pass
        rg = get_range(workbook, start_cell, sheet_name, **kwargs)

    if clear:
        rg.current_region.clear()

    rg.options(index=index, header=header).value = dataframe

    if range_name:
        create_named_range(
            workbook,
            range_name,
            address=rg.address,
            sheet_name=rg.sheet.name,
            resize=resize,
        )

    if save:
        workbook.save(path)
    if close:
        workbook.close()

    return workbook
