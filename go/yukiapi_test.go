package yukiapi

import (
	"context"
	"testing"
	"time"
)

func TestSearch(t *testing.T) {
	client := New(WithTimeout(15 * time.Second))
	ctx := context.Background()

	results, err := client.Search(ctx, "Kesariya", 2)
	if err != nil {
		t.Fatalf("Search returned error: %v", err)
	}
	if len(results) == 0 {
		t.Fatal("Search returned 0 results")
	}
	if results[0].ID == "" {
		t.Fatal("Track ID is empty")
	}
}

func TestDetails(t *testing.T) {
	client := New(WithTimeout(15 * time.Second))
	ctx := context.Background()

	track, err := client.Details(ctx, "BddP6PYo2gs")
	if err != nil {
		t.Fatalf("Details returned error: %v", err)
	}
	if track.ID != "BddP6PYo2gs" {
		t.Fatalf("Expected ID BddP6PYo2gs, got %s", track.ID)
	}
}

func TestGetStream(t *testing.T) {
	client := New(WithTimeout(15 * time.Second))
	ctx := context.Background()

	streamURL, err := client.GetStream(ctx, "BddP6PYo2gs", "audio")
	if err != nil {
		t.Fatalf("GetStream returned error: %v", err)
	}
	if streamURL == "" {
		t.Fatal("Stream URL is empty")
	}
}
