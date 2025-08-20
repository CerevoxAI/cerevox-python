"""
Cerevox SDK Constants
"""

from dataclasses import dataclass


@dataclass
class CoreConstants:
    """
    Constants for the Cerevox SDK core
    """

    FAILED_ID = "Failed to get request ID from response"
    HTTPS_PREFIX = "https://"
    HTTP_PREFIX = "http://"
    REQUEST_ID_DESCRIPTION = "The request id returned by the Cerevox API"


core = CoreConstants()
