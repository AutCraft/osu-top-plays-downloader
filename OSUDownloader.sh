#!/usr/bin/env bash
set -e

SONGS_DIR="./songs"
mkdir -p "$SONGS_DIR"

sanitize_filename() {
    local name="$1"
    # Replace invalid chars <>:"/\|?* with underscore and trim spaces/dots
    local clean
    clean=$(echo "$name" | sed -E 's/[<>:"/\\|?*]+/_/g' | sed 's/^[. ]*//;s/[. ]*$//')
    if [ -z "$clean" ]; then
        echo "beatmap"
    else
        echo "$clean"
    fi
}

resolve_user_id() {
    local input="$1"
    # URL match
    if [[ "$input" =~ /users/([0-9]+) ]] || [[ "$input" =~ /u/([0-9]+) ]]; then
        echo "${BASH_REMATCH[1]}"
        return 0
    fi
    # Pure numeric ID
    if [[ "$input" =~ ^[0-9]+$ ]]; then
        echo "$input"
        return 0
    fi

    # Username lookup via redirect
    local final_url
    final_url=$(curl -s -L -o /dev/null -w "%{url_effective}" -A "Mozilla/5.0" "https://osu.ppy.sh/users/$input")
    if [[ "$final_url" =~ /users/([0-9]+) ]] || [[ "$final_url" =~ /u/([0-9]+) ]]; then
        echo "${BASH_REMATCH[1]}"
        return 0
    fi

    echo "Error: Could not resolve user ID for: '$input'" >&2
    return 1
}

parse_json_maps() {
    local json="$1"
    if command -v jq >/dev/null 2>&1; then
        echo "$json" | jq -r '.[] | select(.beatmapset != null) | "\(.beatmapset.id)\t\(.beatmapset.title)"'
    elif command -v node >/dev/null 2>&1; then
        node -e '
            const data = JSON.parse(process.argv[1]);
            data.forEach(x => {
                if (x.beatmapset) console.log(`${x.beatmapset.id}\t${x.beatmapset.title}`);
            });
        ' "$json"
    elif command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
        local py_cmd="python3"
        command -v python3 >/dev/null 2>&1 || py_cmd="python"
        $py_cmd -c '
import sys, json
try:
    data = json.loads(sys.argv[1])
    for x in data:
        s = x.get("beatmapset")
        if s:
            print(f"{s[\"id\"]}\t{s[\"title\"]}")
except Exception:
    pass
' "$json"
    else
        # Basic grep/sed fallback
        echo "$json" | grep -o '{"id":[0-9]*,"[^}]*"title":"[^"]*"' | sed -E 's/.*"id":([0-9]+).*"title":"([^"]+)".*/\1\t\2/'
    fi
}

download_beatmapset() {
    local set_id="$1"
    local title="$2"
    local safe_title
    safe_title=$(sanitize_filename "$title")
    local filename="${set_id} ${safe_title}.osz"
    local target_path="${SONGS_DIR}/${filename}"

    if [ -f "$target_path" ] && [ "$(wc -c < "$target_path" 2>/dev/null || echo 0)" -gt 1024 ]; then
        echo "Already downloaded: $filename"
        return 0
    fi

    local temp_path="${target_path}.tmp"
    local mirrors=(
        "Catboy|https://catboy.best/d/${set_id}"
        "Sayobot|https://dl.sayobot.cn/beatmaps/download/novideo/${set_id}"
        "Nerinyan|https://api.nerinyan.moe/d/${set_id}?noVideo=true"
    )

    for entry in "${mirrors[@]}"; do
        local m_name="${entry%%|*}"
        local m_url="${entry#*|}"

        echo "  Downloading from ${m_name}..."
        if curl -f -s -L -A "Mozilla/5.0" --max-time 30 -o "$temp_path" "$m_url"; then
            local size
            size=$(wc -c < "$temp_path" 2>/dev/null || echo 0)
            if [ "$size" -gt 1024 ]; then
                # Check zip magic bytes (PK)
                local magic
                magic=$(head -c 2 "$temp_path" 2>/dev/null || true)
                if [ "$magic" = "PK" ]; then
                    mv -f "$temp_path" "$target_path"
                    echo "  Saved: $filename"
                    return 0
                fi
            fi
        fi
        rm -f "$temp_path" 2>/dev/null || true
    done

    echo "  Failed to download mapset ${set_id} from all mirrors."
    return 1
}

