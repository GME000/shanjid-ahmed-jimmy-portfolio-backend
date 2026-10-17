from rest_framework.throttling import ScopedRateThrottle
class CommentThrottle(ScopedRateThrottle): scope = "comments"
class ContactThrottle(ScopedRateThrottle): scope = "contact"
class LikeThrottle(ScopedRateThrottle): scope = "likes"

