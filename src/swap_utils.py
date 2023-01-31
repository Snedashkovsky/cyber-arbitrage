import pandas as pd
import numpy as np
from typing import Optional

from cyber_sdk.core.bech32 import AccAddress
from cyber_sdk.core.coins import Coins

from src.denom_utils import rename_denom, reverse_rename_denom
from config import BOSTROM_CHAIN_ID, BOSTROM_NODE_RPC_URL, POOL_FEE, BOSTROM_LCD_CLIENT, OSMOSIS_LCD_CLIENT, \
    PUSSY_LCD_CLIENT, CLI_WALLET


def get_pool_value_by_coin(
        pool_balances: list[dict],
        coin_denom: str,
        return_weight: bool = False,
        print_error: bool = False) -> Optional[int]:
    """
    Get coin amount or coin weight from pool balance data
    :param pool_balances: pool balance data
    :param coin_denom: coin denom which should be extracted
    :param return_weight: get weight or amount
    :param print_error: print error or not
    :return: weight or amount
    """

    _value_key = 'weight' if return_weight else 'amount'
    try:
        return [int(item[_value_key]) for item in pool_balances if item['denom'] == coin_denom][0]
    except (KeyError, IndexError) as e:
        if print_error:
            print(f'Key {_value_key} for coin {coin_denom} not fount in {pool_balances}\n{e}')


def get_balance(
        address: str,
        price_df: pd.DataFrame,
        base_coin_denom: str = 'hydrogen') -> [int, Coins]:
    """
    Extract address balance by coins and convert it to base denomination
    :param address: address
    :param price_df: dataframe with price data
    :param base_coin_denom: a base denom
    :return: address balance converted to base denomination and address balance by coins
    """
    assert address[:4] in ('osmo', 'puss', 'bost')
    if address[:4] == 'osmo':
        _lcd_client = OSMOSIS_LCD_CLIENT
    elif address[:4] == 'puss':
        _lcd_client = PUSSY_LCD_CLIENT
    else:
        _lcd_client = BOSTROM_LCD_CLIENT

    _balance_all_coins = _lcd_client.bank.balance(address=AccAddress(address))[0]

    _balance_in_base_coin = 0
    for _coin in _balance_all_coins.to_list():
        _coin_denom = rename_denom(_coin.denom)
        try:
            _balance_in_base_coin += _coin.amount * price_df.loc[base_coin_denom, _coin_denom] \
                if price_df.loc[base_coin_denom, _coin_denom] > 0 else 0
        except KeyError:
            print(f'{_coin_denom} not found in price_df')
            pass
    return int(_balance_in_base_coin) if not np.isnan(_balance_in_base_coin) else 0, _balance_all_coins


def generate_swap_bash_query(
        coin_from_amount: float,
        coin_from_denom: str,
        coin_to_denom: str,
        coins_pool_df: pd.DataFrame,
        price_df: pd.DataFrame,
        max_slippage: float = 0.15,
        wallet: str = CLI_WALLET,
        chain_id: str = BOSTROM_CHAIN_ID,
        node_rpc_url: str = BOSTROM_NODE_RPC_URL) -> str:
    """
    Generate swap CLI bash query for bostrom network
    :param coin_from_amount: coin amount from
    :param coin_from_denom: coin denom from
    :param coin_to_denom: coin denom to
    :param coins_pool_df: dataframe with a pool in which coins should be swapped
    :param price_df: dataframe with price data
    :param max_slippage: max slippage
    :param wallet: wallet name/address in CLI
    :param chain_id: chain id
    :param node_rpc_url: URL of RPC node
    :return: swap bash query for bostrom network
    """
    _pool_id = coins_pool_df.loc[:, 'id'].to_list()[0]
    _pool_type = coins_pool_df.loc[:, 'type_id'].to_list()[0]
    _price = price_df.loc[coin_from_denom, coin_to_denom] * (1 + max_slippage)
    return f'cyber tx liquidity swap {_pool_id} {_pool_type} {int(coin_from_amount)}{reverse_rename_denom(coin_from_denom)}' \
           f' {reverse_rename_denom(coin_to_denom)} {_price:.12f} 0.003 ' \
           f'--from {wallet} --chain-id {chain_id} --gas 200000 --gas-prices 0.01boot --yes ' \
           f'--node {node_rpc_url} --broadcast-mode block'


def generate_swap_bash_queries(
        way: list,
        coin1_amount: float,
        pools_df: pd.DataFrame,
        price_df: pd.DataFrame) -> [float, list]:
    """
    Generate swap CLI bash queries for bostrom network
    :param way: list of swap ways
    :param coin1_amount: initial coin amount
    :param pools_df: dataframe with pool data
    :param price_df: dataframe with price data
    :return: predicted result and list of swap bash queries for bostrom network
    """
    _coin_from_amount = coin1_amount
    _coin2_way_queries = []
    for _way_item in way:
        _coin_from_denom = _way_item[0]
        _coin_to_denom = _way_item[1]
        _coins_pool_df = pools_df[(pools_df.reserve_coin_denoms.isin([[_coin_from_denom, _coin_to_denom]])) | (
            pools_df.reserve_coin_denoms.isin([[_coin_to_denom, _coin_from_denom]]))]
        _coin_from_pool_amount = get_pool_value_by_coin(_coins_pool_df.balances.values[0], _coin_from_denom)
        _coin_to_pool_amount = get_pool_value_by_coin(_coins_pool_df.balances.values[0], _coin_to_denom)
        _coin_to_amount = _coin_from_amount * _coin_to_pool_amount / (
                    _coin_from_pool_amount + 2 * _coin_from_amount) * (1 - POOL_FEE)
        _coin2_way_queries.append(
            generate_swap_bash_query(
                coin_from_amount=_coin_from_amount, coin_from_denom=_coin_from_denom, coin_to_denom=_coin_to_denom,
                coins_pool_df=_coins_pool_df, price_df=price_df))
        _coin_from_amount = _coin_to_amount
    return _coin_from_amount, _coin2_way_queries
