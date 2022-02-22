class AuthToken:
    """Represents an authentication token in the Revolt API"""
    
    def __init__(self, client, token: str, *, session: bool = False):
        self.client = client
        self.value = token
        self.is_bot = not session

    def __repr__(self) -> str:
        if self.is_bot:
            return f"<Token type='bot'>"
        
        return f"<Token type='session'>"
    
    @property
    def headers(self):
        if self.is_bot is True:
            return {"x-bot-token": self.value}
        
        return {"x-session-token": self.value}

    @property
    def payload(self):
        return {"token": self.value}

    @classmethod
    def create_session(cls, client, email: str, password: str): 
        ...