run_self_check() {
    echo "Running self-check..."
    test_clean=$(sanitize_filename 'test: *?/"<>| name. ')
    if [ "$test_clean" != "test_ _ name" ] && [ "$test_clean" != "test_ ___ name" ]; then
        echo "Self-check failed: sanitize_filename gave '$test_clean'" >&2
        exit 1
    fi
    test_jp=$(sanitize_filename '夜に駆ける')
    if [ "$test_jp" != "夜に駆ける" ]; then
        echo "Self-check failed for unicode '$test_jp'" >&2
        exit 1
    fi
    uid=$(resolve_user_id "2")
    if [ "$uid" != "2" ]; then
        echo "Self-check failed: resolve_user_id gave '$uid'" >&2
        exit 1
    fi
    echo "Self-check passed!"
    exit 0
}

main() {
    if [ "$1" = "--test" ]; then
        run_self_check
    fi

    local raw_user=""
    local number_of_maps=10
    local mode=1

    if [ $# -ge 1 ]; then
        raw_user="$1"
        number_of_maps="${2:-10}"
        mode="${3:-1}"
    else
        read -r -p "Enter User ID, Profile URL, or Username: " raw_user
        read -r -p "Enter number of maps to download (default 10): " input_num
        number_of_maps="${input_num:-10}"
        read -r -p "Choose mode [1: Most Played (default), 2: Top Plays (Best pp)]: " input_mode
        mode="${input_mode:-1}"
    fi

    local user_id
    user_id=$(resolve_user_id "$raw_user") || exit 1

    local endpoint="beatmapsets/most_played"
    local mode_label="Most Played"
    if [ "$mode" = "2" ]; then
        endpoint="scores/best"
        mode_label="Top Plays (Best pp)"
    fi

    echo ""
    echo "Fetching ${number_of_maps} ${mode_label} for user ID ${user_id}..."

    local offset=0
    local all_items=""
    local total_fetched=0

    while [ "$total_fetched" -lt "$number_of_maps" ]; do
        local limit=$((number_of_maps - total_fetched))
        if [ "$limit" -gt 100 ]; then
            limit=100
        fi

        local url="https://osu.ppy.sh/users/${user_id}/${endpoint}?offset=${offset}&limit=${limit}"
        local resp
        resp=$(curl -s -L -A "Mozilla/5.0" "$url")

        local parsed
        parsed=$(parse_json_maps "$resp")
        if [ -z "$parsed" ]; then
            break
        fi

        all_items="${all_items}${parsed}"$'\n'
        local batch_count
        batch_count=$(echo "$parsed" | grep -c . || echo 0)
        total_fetched=$((total_fetched + batch_count))
        offset=$((offset + batch_count))

        if [ "$batch_count" -lt "$limit" ]; then
            break
        fi
    done

    if [ -z "$all_items" ]; then
        echo "No beatmaps found."
        exit 0
    fi

    # Deduplicate unique beatmapsets while preserving order
    local unique_lines
    unique_lines=$(echo "$all_items" | awk -F'\t' '!seen[$1]++ && NF>=2')
    local unique_count
    unique_count=$(echo "$unique_lines" | grep -c . || echo 0)
    local total_diffs
    total_diffs=$(echo "$all_items" | grep -c . || echo 0)

    echo "Found ${unique_count} unique beatmapsets (${total_diffs} total difficulties/plays) to download."
    echo ""

    local success=0
    local idx=1
    while IFS=$'\t' read -r sid title; do
        [ -z "$sid" ] && continue
        echo "[${idx}/${unique_count}] Beatmapset ${sid}: ${title}"
        if download_beatmapset "$sid" "$title"; then
            success=$((success + 1))
        fi
        idx=$((idx + 1))
    done <<< "$unique_lines"

    echo ""
    echo "Done! Downloaded ${success}/${unique_count} (${total_diffs} difficulties) beatmapsets into '${SONGS_DIR}/'."
}

main "$@"
