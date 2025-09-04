import asyncio
import re
from datetime import datetime
from statistics import median
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from typing import Dict, Any

# ----------------- SCRAPER -----------------
async def scrape_instagram_profile(username: str) -> dict:
    """
    Scrapes Instagram profile info (followers, following, posts, bio, verified badge, engagement).
    """
    print(f"Attempting to scrape profile: {username}...")
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()

        try:
            url = f"https://www.instagram.com/{username}/"
            await page.goto(url, timeout=20000)
            
            # Wait for page to load
            await asyncio.sleep(3)

            # Check if unavailable
            page_title = await page.title()
            if "page not found" in page_title.lower() or "unavailable" in page_title.lower():
                await browser.close()
                return {"error": "Profile not found or private."}

            print("Profile loaded successfully.")

            # --- Stats (Updated selectors) ---
            stats = {'posts': 0, 'followers': 0, 'following': 0}
            
            try:
                # Try multiple selectors for stats
                stat_selectors = [
                    'header section ul li',
                    'header div ul li',
                    'main header section ul li'
                ]
                
                stat_elements = []
                for selector in stat_selectors:
                    stat_elements = await page.locator(selector).all()
                    if stat_elements:
                        break
                
                for i, element in enumerate(stat_elements[:3]):  # First 3 elements are usually posts, followers, following
                    try:
                        text_content = await element.inner_text()
                        # Extract number from text
                        number_match = re.search(r'([\d,]+\.?\d*[KkMm]?)', text_content)
                        if number_match:
                            value_str = number_match.group(1).lower()
                            value = 0
                            if 'k' in value_str:
                                value = int(float(value_str.replace('k', '').replace(',', '')) * 1000)
                            elif 'm' in value_str:
                                value = int(float(value_str.replace('m', '').replace(',', '')) * 1000000)
                            else:
                                try:
                                    value = int(value_str.replace(',', ''))
                                except:
                                    value = 0
                            
                            # Assign based on position (Instagram order: posts, followers, following)
                            if i == 0:
                                stats['posts'] = value
                            elif i == 1:
                                stats['followers'] = value
                            elif i == 2:
                                stats['following'] = value
                    except Exception as e:
                        print(f"Error parsing stat element {i}: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error extracting stats: {e}")

            # --- Bio & Verified Badge ---
            bio = ""
            try:
                bio_selectors = [
                    'header section div div span',
                    'main header section div div span',
                    'header div div span'
                ]
                
                for selector in bio_selectors:
                    bio_elements = await page.locator(selector).all()
                    if bio_elements:
                        bio = await bio_elements[0].inner_text()
                        break
            except Exception as e:
                print(f"Error extracting bio: {e}")

            # Check for verified badge
            verified = False
            try:
                verified_selectors = [
                    "svg[aria-label='Verified']",
                    "[data-testid='verified-icon']",
                    "svg[title='Verified']"
                ]
                
                for selector in verified_selectors:
                    verified_count = await page.locator(selector).count()
                    if verified_count > 0:
                        verified = True
                        break
            except Exception as e:
                print(f"Error checking verified status: {e}")

            # --- Recent Posts Engagement (Simplified) ---
            likes_list = []
            post_dates = []

            try:
                # Get post links
                post_selectors = [
                    'article a[href*="/p/"]',
                    'main article a[href*="/p/"]',
                    'div a[href*="/p/"]'
                ]
                
                posts = []
                for selector in post_selectors:
                    posts = await page.locator(selector).all()
                    if posts:
                        break
                
                # Analyze first 3 posts only to avoid rate limiting
                for i, post in enumerate(posts[:3]):
                    try:
                        href = await post.get_attribute("href")
                        if not href:
                            continue
                            
                        print(f"Analyzing post {i+1}...")
                        await page.goto(f"https://www.instagram.com{href}")
                        await asyncio.sleep(2)  # Wait for post to load
                        
                        # Try to get post date
                        try:
                            time_element = await page.locator("time").first.wait_for(timeout=5000)
                            ts = await time_element.get_attribute("datetime")
                            if ts:
                                post_dates.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
                        except:
                            pass

                        # Try to get likes count
                        try:
                            # Multiple selectors for likes
                            likes_selectors = [
                                'section span[role="button"]',
                                'section span',
                                'article section span'
                            ]
                            
                            for selector in likes_selectors:
                                likes_elements = await page.locator(selector).all()
                                for element in likes_elements:
                                    likes_text = await element.inner_text()
                                    if 'like' in likes_text.lower():
                                        # Extract number
                                        numbers = re.findall(r'([\d,]+)', likes_text)
                                        if numbers:
                                            likes_val = int(numbers[0].replace(',', ''))
                                            likes_list.append(likes_val)
                                            break
                                if likes_list and len(likes_list) > i:  # Found likes for this post
                                    break
                        except Exception as like_error:
                            print(f"Error getting likes for post {i+1}: {like_error}")
                            continue
                            
                    except Exception as post_error:
                        print(f"Error analyzing post {i+1}: {post_error}")
                        continue
                        
            except Exception as e:
                print(f"Error analyzing posts: {e}")

            await browser.close()

            return {
                "username": username,
                "follower_count": stats['followers'],
                "following_count": stats['following'],
                "post_count": stats['posts'],
                "bio": bio,
                "verified": verified,
                "recent_likes": likes_list,
                "post_dates": post_dates
            }

        except PlaywrightTimeoutError:
            await browser.close()
            return {"error": "Timeout loading Instagram page"}
        except Exception as e:
            await browser.close()
            return {"error": f"Unexpected error: {str(e)}"}

