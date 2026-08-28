class YukiAPIError(Exception):
    """Base exception for all YukiYTAPI errors."""
    pass

class TrackNotFoundError(YukiAPIError):
    """Raised when a track or query cannot be found."""
    pass

class TokenError(YukiAPIError):
    """Raised when token generation or authentication fails."""
    pass

class DownloadError(YukiAPIError):
    """Raised when streaming or downloading fails."""
    pass
