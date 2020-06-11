def readin(self, infile=None, inwb=None, xl=None,
               close=False, tables=False, visible=False, **kwargs):
        """
        Read in Excel workbook with input for this product and
        read in various parameters and tables.

        Parameters:
        -----------
        infile: A file name to read from (ignored if inwb is passed).

        inwb: An input workbook object
        xl: An Excel instance corresponding to inwb
        (required if inwb is passed).

        close: Close the workbook and Excel instance after reading
        (default: False)

        Returns:
        --------
        xl, inwb: An Excel instance and a workbook object. (Both will be
        None if close=True.)
        """
        #Check to see if a workbook object was passed, and if so also an
        #excel instance
        if inwb is not None:
            if self.verbose:
                print("got a workbook instance")
            if not xl:
                raise ValueError(
                    "must pass an excel instance if passing a workbook object")

        if infile and (not inwb):
            if self.verbose:
                print('Loading Excel Workbook....')
            xl, inwb = sc.ExcelConnection(visible=visible, name=infile)
            if self.verbose:
                print(xl)
                print(inwb)
                print('Done')
        if inwb is None:
            #Then we didn't get a filename or a workbook
            raise ValueError('Must specify either infile or inwb and xl '+
                             'in BaseShipper.readin().')

        if self.verbose:
            print(inwb)
            print('Reading in Excel data....')

        #TBD: combine the following two read-in statements
        #to infer whether we have a series or data frame
        #by first reading as a data frame, counting columns
        #and repeating the read-in as a series if there is
        #only one.
        for k in list(self.data_frame_range_names.keys()):
            #print("inside readin, reading in "+k)
            exec('self.'+k+' = self._readDf(inwb, "'+
                 self.data_frame_range_names[k]+
                 '", tables=tables)')


        #Scenario number
        if self.scenrange is not None:
            self._getScen(self.scenrange)

        if close:
            inwb.Close(False)
        if self.verbose:
            print('Done reading Excel data.')

        #Set up some attributes from the data we just read in.
        if self.prodpar is not None:
            self.columns = self.prodpar.columns

        #Get the individual time parameters and make them
        #class attributes
        if self.timepar is not None:
            self.get_time_parameters()



        return xl,inwb