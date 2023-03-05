import requests
import pandas as pd
import numpy as np
from math import isnan
from IPython.core.display import display, HTML
from pandarallel import pandarallel
from itertools import permutations
from typing import Optional

from src.bash_utils import get_json_from_bash_query
from src.swap_utils import get_pool_value_by_coin
from src.denom_utils import rename_denom, reverse_rename_denom
from config import BOSTROM_RELATED_OSMO_POOLS, BOSTROM_POOLS_BASH_QUERY, OSMOSIS_POOLS_API_URL, BOSTROM_NODE_RPC_URL, \
    PUSSY_POOLS_BASH_QUERY, PUSSY_NODE_RPC_URL, COINS_IN_DIFFERENT_CHAINS


def get_pools_cyber(network: str = 'bostrom',
                    display_data: bool = False,
                    recalculate_pools: bool = True,
                    cyber_pools_bash_query: str = None) -> pd.DataFrame:
    """
    Extract pools data from cyber protocol network
    :param network: cyber protocol network name
    :param display_data: display or not pool data
    :param recalculate_pools: update or not pool list
    :param cyber_pools_bash_query: bash query for getting pool data
    :return: dataframe with pools data
    """
    assert network in ('bostrom', 'pussy', 'space-pussy')
    if cyber_pools_bash_query is None and network == 'bostrom':
        cyber_pools_bash_query = BOSTROM_POOLS_BASH_QUERY
    elif cyber_pools_bash_query is None and network in ('pussy', 'space-pussy'):
        cyber_pools_bash_query = PUSSY_POOLS_BASH_QUERY

    if recalculate_pools:
        _pools_cyber_json = get_json_from_bash_query(cyber_pools_bash_query)
        _pools_cyber_df = pd.DataFrame(_pools_cyber_json['pools'])
        _pools_cyber_df.to_csv('data/bostrom_pools.csv')
    else:
        _pools_cyber_df = pd.read_csv('data/bostrom_pools.csv',
                                      converters={'reserve_coin_denoms': lambda x: x.strip("['']").split("', '")})

    pandarallel.initialize(nb_workers=len(_pools_cyber_df), verbose=1)
    _pools_cyber_df['balances'] = \
        _pools_cyber_df['reserve_account_address'].parallel_map(
            lambda address: get_json_from_bash_query(
                f'cyber query bank balances {address} --node {BOSTROM_NODE_RPC_URL} -o json' if network == 'bostrom'
                else f'pussy query bank balances {address} --node {PUSSY_NODE_RPC_URL} -o json')['balances'])
    _pools_cyber_df['balances'] = \
        _pools_cyber_df['balances'].map(lambda x: [{'denom': rename_denom(item['denom']), 'amount': item['amount']}
                                                   for item in x])
    _pools_cyber_df['reserve_coin_denoms'] = \
        _pools_cyber_df['reserve_coin_denoms'].map(lambda x: [rename_denom(item) for item in x])
    _pools_cyber_df['swap_fee'] = 0.003
    _pools_cyber_df['network'] = network
    if display_data:
        print('Bostrom Pools')
        display(HTML(_pools_cyber_df.to_html(index=False, notebook=True, show_dimensions=False)))
    return _pools_cyber_df


