from typing import Literal


class Token:
    """Represents an authentication token in the Revolt API"""
    
    def __init__(self, token: str, *, session: bool = False):
        self.value = token
        
        self.type: Literal['bot', 'session']
        if session == True:
            self.type = 'session'
        else:
            self.type = 'bot'

    def __repr__(self) -> str:
        return f'<Token type={self.type}>'
