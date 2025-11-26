#!/bin/bash

# Configuration
BASE_URL="https://apps.fs.usda.gov/arcx/rest/services"
OUTPUT_DIR="./data/apps.fs.usda.gov.arcx.rest.services"
DELAY=0.2 # Delay in seconds between requests
FORCE_DOWNLOAD=false # Default behavior: do not force downloads

# Parse command-line arguments
while getopts "f" opt; do
    case $opt in
        f) FORCE_DOWNLOAD=true ;; # Enable force download
        *)
            echo "Usage: $0 [-f]"
            echo "  -f    Force download even if files already exist"
            exit 1
            ;;
    esac
done

# Ensure the base output directory exists
mkdir -p "$OUTPUT_DIR"

# A recursive function to crawl the hierarchy
crawl() {
    local current_url=$1
    local current_path=$2

    echo "[*] Processing: $current_path"

    # Create the local directory for the current path
    mkdir -p "$current_path"

    # --- MODIFICATION START: Check for existing _index.json ---
    local json_url="${current_url}?f=json"
    local index_file="${current_path}/_index.json"
    local response

    if [ "$FORCE_DOWNLOAD" = true ] || [ ! -f "$index_file" ]; then
        echo "  [DOWNLOAD] Fetching index: $json_url"
        response=$(curl -s -L "$json_url")

        # Check if curl succeeded and returned valid JSON
        if ! jq -e . >/dev/null 2>&1 <<<"$response"; then
            echo "  [!] Failed to fetch or parse JSON from $json_url"
            return
        fi

        # Save the newly downloaded index file
        echo "$response" | jq '.' > "$index_file"
        sleep $DELAY
    else
        echo "  [CACHE] Index file exists, reading from disk: $index_file"
        response=$(cat "$index_file")
    fi
    # --- MODIFICATION END ---

    # Extract and loop through folders (this part is unchanged)
    local folders
    folders=$(echo "$response" | jq -r '.folders[]' || true)
    for folder in $folders; do
        crawl "${current_url}/${folder}" "${current_path}/${folder}"
    done

    # Extract service names and types (this part is unchanged)
    local services
    services=$(echo "$response" | jq -c '.services[]' || true)
    while IFS= read -r service_json; do
        local service_name
        service_name=$(echo "$service_json" | jq -r '.name')
        local service_type
        service_type=$(echo "$service_json" | jq -r '.type')

        local base_service_name=${service_name##*/}
        local service_file="${current_path}/${base_service_name}_${service_type}.json"

        # --- MODIFICATION START: Check if the service file exists before downloading ---
        if [ "$FORCE_DOWNLOAD" = true ] || [ ! -f "$service_file" ]; then
            echo "  -> [DOWNLOAD] Service: ${base_service_name} (${service_type})"

            local service_url="${BASE_URL}/${service_name}/${service_type}?f=json"
            curl -s -L "$service_url" | jq '.' > "$service_file"
            sleep $DELAY
        else
            echo "  -> [SKIP] Service exists: ${base_service_name} (${service_type})"
        fi
        # --- MODIFICATION END ---

    done <<< "$services"
}

# Start the process
echo "Starting download to '$OUTPUT_DIR'..."
crawl "$BASE_URL" "$OUTPUT_DIR"
echo "[+] Download complete!"