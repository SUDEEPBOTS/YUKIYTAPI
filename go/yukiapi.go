package yukiapi

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

const (
	DefaultBaseURL     = "https://music.yukiapi.site"
	DefaultFallbackURL = "https://yukiapi.site/music"
)

type Client struct {
	BaseURL     string
	FallbackURL string
	HTTPClient  *http.Client
}

type Option func(*Client)

func WithBaseURL(customURL string) Option {
	return func(c *Client) {
		c.BaseURL = strings.TrimRight(customURL, "/")
	}
}

func WithHTTPClient(httpClient *http.Client) Option {
	return func(c *Client) {
		c.HTTPClient = httpClient
	}
}

func WithTimeout(timeout time.Duration) Option {
	return func(c *Client) {
		c.HTTPClient.Timeout = timeout
	}
}

func New(opts ...Option) *Client {
	c := &Client{
		BaseURL:     DefaultBaseURL,
		FallbackURL: DefaultFallbackURL,
		HTTPClient:  &http.Client{Timeout: 60 * time.Second},
	}
	for _, opt := range opts {
		opt(c)
	}
	return c
}

// ExtractVideoID extracts an 11-character YouTube video ID from various URL formats.
func ExtractVideoID(rawURL string) string {
	rawURL = strings.TrimSpace(rawURL)
	if len(rawURL) == 11 && regexp.MustCompile(`^[a-zA-Z0-9_-]{11}$`).MatchString(rawURL) {
		return rawURL
	}
	patterns := []*regexp.Regexp{
		regexp.MustCompile(`(?:v=)([a-zA-Z0-9_-]{11})`),
		regexp.MustCompile(`youtu\.be/([a-zA-Z0-9_-]{11})`),
		regexp.MustCompile(`/shorts/([a-zA-Z0-9_-]{11})`),
		regexp.MustCompile(`/embed/([a-zA-Z0-9_-]{11})`),
		regexp.MustCompile(`/live/([a-zA-Z0-9_-]{11})`),
	}
	for _, p := range patterns {
		matches := p.FindStringSubmatch(rawURL)
		if len(matches) > 1 {
			return matches[1]
		}
	}
	return rawURL
}

func (c *Client) request(ctx context.Context, path string, params url.Values, target interface{}) error {
	urls := []string{
		fmt.Sprintf("%s%s", c.BaseURL, path),
		fmt.Sprintf("%s%s", c.FallbackURL, path),
	}
	if len(params) > 0 {
		encoded := params.Encode()
		urls[0] = fmt.Sprintf("%s?%s", urls[0], encoded)
		urls[1] = fmt.Sprintf("%s?%s", urls[1], encoded)
	}

	var lastErr error
	for _, reqURL := range urls {
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, reqURL, nil)
		if err != nil {
			lastErr = err
			continue
		}

		resp, err := c.HTTPClient.Do(req)
		if err != nil {
			lastErr = err
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode == http.StatusOK {
			return json.NewDecoder(resp.Body).Decode(target)
		} else if resp.StatusCode == http.StatusNotFound {
			return ErrTrackNotFound
		} else {
			lastErr = fmt.Errorf("yukiapi: http status %d", resp.StatusCode)
		}
	}
	if lastErr != nil {
		return lastErr
	}
	return ErrTrackNotFound
}

// Search queries YouTube tracks using YukiAPI's 3-Way Async Search Race.
func (c *Client) Search(ctx context.Context, query string, limit int) ([]Track, error) {
	if strings.TrimSpace(query) == "" {
		return nil, ErrEmptyQuery
	}
	if limit <= 0 {
		limit = 5
	}
	params := url.Values{}
	params.Set("q", query)
	params.Set("limit", fmt.Sprintf("%d", limit))

	var res SearchResponse
	if err := c.request(ctx, "/search", params, &res); err != nil {
		return nil, err
	}
	return res.Results, nil
}

