from dotenv import dotenv_values

from cyber_sdk.client.lcd import LCDClient

# human-readable names of ibc denoms
IBC_COIN_NAMES = \
    {
        'ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2': 'uatom in osmosis',
        'ibc/FE2CD1E6828EC0FAB8AF39BAC45BC25B965BA67CCBC50C13A14BD610B0D1E2C4': 'boot in osmosis',
        'ibc/46B44899322F3CD854D2D46DEEF881958467CDD4B3B10086DA49296BBED94BED': 'ujuno in osmosis',
        'ibc/EA4C0A9F72E2CEDF10D0E7A9A6A22954DB3444910DB5BE980DF59B05A46DAD1C': 'udsm in osmosis',
        'ibc/EA1D43981D5C9A1C4AAEA9C23BB1D4FA126BA9BC7020A25E0AE4AA841EA25DC5': 'weth in osmosis',
        'ibc/65381C5F3FD21442283D56925E62EA524DED8B6927F0FF94E21E0020954C40B5': 'weth.grv in osmosis',

        'ibc/15E9C5CF5969080539DB395FA7D9C0868265217EFC528433671AAF9B1912D159': 'uatom in bostrom',
        'ibc/BA313C4A19DFBF943586C0387E6B11286F9E416B4DD27574E6909CABE0E342FA': 'deprecated uatom in bostrom',
        'ibc/13B2C536BB057AC79D5616B8EA1B9540EC1F2170718CAFF6F0083C966FFFED0B': 'uosmo in bostrom',
        'ibc/43DB7553C43D81CB01E9A2644B49A241314B482C2E56F86E85A6539C60383151': 'pussy in bostrom',
        'ibc/9B45B8C514B76D792BEC4850AE601E0E73CE7D307A567F34038432FC80D74780': 'liquidpussy in bostrom',
        'ibc/8D9262E35CAE362FA74AE05E430550757CF8D842EC1B241F645D3CB7179AFD10': 'ujuno in bostrom',
        'ibc/C23D820C5B6009E544AFC8AF5A2FEC288108AEDBFAEFDBBDD6BE54CC23069559': 'ugraviton in bostrom',
        'ibc/B6CAD3F7469F3FAD18ED2230A6C7B15E654AB2E1B66E1C70879C04FEF874A863': 'wei gravETH in bostrom',
        'ibc/4B322204B4F59D770680FE4D7A565DDC3F37BFF035474B717476C66A4F83DD72': 'aevmos in bostrom',
        'ibc/CA5E8F31288514D728AFD1F0533A7F6902AA1192C88C9540F814893C3EAFE244': 'udsm in bostrom'
     }

BOSTROM_RELATED_OSMO_POOLS = (1, 596, 597, 497, 619, 911, 912)

BOSTROM_NODE_RPC_URL = 'https://rpc.bostrom.cybernode.ai:443'  # 'https://rpc.bostrom.bronbro.io:443'
BOSTROM_NODE_LCD_URL = 'https://lcd.bostrom.cybernode.ai/'
BOSTROM_POOLS_BASH_QUERY = f'cyber query liquidity pools --node {BOSTROM_NODE_RPC_URL} -o json'
BOSTROM_CHAIN_ID = 'bostrom'
BOSTROM_LCD_CLIENT = LCDClient(chain_id=BOSTROM_CHAIN_ID, url=BOSTROM_NODE_LCD_URL)

PUSSY_NODE_RPC_URL = 'https://rpc.space-pussy.cybernode.ai:443'
PUSSY_NODE_LCD_URL = 'https://lcd.space-pussy.cybernode.ai/'
PUSSY_POOLS_BASH_QUERY = f'pussy query liquidity pools --node {PUSSY_NODE_RPC_URL} -o json'
PUSSY_CHAIN_ID = 'space-pussy'
PUSSY_LCD_CLIENT = LCDClient(chain_id=PUSSY_CHAIN_ID, url=PUSSY_NODE_LCD_URL)

OSMOSIS_NODE_RPC_URL = 'https://rpc.osmosis-1.bronbro.io:443'
OSMOSIS_NODE_LCD_URL = 'https://lcd.osmosis-1.bronbro.io'
OSMOSIS_POOLS_API_URL = 'https://lcd.osmosis-1.bronbro.io/osmosis/gamm/v1beta1/pools?pagination.limit=1000'  # 'https://lcd-osmosis.keplr.app/osmosis/gamm/v1beta1/pools?pagination.limit=1000'
OSMOSIS_CHAIN_ID = 'osmosis-1'
OSMOSIS_LCD_CLIENT = LCDClient(chain_id=OSMOSIS_CHAIN_ID, url=OSMOSIS_NODE_LCD_URL, prefix='osmo')
OSMOSIS_BASH_PRECOMMAND = dotenv_values(".env")['BASH_PRECOMMAND']

# usual pool fee
POOL_FEE = 0.003

CLI_WALLET = '$WALLET'
