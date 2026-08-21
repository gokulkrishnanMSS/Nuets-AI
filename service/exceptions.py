class FoodNotRecognisedError(Exception):
    """Raised when no food could be identified in the uploaded image.

    Controllers translate this into a 404 response.
    """
