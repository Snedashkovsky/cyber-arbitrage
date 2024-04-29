from functools import cache

from cyberutils.contract import query_contract

from config import IBC_COIN_NAMES, BOSTROM_NODE_LCD_URL, BOSTROM_OCR_CONTRACT


@cache
def rename_denom(denom: str, denom_names_dict: dict = IBC_COIN_NAMES) -> str:
    """
    Rename denoms to human-readable names
    :param denom: network denom
    :param denom_names_dict: dictionary with human-readable names
    :return: human-readable name
    """
    return denom_names_dict[denom] if denom in denom_names_dict.keys() else denom


@cache
def reverse_rename_denom(denom: str, denom_names_dict: dict = IBC_COIN_NAMES) -> str:
    """
    Rename denoms from human-readable to network names
    :param denom: human-readable name
    :param denom_names_dict: dictionary with human-readable names
    :return: network name
    """
    denom_names_reverse_dict = {v: k for k, v in denom_names_dict.items()}
    return denom_names_reverse_dict.get(denom, denom.removesuffix('(pussy)'))


@cache
def get_asset_metadata_from_ocr_contract(
        chain_name: str,
        asset_denom: str,
        contract_address: str = BOSTROM_OCR_CONTRACT,
        node_lcd_url: str = BOSTROM_NODE_LCD_URL
) -> dict:
    """
    Get asset metadata from On-Chain Registry contract
    (https://github.com/Snedashkovsky/on-chain-registry?tab=readme-ov-file#assets)
    :param chain_name: the chain name
    :param asset_denom: the raw asset denom in the chain
    :param contract_address: the OCR contract address
    :param node_lcd_url: the LCD node url for getting asset metadata for the OCR contract
    :return: asset metadata json
    """
    return query_contract(
        contract_address=contract_address,
        query={'get_asset':
                   {'chain_name': chain_name,
                    'base': asset_denom}},
        node_lcd_url=node_lcd_url)


@cache
def get_readable_asset_denom_from_ocr_contract(
        chain_name: str,
        asset_denom: str,
        contract_address: str = BOSTROM_OCR_CONTRACT,
        node_lcd_url: str = BOSTROM_NODE_LCD_URL
) -> str:
    """
    Get human-readable asset denom from On-Chain Registry contract
    (https://github.com/Snedashkovsky/on-chain-registry?tab=readme-ov-file#assets)
    :param chain_name: the chain name
    :param asset_denom: the raw asset denom in the chain
    :param contract_address: the OCR contract address
    :param node_lcd_url: the LCD node url for getting asset metadata for the OCR contract
    :return: human-readable asset denom from OCR contract
    """
    if asset_denom[:4] != 'ibc/':
        return asset_denom

    asset_metadata = get_asset_metadata_from_ocr_contract(
        chain_name=chain_name,
        asset_denom=asset_denom,
        contract_address=contract_address,
        node_lcd_url=node_lcd_url
    )
    assert 'data' in asset_metadata.keys() and {'chain_name', 'asset'}.issubset(set(asset_metadata['data'].keys()))
    assert asset_metadata['data']['chain_name'] == chain_name

    if 'denom_units' in asset_metadata['data']['asset'].keys() and asset_metadata['data']['asset']['denom_units']:
        denom_units = asset_metadata['data']['asset']['denom_units']
        asset_readable_denom = [item['denom'] for item in denom_units if item['exponent'] == 0][0]
    elif 'traces' in asset_metadata['data']['asset'].keys() and asset_metadata['data']['asset']['traces']:
        trace = asset_metadata['data']['asset']['traces'][-1]
        asset_readable_denom = trace['counterparty']['base_denom']
    else:
        return asset_denom

    if (asset_readable_denom[:8] == 'factory/' and
            'symbol' in asset_metadata['data']['asset'].keys() and
            asset_metadata['data']['asset']['symbol']):
        asset_readable_denom = asset_metadata['data']['asset']['symbol']

    return f'{asset_readable_denom} in {chain_name}'


@cache
def get_readable_asset_denom(
        chain_name: str,
        asset_denom: str,
        contract_address: str = BOSTROM_OCR_CONTRACT,
        node_lcd_url: str = BOSTROM_NODE_LCD_URL
) -> str:
    """
    Get human-readable asset denom from the config dictionary (config.py) or On-Chain Registry contract
    (https://github.com/Snedashkovsky/on-chain-registry?tab=readme-ov-file#assets)
    :param chain_name: the chain name
    :param asset_denom: the raw asset denom in the chain
    :param contract_address: the OCR contract address
    :param node_lcd_url: the LCD node url for getting asset metadata for the OCR contract
    :return: human-readable asset denom
    """
    asset_renamed_denom = rename_denom(denom=asset_denom)
    if asset_renamed_denom == asset_denom and asset_denom[:4] == 'ibc/':
        return get_readable_asset_denom_from_ocr_contract(
            chain_name=chain_name,
            asset_denom=asset_denom,
            contract_address=contract_address,
            node_lcd_url=node_lcd_url
        )
    return asset_renamed_denom
