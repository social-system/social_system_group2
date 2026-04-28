package config

import (
	"fmt"
	"os"
	"strconv"
)

type Config struct {
	OpenAIAPIKey      string
	FridgeAPIBaseURL  string
	UserPrefsFilePath string
	Port              string
	OpenAIModel       string
	CacheEnabled      bool
	Debug             bool
}

func Load() (*Config, error) {
	debug := false
	if v := os.Getenv("DEBUG"); v != "" {
		var err error
		debug, err = strconv.ParseBool(v)
		if err != nil {
			return nil, fmt.Errorf("DEBUG must be true or false: %w", err)
		}
	}

	apiKey := os.Getenv("OPENAI_API_KEY")
	if apiKey == "" && !debug {
		return nil, fmt.Errorf("OPENAI_API_KEY is required")
	}

	fridgeURL := os.Getenv("FRIDGE_API_BASE_URL")

	prefsPath := os.Getenv("USER_PREFS_FILE_PATH")
	if prefsPath == "" {
		prefsPath = "./data/preferences.json"
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	model := os.Getenv("OPENAI_MODEL")
	if model == "" {
		model = "gpt-4o"
	}

	cacheEnabled := true
	if v := os.Getenv("AI_CACHE_ENABLED"); v != "" {
		var err error
		cacheEnabled, err = strconv.ParseBool(v)
		if err != nil {
			return nil, fmt.Errorf("AI_CACHE_ENABLED must be true or false: %w", err)
		}
	}

	return &Config{
		OpenAIAPIKey:      apiKey,
		FridgeAPIBaseURL:  fridgeURL,
		UserPrefsFilePath: prefsPath,
		Port:              port,
		OpenAIModel:       model,
		CacheEnabled:      cacheEnabled,
		Debug:             debug,
	}, nil
}
