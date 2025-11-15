#!/bin/bash

# set start and end dates to the first Pips game and today
start_date="2025-08-18"
end_date=$(date +%Y-%m-%d)

echo "Fetching Pips games from $start_date to $end_date..."

mkdir -p all_boards

# convert start/end dates to epoch seconds 
start_sec=$(date -j -f "%Y-%m-%d" "$start_date" "+%s")
end_sec=$(date -j -f "%Y-%m-%d" "$end_date" "+%s")

current_sec="$start_sec"

while [ "$current_sec" -le "$end_sec" ]; do

    # convert epoch seconds to YYYY-MM-DD
    current_date=$(date -j -f "%s" "$current_sec" "+%Y-%m-%d")

    json_file="all_boards/${current_date}.json"

    if [ -e "$json_file" ]; then
        echo "JSON for $current_date already exists. Skipping."
    else
        echo "Fetching JSON for: $current_date"

        url="https://www.nytimes.com/svc/pips/v1/${current_date}.json"
        curl -s "$url" -o "$json_file"

        if [ $? -eq 0 ] && [ -s "$json_file" ]; then
            echo "Successfully saved $json_file"
        else
            echo "Failed to fetch $current_date"
            rm -f "$json_file"
        fi

        sleep 0.5
    fi

    # increment by one day (86400 seconds)
    current_sec=$((current_sec + 86400))

done

echo "Fetched all Pips games!"
