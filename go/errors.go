package yukiapi

import "errors"

var (
	ErrTrackNotFound  = errors.New("yukiapi: track not found")
	ErrTokenFailed    = errors.New("yukiapi: failed to obtain download token")
	ErrDownloadFailed = errors.New("yukiapi: download failed")
	ErrEmptyQuery     = errors.New("yukiapi: query cannot be empty")
)
