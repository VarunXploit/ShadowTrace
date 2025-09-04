from backend.threat_detector import ThreatDetector
from backend.impersonation import ImpersonationDetector
from backend.fake_detector import AccountVerifier   # changed

class VIPDetectionPipeline:
    def __init__(self, official_usernames=None):
        self.threat_detector = ThreatDetector()
        self.account_verifier = AccountVerifier()   # changed
        self.impersonation_detector = ImpersonationDetector(official_usernames)

    def check_text(self, text):
        return self.threat_detector.predict(text)

    def check_account(self, account_dict):
        return self.account_verifier.verify(account_dict)   # changed

    def check_username(self, username):
        return self.impersonation_detector.check_username(username)

    def check_profile_pic(self, vip_img, sus_img):
        return self.impersonation_detector.check_profile_pic(vip_img, sus_img)
