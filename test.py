from ytmusicapi import YTMusic

yt = YTMusic()  # anonymous access (no login needed)

query = "damn"
results = yt.search(query, filter="albums")

for album in results:
    print(album["title"], "-", album["browseId"])

print("\n\n\n")

print(results)

print("\n\n\n")

album_id = results[0]["browseId"]
album = yt.get_album(album_id)
print("Album: ", album["title"])
print("Artist: ", album["artists"][0]["name"])
print("year: ", album["year"])
print("trackCount: ", album["trackCount"])
print("thumbnail: ", album["thumbnails"][-1]["url"])
print()
# print(album["title"], "by", album["artist"]["name"])
# for track in album["tracks"]:
#     print(track["title"], "-", track["videoId"])
