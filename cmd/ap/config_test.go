package main

import (
	"testing"
)

func TestIsExt(t *testing.T) {
	tests := []struct {
		name     string
		filename string
		exts     []string
		want     bool
	}{
		{
			name:     "matching extension",
			filename: "video.mp4",
			exts:     []string{".mp4", ".mkv"},
			want:     true,
		},
		{
			name:     "matching extension with uppercase filename",
			filename: "VIDEO.MP4",
			exts:     []string{".mp4", ".mkv"},
			want:     true,
		},
		{
			name:     "non-matching extension",
			filename: "document.pdf",
			exts:     []string{".mp4", ".mkv"},
			want:     false,
		},
		{
			name:     "filename with no extension",
			filename: "README",
			exts:     []string{".txt", ".md"},
			want:     false,
		},
		{
			name:     "empty extensions list",
			filename: "image.png",
			exts:     []string{},
			want:     false,
		},
		{
			name:     "hidden file matching extension",
			filename: ".hidden.mp4",
			exts:     []string{".mp4", ".mkv"},
			want:     true,
		},
		{
			name:     "hidden file as extension",
			filename: ".mp4",
			exts:     []string{".mp4", ".mkv"},
			want:     true,
		},
		{
			name:     "path containing directories",
			filename: "/var/log/syslog.1",
			exts:     []string{".1", ".log"},
			want:     true,
		},
		{
			name:     "filename with multiple dots",
			filename: "archive.tar.gz",
			exts:     []string{".gz", ".zip"},
			want:     true,
		},
		{
			name:     "filename with multiple dots, matching inner",
			filename: "archive.tar.gz",
			exts:     []string{".tar", ".zip"},
			want:     false,
		},
		{
			name:     "Windows path",
			filename: "C:\\Users\\User\\Documents\\file.TXT",
			exts:     []string{".txt", ".doc"},
			want:     true,
		},
		{
			name:     "exact match without dot in list",
			filename: "file.txt",
			exts:     []string{"txt"},
			want:     false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := isExt(tt.filename, tt.exts); got != tt.want {
				t.Errorf("isExt(%q, %v) = %v, want %v", tt.filename, tt.exts, got, tt.want)
			}
		})
	}
}

func TestLanguageLabel(t *testing.T) {
	tests := []struct {
		name     string
		code     string
		expected string
	}{
		{
			name:     "English code",
			code:     "en",
			expected: "English",
		},
		{
			name:     "Spanish code",
			code:     "es",
			expected: "Español",
		},
		{
			name:     "Portuguese (BR) code",
			code:     "pt-br",
			expected: "Português (BR)",
		},
		{
			name:     "German code",
			code:     "de",
			expected: "Deutsch",
		},
		{
			name:     "Unknown code returns self",
			code:     "unknown",
			expected: "unknown",
		},
		{
			name:     "Empty code returns self",
			code:     "",
			expected: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := languageLabel(tt.code)
			if result != tt.expected {
				t.Errorf("languageLabel(%q) = %q, expected %q", tt.code, result, tt.expected)
			}
		})
	}
}
