from ytmusicapi import YTMusic
import questionary
import sys
import json

yt = YTMusic()


album_query = questionary.text("Album name: ").ask()
if not album_query:
    sys.exit(0)

results = yt.search(album_query, filter="albums")
first_four_albums = results[:4]
preferred_base_album_title = questionary.select(
    "Which version:", choices=[album["title"] for album in first_four_albums]
).ask()

preferred_base_album = next(
    (
        album
        for album in first_four_albums
        if album["title"] == preferred_base_album_title
    )
)

default_album_id = preferred_base_album["browseId"]  # results[0]["browseId"]
default_album = yt.get_album(default_album_id)

if any(track.get("isExplicit", False) for track in default_album["tracks"]):
    default_album["isExplicit"] = True

albums_to_compare = [default_album]

# 2) Collect other versions
for version in default_album.get("other_versions", []):
    try:
        new_version = yt.get_album(version["browseId"])
        if any(track.get("isExplicit", False) for track in new_version["tracks"]):
            new_version["isExplicit"] = True
        albums_to_compare.append(new_version)
    except Exception:
        pass  # skip broken versions safely


first_four_albums = albums_to_compare[:4]
with open("data2.json", "w", encoding="utf-8") as f:
    json.dump(albums_to_compare, f, indent=4)

preferred_album_title = questionary.select(
    "which version:",
    choices=[
        f"{album['title']}{' 􀂝 ' if album['isExplicit'] else ''} ⋅ {
            album['trackCount']
        } songs"
        for album in first_four_albums
    ],
).ask()

# # 3) Choose best version
# def score(album):
#     track_count = len(album.get("tracks", []))
#     is_explicit = album.get("isExplicit", False)
#     return (track_count, is_explicit)
#
#
# best_album = max(albums_to_compare, key=score)


# results = yt.search("eternal sunshine ariana grande", filter="albums")
# with open("data2.json", "w", encoding="utf-8") as f:
#     json.dump(results, f, indent=4)