# ----------------- FEATURE ENGINEERING -----------------
def calculate_features(scraped: Dict[str, Any]) -> Dict[str, Any]:
    features = {}

    # 1. Engagement Rate
    followers = scraped.get("follower_count", 0)
    likes = scraped.get("recent_likes", [])
    if followers > 0 and likes:
        avg_likes = sum(likes) / len(likes)
        features["engagement_rate"] = round((avg_likes / followers) * 100, 2)
    else:
        features["engagement_rate"] = 0

    # 2. Profile Age (Earliest Post Date)
    post_dates = scraped.get("post_dates", [])
    if post_dates:
        earliest = min(post_dates)
        age_days = (datetime.now(earliest.tzinfo) - earliest).days
        age_years = age_days / 365
        features["profile_age_years"] = round(age_years, 1)
    else:
        features["profile_age_years"] = 0

    # 3. Verified Badge
    features["verified"] = scraped.get("verified", False)

    # 4. Bio Presence
    bio = scraped.get("bio", "")
    if not bio or len(bio.strip()) < 5:
        features["bio_quality"] = "low"
    else:
        features["bio_quality"] = "good"

    # 5. Follower/Following Ratio
    followers = scraped.get("follower_count", 0)
    following = scraped.get("following_count", 1)  # Avoid division by zero
    features["follower_following_ratio"] = round(followers / following, 2)

    # 6. Placeholder: Image Reuse Detection (phash)
    features["image_reuse_penalty"] = 0  # default = no penalty

    return features

# ----------------- SCORING -----------------
def calculate_authenticity_score(features: Dict[str, Any]) -> Dict[str, Any]:
    score = 0
    evidence = []

    # Verified Badge
    if features["verified"]:
        score += 50
        evidence.append("Verified badge present (+50)")
    else:
        evidence.append("No verified badge")

    # Profile Age
    age_years = features["profile_age_years"]
    if age_years >= 3:
        score += 20
        evidence.append(f"Profile age {age_years} years (+20)")
    elif age_years >= 1:
        score += 10
        evidence.append(f"Profile age {age_years} years (+10)")
    else:
        score -= 10
        evidence.append(f"Profile too new ({age_years} years) (-10)")

    # Engagement Rate
    er = features["engagement_rate"]
    if 2 <= er <= 10:
        score += 15
        evidence.append(f"Healthy engagement rate {er}% (+15)")
    elif 0.5 <= er < 2:
        score += 5
        evidence.append(f"Low but normal engagement rate {er}% (+5)")
    elif er > 10:
        score -= 10
        evidence.append(f"Suspiciously high engagement rate {er}% (-10)")
    else:
        score -= 5
        evidence.append(f"Very low engagement rate {er}% (-5)")

    # Bio Quality
    if features["bio_quality"] == "good":
        score += 15
        evidence.append("Complete bio (+15)")
    else:
        score -= 15
        evidence.append("Empty/poor bio (-15)")

    # Follower/Following Ratio
    ratio = features["follower_following_ratio"]
    if ratio > 10:
        score += 10
        evidence.append(f"Good follower ratio ({ratio:.1f}) (+10)")
    elif ratio > 1:
        score += 5
        evidence.append(f"Decent follower ratio ({ratio:.1f}) (+5)")
    else:
        score -= 5
        evidence.append(f"Poor follower ratio ({ratio:.1f}) (-5)")

    # Image Reuse Penalty
    penalty = features["image_reuse_penalty"]
    score -= penalty
    if penalty > 0:
        evidence.append(f"Image reuse detected (-{penalty})")

    # Ensure score is within bounds
    score = max(0, min(100, score))

    # Final Decision
    if score >= 70:
        status = "Authentic"
    elif 40 <= score < 70:
        status = "Suspicious"
    else:
        status = "Likely Fake"

    return {"score": score, "status": status, "evidence": evidence}

# ----------------- MAIN -----------------
async def main():
    print("Instagram Profile Authenticity Checker")
    print("=" * 40)
    
    username = input("Enter Instagram username (without @): ").strip().replace('@', '')
    
    if not username:
        print("Please enter a valid username.")
        return
        
    print(f"\nAnalyzing @{username}...")
    scraped = await scrape_instagram_profile(username)

    if "error" in scraped:
        print("❌ Error:", scraped["error"])
        return

    features = calculate_features(scraped)
    result = calculate_authenticity_score(features)

    print("\n" + "="*50)
    print("PROFILE ANALYSIS RESULTS")
    print("="*50)
    print(f"Username: @{scraped['username']}")
    print(f"Followers: {scraped['follower_count']:,}")
    print(f"Following: {scraped['following_count']:,}")
    print(f"Posts: {scraped['post_count']:,}")
    print(f"Verified: {'✅ Yes' if scraped['verified'] else '❌ No'}")
    print(f"Bio: {scraped['bio'][:100]}..." if len(scraped['bio']) > 100 else f"Bio: {scraped['bio']}")
    
    print(f"\n📊 FEATURES:")
    print(f"Engagement Rate: {features['engagement_rate']:.2f}%")
    print(f"Profile Age: {features['profile_age_years']} years")
    print(f"Bio Quality: {features['bio_quality']}")
    print(f"Follower/Following Ratio: {features['follower_following_ratio']:.2f}")
    
    print(f"\n🎯 AUTHENTICITY ASSESSMENT:")
    print(f"Score: {result['score']}/100")
    
    # Add color coding for status
    status = result['status']
    if 'Highly Authentic' in status or 'Likely Authentic' in status:
        print(f"Status: ✅ {status}")
    elif 'Uncertain' in status:
        print(f"Status: ⚠ {status}")
    else:
        print(f"Status: ❌ {status}")
    
    print(f"\n📝 Analysis Details:")
    for ev in result['evidence']:
        print(f"  {ev}")
        
    print(f"\nRecent post likes: {scraped['recent_likes']}")

if __name__ == "_main_":
    asyncio.run(main())
