import time
import json
import musicbrainzngs
from musicbrainzngs.musicbrainz import NetworkError

musicbrainzngs.set_useragent(
    "GetDiscs",
    "0.1",
    "natanameyer@gmail.com",
)


def filter_by_track_count(
    artist_name, album_title, target_track_count, limit=25, retries=5, delay=2
):
    search_results = None  # initialize to avoid unbound variable error

    for attempt in range(1, retries + 1):
        try:
            search_results = musicbrainzngs.search_releases(
                artist=artist_name, release=album_title, limit=limit
            )
            break  # if successful, exit retry loop
        except NetworkError as e:
            print(f"NetworkError on attempt {attempt}/{retries}: {e}")
            if attempt < retries:
                time.sleep(delay)  # wait before retrying
            else:
                raise  # re-raise after last attempt

    if search_results is None:
        # This should never happen unless retries=0
        return None
    releases = search_results.get("release-list", [])
    matching_releases = []
    for release in releases:
        total_tracks_in_release = release.get("medium-track-count")
        if total_tracks_in_release == target_track_count:
            matching_releases.append(release)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(matching_releases, f, indent=4)

    if len(matching_releases) > 0:
        return matching_releases[0]

    return None


def print_result_info(album_data):
    print("Title:", album_data.get("title"))
    print("Date:", album_data.get("date"))
    print("Artist:", album_data.get("artist-credit")[0]["name"])
    print("Disambiguation:", album_data.get("disambiguation"))
    disc_info = album_data.get("medium-list")
    print("\nDiscs:", len(disc_info))
    if len(disc_info) > 1:
        current_track = 1
        for i, disc in enumerate(disc_info, start=1):
            start = current_track
            end = current_track + disc["track-count"] - 1

            print(f"Disc {i}: {start}-{end}")

            current_track = end + 1


def get_disc_info(artist_name, album_title, album_tracks):
    result = filter_by_track_count(artist_name, album_title, album_tracks)
    if result:
        medium_list = result.get("medium-list")
        return [d["track-count"] for d in medium_list]
    return [album_tracks]
