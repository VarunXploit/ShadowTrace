import imagehash
from PIL import Image
import Levenshtein

# --- Username similarity ---
def check_username_similarity(candidate, official_list, threshold=0.3):
    """
    candidate: username to check
    official_list: list of official VIP usernames
    threshold: fraction (0.0 = exact, 1.0 = very different)
    """
    candidate = candidate.lower()
    scores = []
    for vip in official_list:
        dist = Levenshtein.distance(candidate, vip.lower())
        max_len = max(len(candidate), len(vip))
        similarity = 1 - dist / max_len
        scores.append((vip, similarity))
    best_match = max(scores, key=lambda x: x[1])
    return best_match, best_match[1] >= (1 - threshold)


# --- Profile picture similarity ---
def check_profile_pic(img1_path, img2_path, max_distance=5):
    """
    Compare two profile pics using perceptual hash.
    """
    h1 = imagehash.phash(Image.open(img1_path))
    h2 = imagehash.phash(Image.open(img2_path))
    dist = h1 - h2
    return dist, dist <= max_distance


if __name__ == "__main__":
    # Example usage
    official_usernames = ["viratkohli", "iamsrk", "neeraj_chopra"]
    candidate_username = "v1ratkohli"

    match, flag = check_username_similarity(candidate_username, official_usernames)
    print(f"Username check → Closest match: {match} | Is impersonation? {flag}")

    # Example profile picture comparison
    # (replace with your actual images)
    try:
        dist, flag = check_profile_pic("data/vip_profile.jpg", "data/suspicious_profile.jpg")
        print(f"Profile pic distance={dist} | Impersonation? {flag}")
    except FileNotFoundError:
        print("⚠️ Skipping image test (no files found). Put sample images in data/ to test.")
