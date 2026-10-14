import requests
import config

class Member5Client:
    def __init__(self, api_url=config.MEMBER5_API_URL):
        self.api_url = api_url
        self.session = requests.Session()
        self.connected = False
        self.last_status = "Not sent yet"

    def send_detection(self, payload):
        """
        Transmits Member 2 JSON to Member 5 FastAPI endpoint:
        POST /detection/
        
        Returns: (success: bool, info: str)
        """
        try:
            resp = self.session.post(
                self.api_url,
                json=payload,
                timeout=0.6,
                headers={"Content-Type": "application/json"}
            )
            if resp.status_code in (200, 201):
                self.connected = True
                self.last_status = f"HTTP {resp.status_code} OK"
                return True, self.last_status
            else:
                self.last_status = f"HTTP {resp.status_code}: {resp.text[:60]}"
                return False, self.last_status
        except requests.exceptions.RequestException as e:
            self.connected = False
            self.last_status = f"Offline (Member 5 endpoint {self.api_url} not active)"
            return False, self.last_status
