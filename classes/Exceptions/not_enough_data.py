class NotEnoughDataError(Exception):
    """Exception raised for errors when there is not enough data.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Not enough data provided."):
        self.message = message
        super().__init__(self.message)