// Details fetches complete track metadata including duration, thumbnail, and video ID.
func (c *Client) Details(ctx context.Context, queryOrURL string) (*Track, error) {
	if strings.TrimSpace(queryOrURL) == "" {
		return nil, ErrEmptyQuery
	}
	params := url.Values{}
	params.Set("url", queryOrURL)

	var res DetailsResponse
	if err := c.request(ctx, "/details", params, &res); err != nil {
		return nil, err
	}
	return &Track{
		ID:          res.ID,
		VidID:       res.VidID,
		Title:       res.Title,
		Duration:    res.Duration,
		DurationMin: res.DurationMin,
		DurationSec: res.DurationSec,
		Link:        res.Link,
		Thumbnail:   res.Thumbnail,
		Channel:     res.Channel,
		Views:       res.Views,
	}, nil
}

// GetToken generates a high-speed download & streaming token.
func (c *Client) GetToken(ctx context.Context, queryOrURL string, mediaType string) (string, string, error) {
	vidID := ExtractVideoID(queryOrURL)
	if len(vidID) != 11 {
		track, err := c.Details(ctx, queryOrURL)
		if err != nil {
			return "", "", err
		}
		vidID = track.ID
	}
	if mediaType == "" {
		mediaType = "audio"
	}
	params := url.Values{}
	params.Set("url", vidID)
	params.Set("type", mediaType)

	var res DownloadTokenResponse
	if err := c.request(ctx, "/download", params, &res); err != nil {
		return "", "", err
	}
	if res.DownloadToken == "" {
		return "", "", ErrTokenFailed
	}
	return res.DownloadToken, res.VideoID, nil
}

// GetStream returns a direct streaming URL with authorization token for PyTgCalls / FFmpeg.
func (c *Client) GetStream(ctx context.Context, queryOrURL string, mediaType string) (string, error) {
	token, vidID, err := c.GetToken(ctx, queryOrURL, mediaType)
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("%s/stream/%s?type=%s&token=%s", c.BaseURL, vidID, mediaType, token), nil
}

// Playlist extracts track information from a YouTube playlist URL.
func (c *Client) Playlist(ctx context.Context, playlistURL string, limit int) ([]Track, error) {
	if strings.TrimSpace(playlistURL) == "" {
		return nil, ErrEmptyQuery
	}
	if limit <= 0 {
		limit = 50
	}
	params := url.Values{}
	params.Set("url", playlistURL)
	params.Set("limit", fmt.Sprintf("%d", limit))

	var res PlaylistResponse
	if err := c.request(ctx, "/playlist", params, &res); err != nil {
		return nil, err
	}
	return res.Tracks, nil
}

// Download saves the audio/video file atomically to the destination directory.
func (c *Client) Download(ctx context.Context, queryOrURL string, mediaType string, outputDir string, customFilename string) (string, error) {
	if mediaType == "" {
		mediaType = "audio"
	}
	if outputDir == "" {
		outputDir = "downloads"
	}

	token, vidID, err := c.GetToken(ctx, queryOrURL, mediaType)
	if err != nil {
		return "", err
	}

	ext := "mp3"
	if mediaType == "video" {
		ext = "mp4"
	}

	filename := customFilename
	if filename == "" {
		filename = fmt.Sprintf("%s.%s", vidID, ext)
	}

	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return "", err
	}

	finalPath := filepath.Join(outputDir, filename)
	if fi, err := os.Stat(finalPath); err == nil && fi.Size() > 0 {
		return finalPath, nil
	}

	streamURL := fmt.Sprintf("%s/stream/%s?type=%s&token=%s", c.BaseURL, vidID, mediaType, token)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, streamURL, nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("X-Download-Token", token)

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("yukiapi: stream returned status %d", resp.StatusCode)
	}

	tmpPath := fmt.Sprintf("%s.%d.tmp", finalPath, os.Getpid())
	out, err := os.Create(tmpPath)
	if err != nil {
		return "", err
	}

	_, err = io.Copy(out, resp.Body)
	out.Close()
	if err != nil {
		_ = os.Remove(tmpPath)
		return "", err
	}

	if err := os.Rename(tmpPath, finalPath); err != nil {
		_ = os.Remove(tmpPath)
		return "", err
	}

	return finalPath, nil
}
