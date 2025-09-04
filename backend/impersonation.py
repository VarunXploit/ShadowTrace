import imagehash
from PIL import Image
import Levenshtein
import os

class ImpersonationDetector:
    def __init__(self, official_usernames=None, max_distance=5):
        self.official_usernames = official_usernames or []
        self.max_distance = max_distance

    def check_username(self, candidate: str, threshold: float = 0.3):
        candidate = (candidate or "").lower()
        scores = []
        for vip in self.official_usernames:
            vip_l = (vip or "").lower()
            if len(vip_l) == 0:
                continue
            dist = Levenshtein.distance(candidate, vip_l)
            max_len = max(1, len(candidate), len(vip_l))
            similarity = 1 - dist / max_len
            scores.append((vip, similarity))
        if not scores:
            return {"closest_match": (None, 0.0), "is_impersonation": False}
        best = max(scores, key=lambda x: x[1])
        flag = best[1] >= (1 - threshold)
        return {"closest_match": best, "is_impersonation": flag}

    def check_profile_pic(self, vip_img_path: str, sus_img_path: str):
        if not os.path.exists(vip_img_path) or not os.path.exists(sus_img_path):
            raise FileNotFoundError("profile image(s) not found")
        h1 = imagehash.phash(Image.open(vip_img_path))
        h2 = imagehash.phash(Image.open(sus_img_path))
        dist = int(h1 - h2)
        flag = dist <= self.max_distance
        return {"distance": dist, "is_impersonation": flag}
