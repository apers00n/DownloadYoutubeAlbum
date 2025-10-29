from ytmusicapi import YTMusic

yt = YTMusic()

results = yt.search("DAMN", filter="albums")
for album in results:
    print(album["title"], "-", album["browseId"])

album = results[0]
album_id = album["browseId"]
album_data = yt.get_album(album_id)
print(album_data["year"])
print(album_data["description"])
