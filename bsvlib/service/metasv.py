import json
from contextlib import suppress
from typing import Optional, List, Dict, Union

import requests

from .provider import Provider
from ..constants import Chain, METASV_TOKEN


class MetaSV(Provider):  # pragma: no cover

    def __init__(self, token: Optional[str] = None, headers: Optional[Dict] = None, timeout: Optional[int] = None):
        super().__init__(Chain.MAIN, headers, timeout)
        self.token = token or METASV_TOKEN
        assert self.token, 'MetaSV service requires a token'
        self.url = 'https://apiv2.metasv.com'
        self.headers.update({'Authorization': f'Bearer {self.token}', })

    def _get_unspents(self, address: str, flag: Optional[str] = None) -> Union[Dict, List[Dict]]:
        with suppress(Exception):
            params = {}
            if flag:
                params['flag'] = flag
            return self.get(url=f'{self.url}/address/{address}/utxo', params=params)
        return []

    def get_unspents(self, **kwargs) -> List[Dict]:
        """
        only P2PKH unspents
        """
        with suppress(Exception):
            address, _, _ = self.parse_kwargs(**kwargs)
            # paging
            paged_unspents: List[Dict] = self._get_unspents(address)
            total_unspents: List[Dict] = paged_unspents
            while paged_unspents:
                paged_unspents = self._get_unspents(address, paged_unspents[-1]['flag'])
                total_unspents.extend(paged_unspents or [])
            # parsing
            unspents: List[Dict] = []
            for item in total_unspents:
                unspent = {'txid': item['txid'], 'vout': item['outIndex'], 'satoshi': item['value'], 'height': item['height']}
                unspent.update(kwargs)
                unspents.append(unspent)
            return unspents
        return []

    def get_balance(self, **kwargs) -> int:
        with suppress(Exception):
            address, _, _ = self.parse_kwargs(**kwargs)
            r: Dict = self.get(url=f'{self.url}/address/{address}/balance')
            return r.get('confirmed') + r.get('unconfirmed')
        return 0

    def broadcast(self, raw: str) -> Optional[str]:
        with suppress(Exception):
            data = json.dumps({'hex': raw})
            r = requests.post(f'{self.url}/tx/broadcast', headers=self.headers, data=data, timeout=self.timeout)
            r.raise_for_status()
            return r.json()['txid']
        return None
