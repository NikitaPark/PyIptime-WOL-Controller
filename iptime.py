import requests
import re
from bs4 import BeautifulSoup

class SessionTimeout(Exception):
    def __init__(self):
        super().__init__('Session has timed out. Login again to use the controller.')

class SessionNotFound(Exception):
    def __init__(self):
        super().__init__('Session dose not exist. Login is required to use the controller.')

class AuthenticationFailed(Exception):
    def __init__(self):
        super().__init__('Authentication is failed. Check your username and password.')

class ConnectionFailed(Exception):
    def __init__(self):
        super().__init__('Failed to connect to router. Check connection to router')

class WOLController:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

        try:
            _target_url = f'http://{self.host}:{self.port}'
            requests.get(url=_target_url, timeout=10)
            self.url = _target_url
        except requests.ConnectTimeout as e:
            raise ConnectionFailed

    def check_session_timeout(self, response) -> None:
        if '//session_timeout' in response: raise SessionTimeout
        
    def login(self, username: str, password: str) -> None:
        target_url = f'{self.url}/sess-bin/login_handler.cgi'
        header = {'Referer': self.url + '/sess-bin/login-session.cgi'}
        data = {'username': username, 'passwd': password}
        res = requests.post(url=target_url, headers=header, data=data)
        
        if '//session_timeout' in res.text:
            raise AuthenticationFailed
        else:
            self.session = {'efm_session_id': re.search(r"setCookie\('([A-Za-z0-9]+)'\);", res.text).group(1)}

    def get_wol_list(self):
        try:
            target_url = f'{self.url}/sess-bin/timepro.cgi'
            params = {'tmenu': 'iframe', 'smenu': 'expertconfwollist'}
            header = {'Referer': f'{self.url}/sess-bin/timepro.cgi?tmenu=expertconf&smenu=remotepc'}
            
            res = requests.get(url=target_url, params=params, headers=header, cookies=self.session)
            
            if self.check_session_timeout(response=res.text):
                raise AuthenticationFailed
            
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.find_all('tr', attrs={'class': 'wol_main_tr'})
            rows.pop(0)

            ret_data = []
            for row in rows:
                target_info = {}
                cols = row.find_all('td')
                
                if len(cols) == 6:
                    target_info['id'] = cols[0].find('p').get_text()
                    target_info['mac_addr'] = cols[1].find('span').get_text()
                    target_info['desc'] = cols[2].find('span').get_text()
                    ret_data.append(target_info)
                else:
                    return ret_data
        
        except requests.Timeout:
            raise ConnectionFailed

    def do_wake_pc(self, mac_addr: str) -> None | bool:
        if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac_addr):
            return False

        mac_addr = mac_addr.upper().replace('-', ':')

        try:
            target_url = f'{self.url}/sess-bin/timepro.cgi' 
            params = {'tmenu': 'iframe', 'smenu': 'expertconfwollist', 'nomore': 0, 'wakeupchk': {mac_addr}, 'act': 'wake'}
            header = {'Referer': f'{self.url}/sess-bin/timepro.cgi?tmenu=iframe&smenu=expertconfwollist'}
            res = requests.post(url=target_url, data=params, headers=header, cookies=self.session)
        
        except requests.Timeout:
            raise ConnectionFailed

        return True