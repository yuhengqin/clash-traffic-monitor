package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestLocalDashboardRejectsCrossOriginAndUntrustedHost(t *testing.T) {
	s := &service{}
	handler := s.withCORS(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusNoContent) }))
	tests := []struct {
		host, origin string
		want         int
	}{
		{"127.0.0.1:18080", "", http.StatusNoContent},
		{"127.0.0.1:18080", "http://127.0.0.1:18080", http.StatusNoContent},
		{"127.0.0.1:18080", "https://evil.example", http.StatusForbidden},
		{"evil.example:18080", "", http.StatusForbidden},
		{"localhost:18080", "http://localhost:18081", http.StatusForbidden},
	}
	for _, tt := range tests {
		req := httptest.NewRequest("GET", "http://"+tt.host+"/api/settings/mihomo", nil)
		if tt.origin != "" {
			req.Header.Set("Origin", tt.origin)
		}
		rec := httptest.NewRecorder()
		handler.ServeHTTP(rec, req)
		if rec.Code != tt.want {
			t.Errorf("host=%q origin=%q: got %d, want %d", tt.host, tt.origin, rec.Code, tt.want)
		}
		if rec.Header().Get("Access-Control-Allow-Origin") == "*" {
			t.Error("wildcard CORS is unsafe")
		}
	}
}

func TestCollectorBaselineDoesNotCountExistingConnections(t *testing.T) {
	svc := newTestService(t)
	payload := connectionsResponse{Connections: []connection{testConnection("existing", []string{"proxy"}, 100, 200)}}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { _ = json.NewEncoder(w).Encode(payload) }))
	defer server.Close()
	svc.setMihomoSettings(mihomoSettings{URL: server.URL})
	svc.collectOnce(context.Background())
	if len(svc.aggregateBuffer) != 0 {
		t.Fatalf("initial snapshot counted existing traffic")
	}
	payload.Connections[0].Download = 250
	svc.collectOnce(context.Background())
	if len(svc.aggregateBuffer) != 1 {
		t.Fatalf("subsequent traffic not recorded")
	}
}
