package yukiapi

type Track struct {
	ID          string `json:"id"`
	VidID       string `json:"vidid"`
	Title       string `json:"title"`
	Duration    string `json:"duration"`
	DurationMin string `json:"duration_min"`
	DurationSec int    `json:"duration_sec"`
	Link        string `json:"link"`
	Thumbnail   string `json:"thumbnail"`
	Channel     string `json:"channel"`
	Views       string `json:"views"`
}

type SearchResponse struct {
	Status  string  `json:"status"`
	Query   string  `json:"query"`
	Count   int     `json:"count"`
	Results []Track `json:"results"`
}

type DetailsResponse struct {
	Status      string `json:"status"`
	ID          string `json:"id"`
	VidID       string `json:"vidid"`
	Title       string `json:"title"`
	Duration    string `json:"duration"`
	DurationMin string `json:"duration_min"`
	DurationSec int    `json:"duration_sec"`
	Link        string `json:"link"`
	Thumbnail   string `json:"thumbnail"`
	Channel     string `json:"channel"`
	Views       string `json:"views"`
}

type PlaylistResponse struct {
	Status string  `json:"status"`
	Count  int     `json:"count"`
	Tracks []Track `json:"tracks"`
}

type DownloadTokenResponse struct {
	Status        string `json:"status"`
	VideoID       string `json:"video_id"`
	DownloadToken string `json:"download_token"`
	Usage         string `json:"usage"`
}
