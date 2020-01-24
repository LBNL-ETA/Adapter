class Labels(object):
    """
    """

    def __init__(self):
        pass

    def set_labels(self):
        """
        """
        self.labels = {
            # table names
            'run_pars' : 'run_parameters',
            'extra_files' : 'inputs_from_files',
            # column labels
            'outpath' : 'Output Path',
            'version' : 'Version',
            'inpath' : 'File Path',
            'tbl_nam' : 'Table Name',
            'query' : 'Query Only'}

        return self.labels