def get_pools_osmosis(display_data: bool = False,
                      recalculate_pools: bool = True,
                      osmosis_pools_api_url: str = OSMOSIS_POOLS_API_URL,
                      bostrom_related_osmo_pools: tuple = BOSTROM_RELATED_OSMO_POOLS,
                      min_uosmo_balance: int = 10_000_000) -> pd.DataFrame:
    """
    Extract pools data from osmosis network
    :param display_data: display or not pool data
    :param recalculate_pools: update or not pool list
    :param osmosis_pools_api_url: API for getting pool data
    :param bostrom_related_osmo_pools: list of bostrom related pool ids
    :param min_uosmo_balance: min balance in pool for excluding empty pools from calculations
    :return: dataframe with pools data
    """
    _pools_osmosis_json = requests.get(osmosis_pools_api_url).json()
    _pools_osmosis_df = pd.DataFrame(_pools_osmosis_json['pools'])
    _pools_osmosis_df['id'] = _pools_osmosis_df['id'].astype(int)
    _pools_osmosis_df = \
        _pools_osmosis_df[_pools_osmosis_df['@type'] != '/osmosis.gamm.poolmodels.stableswap.v1beta1.Pool']
    _pools_osmosis_df['type_id'] = _pools_osmosis_df['@type'].map(
        lambda x: 1 if x == '/osmosis.gamm.v1beta1.Pool' else 0)
    _pools_osmosis_df['total_weight'] = _pools_osmosis_df['total_weight'].fillna(0).astype(int)
    _pools_osmosis_df['balances'] = _pools_osmosis_df['pool_assets'].map(
        lambda x: [
            {'denom': rename_denom(item['token']['denom']),
             'amount': item['token']['amount'],
             'weight': item['weight']} for item in x])
    _pools_osmosis_df['denoms_count'] = _pools_osmosis_df['pool_assets'].map(lambda x: len(x))
    _pools_osmosis_df['swap_fee'] = _pools_osmosis_df['pool_params'].map(lambda x: float(x['swap_fee']))
    _pools_osmosis_df['exit_fee'] = _pools_osmosis_df['pool_params'].map(lambda x: float(x['exit_fee']))
    _pools_osmosis_df['reserve_coin_denoms'] = _pools_osmosis_df['pool_assets'].map(
        lambda x: [item['token']['denom'] for item in x])
    _pools_osmosis_df['reserve_coin_denoms'] = \
        _pools_osmosis_df['reserve_coin_denoms'].map(lambda x: [rename_denom(item) for item in x])
    _pools_osmosis_df['network'] = 'osmosis'
    if min_uosmo_balance:
        _pools_osmosis_df.loc[:, 'uosmo_balance'] = \
            _pools_osmosis_df.balances.map(lambda x: get_pool_value_by_coin(x, 'uosmo'))
        _pools_osmosis_df.loc[:, 'uatom_balance'] = \
            _pools_osmosis_df.balances.map(
                lambda x: get_pool_value_by_coin(x, reverse_rename_denom('uatom in osmosis')))
        _pools_osmosis_df = \
            _pools_osmosis_df[
                ((_pools_osmosis_df.uosmo_balance.isna()) & (_pools_osmosis_df.uosmo_balance.isna())) |
                ((_pools_osmosis_df.uosmo_balance > min_uosmo_balance) | (
                        _pools_osmosis_df.uatom_balance > min_uosmo_balance // 10))]
    if display_data:
        print('Osmosis Pools')
        display(HTML(
            _pools_osmosis_df
            .sort_values('total_weight', ascending=False).to_html(
                index=False, notebook=True, show_dimensions=False)))
    return _pools_osmosis_df


def get_pools(display_data: bool = False,
              recalculate_pools: bool = True,
              networks=None,
              bostrom_related_osmo_pools: Optional[tuple] = BOSTROM_RELATED_OSMO_POOLS) -> pd.DataFrame:
    """
    Extract pools data from osmosis, bostrom and space-pussy network
    :param display_data: display or not pool data
    :param recalculate_pools: update or not pool list
    :param networks: a list of `bostrom`, `space-pussy` or `osmosis` networks, all of them are extracted by default
    :param bostrom_related_osmo_pools: tuple of bostrom related pool ids in osmosis network or None for all pools
    :return: dataframe with pools data
    """

    networks = networks if networks else ['bostrom', 'space-pussy', 'osmosis']

    _pools_df = pd.DataFrame(columns=['network', 'id', 'type_id', 'balances', 'reserve_coin_denoms', 'swap_fee'])

    if 'bostrom' in networks:
        _pools_bostrom_df = \
            get_pools_cyber(network='bostrom', display_data=display_data, recalculate_pools=recalculate_pools)[
                ['network', 'id', 'type_id', 'balances', 'reserve_coin_denoms', 'swap_fee']]
        _pools_df = pd.concat([_pools_df, _pools_bostrom_df])
    if 'space-pussy' in networks:
        _pools_pussy_df = \
            get_pools_cyber(network='space-pussy', display_data=display_data, recalculate_pools=recalculate_pools)[
                ['network', 'id', 'type_id', 'balances', 'reserve_coin_denoms', 'swap_fee']]
        _pools_df = pd.concat([_pools_df, _pools_pussy_df])
    if 'osmosis' in networks:
        _pools_osmosis_df = get_pools_osmosis(display_data=display_data, recalculate_pools=recalculate_pools)[
            ['network', 'id', 'type_id', 'balances', 'reserve_coin_denoms', 'swap_fee']]
        _pools_osmosis_df = \
            _pools_osmosis_df[_pools_osmosis_df.id.isin(
                bostrom_related_osmo_pools)] if bostrom_related_osmo_pools else _pools_osmosis_df
        _pools_df = pd.concat([_pools_df, _pools_osmosis_df])
    return _pools_df


def get_prices(pools_df: pd.DataFrame, zero_fee: bool = False, display_data: bool = False) -> pd.DataFrame:
    """
    Calculate direct prices from pools data
    :param pools_df: dataframe with pools data
    :param zero_fee: calculations without|with pool fees
    :param display_data: display or not price data
    :return: dataframe with price data
    """
    _coins_list = list(pools_df['reserve_coin_denoms'])
    _coins_unique_list = list(set(np.concatenate(_coins_list).flat))
    _price_df = pd.DataFrame(columns=_coins_unique_list, index=_coins_unique_list)

    for _, _pool_row in pools_df.iterrows():
        _price_row_list = []
        _coins_pair = _pool_row.reserve_coin_denoms
        _balances = \
            {item['denom']: np.float64(item['amount']) / np.float64(item['weight']) if 'weight' in item.keys() else int(
                item['amount'])
             for item in _pool_row.balances}
        if _balances:
            for _coin_from, _coin_to in permutations(_coins_pair, 2):
                _swap_fee = _pool_row.swap_fee if not zero_fee else 0
                _price_row_list.append([
                    _coin_from,
                    _coin_to,
                    _balances[_coin_from],
                    float(_balances[_coin_from]) / float(_balances[_coin_to]) * (1 - _swap_fee)])
        _price_overall_df = pd.DataFrame(_price_row_list, columns=['coin_from', 'coin_to', 'pool_balance', 'price'])
        _price_overall_biggest_pools_df = \
            _price_overall_df.sort_values('pool_balance').drop_duplicates(['coin_from', 'coin_to'], keep='last')
        for _, _row in _price_overall_biggest_pools_df.iterrows():
            _price_df.loc[_row.coin_from, _row.coin_to] = _row.price
    for _coin in _coins_unique_list:
        _price_df.loc[_coin, _coin] = 1
    for _col in COINS_IN_DIFFERENT_CHAINS:
        if _col[0] in _coins_unique_list and _col[1] in _coins_unique_list:
            _price_df.loc[_col[0], _col[1]] = 1
            _price_df.loc[_col[1], _col[0]] = 1
    if display_data:
        display(HTML(_price_df.to_html(notebook=True, show_dimensions=False)))
    return _price_df


def get_price_enriched(price_df: pd.DataFrame, base_coin_denom: str = 'hydrogen',
                       display_data: bool = False) -> pd.DataFrame:
    """
    Calculate enriched prices from direct price data
    :param base_coin_denom: coin for liquidity calculation
    :param price_df: dataframe with price data
    :param display_data: display or not enriched price data
    :return: dataframe with enriched price data
    """
    _price_enriched_df = price_df.copy()
    # add prices from different chains
    for _col in COINS_IN_DIFFERENT_CHAINS:
        if _col[0] in _price_enriched_df.index and _col[1] in _price_enriched_df.index:
            for _index in _price_enriched_df.index:
                if isnan(_price_enriched_df.loc[_index, _col[0]]):
                    _price_enriched_df.loc[_index, _col[0]] = _price_enriched_df.loc[_index, _col[1]]
                    _price_enriched_df.loc[_col[0], _index] = _price_enriched_df.loc[_col[1], _index]
                elif isnan(_price_enriched_df.loc[_index, _col[1]]):
                    _price_enriched_df.loc[_index, _col[1]] = _price_enriched_df.loc[_index, _col[0]]
                    _price_enriched_df.loc[_col[1], _index] = _price_enriched_df.loc[_col[0], _index]
    # add prices with base liquid coin
    for _index in _price_enriched_df.index:
        if isnan(_price_enriched_df.loc[_index, base_coin_denom]) and ~isnan(_price_enriched_df.loc[_index, 'boot']):
            _price_enriched_df.loc[_index, base_coin_denom] = \
                _price_enriched_df.loc[_index, 'boot'] * _price_enriched_df.loc['boot', base_coin_denom]
        if isnan(_price_enriched_df.loc[base_coin_denom, _index]) and ~isnan(_price_enriched_df.loc[_index, 'boot']):
            _price_enriched_df.loc[base_coin_denom, _index] = \
                _price_enriched_df.loc['boot', _index] * _price_enriched_df.loc[base_coin_denom, 'boot']

    if display_data:
        display(HTML(_price_enriched_df.to_html(notebook=True, show_dimensions=False)))
    return _price_enriched_df
