class MissingColumnsError(Exception):
    """Exception raised for errors in data cleaning when there was expected columns that are not there.
    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Missing Columns",missing_columns = []):
        self.message = message
        self.missing_columns = missing_columns
        super().__init__(self.message)