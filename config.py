from cyber_sdk.client.lcd import LCDClient, AsyncLCDClient


IBC_COIN_NAMES = \
    {
        'ibc/15E9C5CF5969080539DB395FA7D9C0868265217EFC528433671AAF9B1912D159': 'uatom in bostrom',
        'ibc/BA313C4A19DFBF943586C0387E6B11286F9E416B4DD27574E6909CABE0E342FA': 'deprecated uatom in bostrom',
        'ibc/13B2C536BB057AC79D5616B8EA1B9540EC1F2170718CAFF6F0083C966FFFED0B': 'uosmo in bostrom',
        'ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2': 'uatom in osmosis',
        'ibc/FE2CD1E6828EC0FAB8AF39BAC45BC25B965BA67CCBC50C13A14BD610B0D1E2C4': 'boot in osmosis',
        'ibc/43DB7553C43D81CB01E9A2644B49A241314B482C2E56F86E85A6539C60383151': 'pussy in bostrom'
     }

BOSTROM_RELATED_OSMO_POOLS = (1, 596, 597)
BOSTROM_NODE_RPC_URL = 'https://rpc.bostrom.bronbro.io:443'
BOSTROM_NODE_LCD_URL = 'https://lcd.bostrom.bronbro.io/'
BOSTROM_POOLS_BASH_QUERY = f'cyber query liquidity pools --node {BOSTROM_NODE_RPC_URL} -o json'

OSMOSIS_NODE_RPC_URL = 'https://rpc.osmosis-1.bronbro.io:443'
OSMOSIS_NODE_LCD_URL = 'https://lcd.osmosis-1.bronbro.io'
OSMOSIS_POOLS_API_URL = 'https://lcd-osmosis.keplr.app/osmosis/gamm/v1beta1/pools?pagination.limit=750'

POOL_FEE = 0.003

CHAIN_ID = 'bostrom'
CYBER_LCD_CLIENT = LCDClient(chain_id=CHAIN_ID, url=BOSTROM_NODE_LCD_URL)
CYBER_ASYNC_LCD_CLIENT = AsyncLCDClient(chain_id=CHAIN_ID, url=BOSTROM_NODE_LCD_URL)

WALLET = '$WALLET'
