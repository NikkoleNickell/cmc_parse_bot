from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
from create_bot import os



HEADERS = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': os.getenv('API_KEY'),
}


class CoinMarketCap:
    """
    Class for connecting to coinmarketcap.com API
    
    """

    def __init__(self):
        self.url: str = None
        self.parameters: dict = None
        self.session = Session()


    @classmethod
    def connect(cls, url, parameters):

        instance = cls()
        instance.url = url
        instance.parameters = parameters
        instance.session.headers.update(HEADERS)
        
        try:
            response = instance.session.get(url=instance.url, 
                                            params=instance.parameters)
            instance.data = json.loads(response.text)
            return instance
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)


    def get_pairs(self):
        if self.data is None:
            raise ValueError("No data available. Please call connect() first.")
        
        if 'statusCode' in self.data.keys():
            return self.data['statusCode']

        pairs: dict = {}

        for item in self.data['data']:
            pairs[item['name']] = item['quote']['USD']['price']
            
        self.pairs_keys = list(pairs.keys())
        
        return pairs


    def get_pairs_keys(self):
        if self.data is None or 'data' not in self.data:
            raise ValueError("No data available. Please call connect() first.")
        return self.pairs_keys