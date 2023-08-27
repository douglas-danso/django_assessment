from django.dispatch import Signal

get_new_followers = Signal()

get_new_comments = Signal()

like_a_post = Signal()

like_a_comment = Signal()