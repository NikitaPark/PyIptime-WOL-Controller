import requests
import re
from bs4 import BeautifulSoup

class WOLController:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def check_connection(self) -> bool:
        target_url = f'http://{self.host}:{self.port}'
        
        try:
            requests.get(url=target_url, timeout=10)
            self.url = target_url    
            return True  
        except Exception as e:
            print(e)
            return False
        
    def login(self, username: str, password: str) -> bool:
        target_url = f'{self.url}/sess-bin/login_handler.cgi'
        header = {'Referer': self.url + '/sess-bin/login-session.cgi'}
        data = {'username': username, 'passwd': password}

        res = requests.post(url=target_url, headers=header, data=data)
        
        self.session = {'efm_session_id': re.search(r"setCookie\('([A-Za-z0-9]+)'\);", res.text).group(1)}

    def get_wol_list(self):
        target_url = f'{self.url}/sess-bin/timepro.cgi'
        params = {'tmenu': 'iframe', 'smenu': 'expertconfwollist'}
        header = {'Referer': f'{self.url}/sess-bin/timepro.cgi?tmenu=expertconf&smenu=remotepc'}
        
        res = requests.get(url=target_url, params=params, headers=header, cookies=self.session)
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

    def do_wake_pc(self, mac_addr: str) -> None | bool:
        if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac_addr):
            return False

        mac_addr = mac_addr.upper().replace('-', ':')

        target_url = f'{self.url}/sess-bin/timepro.cgi'
        params = {'tmenu': 'iframe', 'smenu': 'expertconfwollist', 'nomore': 0, 'wakeupchk': {mac_addr}, 'act': 'wake'}
        header = {'Referer': f'{self.url}/sess-bin/timepro.cgi?tmenu=iframe&smenu=expertconfwollist'}

        res = requests.post(url=target_url, data=params, headers=header, cookies=self.session)
        print(res.request.body)
        
        return True