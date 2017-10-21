
post_url = "https://vk.com/oldlentach?w=wall-29534144_7488676"
index_start = post_url.rindex("-")


print(index_start)
post_id = post_url[index_start:]
print(post_id)
