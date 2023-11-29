import requests
import pandas as pd
import numpy as np
from math import isnan, sqrt
from IPython.display import display, HTML
from pandarallel import pandarallel
from itertools import permutations, combinations, chain
from typing import Optional, Union

from cyberutils.bash import get_json_from_bash_query

from src.swap_utils import get_pool_value_by_coin
from src.denom_utils import rename_denom, reverse_rename_denom
from config import BOSTROM_RELATED_OSMO_POOLS, BOSTROM_POOLS_BASH_QUERY, OSMOSIS_POOLS_API_URL, BOSTROM_NODE_RPC_URL, \
    PUSSY_POOLS_BASH_QUERY, PUSSY_NODE_RPC_URL, INTERCHANGEABLE_IBC_COINS, COINS_IN_DIFFERENT_CHAINS, \
    CRESCENT_POOLS_API_URL, POOL_FEE


def get_pools_cyber(network: str = 'bostrom',
                    display_data: bool = False,
                    recalculate_pools: bool = True,
                    pools_bash_query: Optional[str] = None,
                    nb_balance_workers: int = 10) -> pd.DataFrame:
    """
    Extract pools data from a cyber protocol network
    :param network: cyber protocol network name
    :param display_data: display or not pool data
    :param recalculate_pools: update or not pool list
    :param pools_bash_query: bash query for getting pool data
    :param nb_balance_workers: number of workers for pools balance extraction
    :return: dataframe with pools data
    """
    assert network in ('bostrom', 'space-pussy')
    if pools_bash_query is None and network == 'bostrom':
        pools_bash_query = BOSTROM_POOLS_BASH_QUERY
    elif pools_bash_query is None and network == 'space-pussy':
        pools_bash_query = PUSSY_POOLS_BASH_QUERY

    if recalculate_pools:
        _pools_cyber_json = get_json_from_bash_query(pools_bash_query)
        _pools_cyber_df = pd.DataFrame(_pools_cyber_json['pools'])
        _pools_cyber_df.to_csv(f'data/{network}_pools.csv')
    else:
        _pools_cyber_df = pd.read_csv(f'data/{network}_pools.csv',
                                      converters={'reserve_coin_denoms': lambda x: x.strip("['']").split("', '")})
    _pools_cyber_df['id'] = _pools_cyber_df['id'].astype(int)

    pandarallel.initialize(nb_workers=min(len(_pools_cyber_df), nb_balance_workers), verbose=1)
    _pools_cyber_df.loc[:, 'balances'] = \
        _pools_cyber_df['reserve_account_address'].parallel_map(
            lambda address: get_json_from_bash_query(
                f'cyber query bank balances {address} --node {BOSTROM_NODE_RPC_URL} -o json' if network == 'bostrom'
                else f'pussy query bank balances {address} --node {PUSSY_NODE_RPC_URL} -o json')['balances'])
    _pools_cyber_df.loc[:, 'balances'] = \
        _pools_cyber_df['balances'].map(lambda x: [
            {'denom': item['denom'] + '(pussy)' if item['denom'] in (
                'milliampere', 'millivolt') and network == 'space-pussy' else rename_denom(item['denom']),
             'amount': item['amount']}
            for item in x])
    _pools_cyber_df.loc[:, 'reserve_coin_denoms'] = \
        _pools_cyber_df.reserve_coin_denoms.map(
            lambda x: [_coin_denom + '(pussy)' if _coin_denom in (
                'milliampere', 'millivolt') and network == 'space-pussy' else rename_denom(_coin_denom)
                       for _coin_denom in x])
    _pools_cyber_df.loc[:, 'swap_fee'] = POOL_FEE
    _pools_cyber_df.loc[:, 'network'] = network
    if display_data:
        print(f'{network.capitalize()} Pools')
        display(HTML(_pools_cyber_df.to_html(index=False, notebook=True, show_dimensions=False)))
    return _pools_cyber_df


def get_pools_osmosis(network: str = 'osmosis',
                      display_data: bool = False,
                      recalculate_pools: bool = True,
                      pools_api_url: str = OSMOSIS_POOLS_API_URL,
                      min_uosmo_balance: int = 10_000_000) -> pd.DataFrame:
    """
    Extract pools data from an osmosis network
    :param network: osmosis protocol network name
    :param display_data: display or not pool data
    :param recalculate_pools: update or not pool list
    :param pools_api_url: API for getting pool data
    :param min_uosmo_balance: min balance in pool for excluding empty pools from calculations
    :return: dataframe with pools data
    """
    _pools_osmosis_json = requests.get(pools_api_url).json()
    _pools_osmosis_df = pd.DataFrame(_pools_osmosis_json['pools'])

    _pools_osmosis_df['id'] = _pools_osmosis_df['id'].astype(int)
    _pools_osmosis_df = \
        _pools_osmosis_df[_pools_osmosis_df['@type'] != '/osmosis.gamm.poolmodels.stableswap.v1beta1.Pool']
    _pools_osmosis_df.loc[:, 'type_id'] = _pools_osmosis_df['@type'].map(
        lambda x: 1 if x == '/osmosis.gamm.v1beta1.Pool' else 0)
    _pools_osmosis_df['total_weight'] = _pools_osmosis_df['total_weight'].fillna(0).astype(int)
    _pools_osmosis_df.loc[:, 'balances'] = _pools_osmosis_df['pool_assets'].map(
        lambda x: [
            {'denom': rename_denom(item['token']['denom']),
             'amount': item['token']['amount'],
             'weight': item['weight']} for item in x])
    _pools_osmosis_df.loc[:, 'denoms_count'] = _pools_osmosis_df['pool_assets'].map(lambda x: len(x))
    _pools_osmosis_df.loc[:, 'swap_fee'] = _pools_osmosis_df['pool_params'].map(lambda x: float(x['swap_fee']))
    _pools_osmosis_df.loc[:, 'exit_fee'] = _pools_osmosis_df['pool_params'].map(lambda x: float(x['exit_fee']))
    _pools_osmosis_df.loc[:, 'reserve_coin_denoms'] = _pools_osmosis_df['pool_assets'].map(
        lambda x: [item['token']['denom'] for item in x])
    _pools_osmosis_df.loc[:, 'reserve_coin_denoms'] = \
        _pools_osmosis_df['reserve_coin_denoms'].map(lambda x: [rename_denom(item) for item in x])
    _pools_osmosis_df.loc[:, 'network'] = network

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
        print(f'{network.capitalize()} Pools')
        display(HTML(
            _pools_osmosis_df.sort_values('total_weight', ascending=False).to_html(index=False, notebook=True,
                                                                                   show_dimensions=False)))
    return _pools_osmosis_df


def get_roots_in_square_equation(a: float, b: float, c: float) -> Optional[list[float]]:
    """
    Get roots in square equation `a * x ^ 2 + b * x + c = 0`
    :param a: a
    :param b: b
    :param c: c
    :return: roots
    """
    _discriminant = b ** 2 - 4 * a * c
    if _discriminant > 0:
        return [(-b + sqrt(_discriminant)) / (2 * a), (-b - sqrt(_discriminant)) / (2 * a)]
    elif _discriminant == 0:
        return [-b / (2 * a)]
    else:
        print("Not solution (equation roots are not real)")
        return None


def get_crescent_pool_params(row: pd.Series) -> [Optional[Union[float, int]]]:
    """
    Get Crescent pool parameters from a pool data
    :param row: a pool data
    :return: list of pools parameters (price, a, b, base coin amount, quote coin amount)
    """
    base_coin_amount = int(row.balances_crescent['base_coin']['amount'])
    quote_coin_amount = int(row.balances_crescent['quote_coin']['amount'])

    if row.type_id == 'POOL_TYPE_BASIC' and base_coin_amount > 0:
        return quote_coin_amount / base_coin_amount, 0, 0, base_coin_amount, quote_coin_amount
    elif row.type_id == 'POOL_TYPE_BASIC' and base_coin_amount == 0:
        return None, 0, 0, base_coin_amount, quote_coin_amount
    elif row.type_id == 'POOL_TYPE_RANGED':
        _price_min = float(row['min_price'])
        _price_max = float(row['max_price'])

        if base_coin_amount == quote_coin_amount == 0:
            return None, None, None, 0, 0, base_coin_amount, quote_coin_amount

        _price_min_max_sqrt = (_price_max * _price_min) ** 0.5
        a = get_roots_in_square_equation(
            a=_price_max - _price_min_max_sqrt,
            b=-base_coin_amount * _price_min_max_sqrt - quote_coin_amount,
            c=-base_coin_amount * quote_coin_amount
        )[0]
        b = a * _price_min_max_sqrt

        if base_coin_amount == 0:
            price = _price_max
        elif quote_coin_amount == 0:
            price = _price_min
        else:
            price = (b + quote_coin_amount) / (a + base_coin_amount)

        balances_with_a_b = \
            [{'denom': row.balances[0]['denom'], 'amount': int(row.balances[0]['amount']) + row.a},
             {'denom': row.balances[1]['denom'], 'amount': int(row.balances[1]['amount']) + row.b}]
        return price, a, b, balances_with_a_b, base_coin_amount, quote_coin_amount


def get_pools_crescent(network: str = 'crescent',
                       display_data: bool = False,
                       recalculate_pools: bool = True,
                       remove_disabled_pools: bool = True,
                       enrich_data: bool = True,
                       pools_api_url: str = CRESCENT_POOLS_API_URL,
                       base_coin_denom: str = 'ubcre') -> pd.DataFrame:
    """
    Extract pools data from a crescent protocol network
    :param network: crescent protocol network name
    :param display_data: display or not pool data
    :param recalculate_pools: update or not pool list
    :param remove_disabled_pools: remove or not disabled pools
    :param enrich_data: calculate or not pools params
    :param pools_api_url: API for getting pool data
    :param base_coin_denom: base coin denom
    :return: dataframe with pools data
    """
    assert network == 'crescent'
    _pools_crescent_json = requests.get(pools_api_url).json()
    _pools_crescent_df = pd.DataFrame(_pools_crescent_json['pools'])

    _pools_crescent_df['id'] = _pools_crescent_df['id'].astype(int)
    _pools_crescent_df['min_price'] = _pools_crescent_df['min_price'].astype(float)
    _pools_crescent_df['max_price'] = _pools_crescent_df['max_price'].astype(float)
    _pools_crescent_df['swap_fee'] = 0.0
    _pools_crescent_df.rename(columns={'type': 'type_id'}, inplace=True)
    _pools_crescent_df.loc[:, 'balances_crescent'] = _pools_crescent_df.loc[:, 'balances']
    _pools_crescent_df.loc[:, 'balances'] = _pools_crescent_df.loc[:, 'balances'].map(
        lambda balances: [coin for coin_type, coin in balances.items()])
    _pools_crescent_df.loc[:, 'reserve_coin_denoms'] = _pools_crescent_df.loc[:, 'balances_crescent'].map(
        lambda balances_crescent: [balances_crescent['base_coin']['denom'], balances_crescent['quote_coin']['denom']])
    _pools_crescent_df['network'] = network
    _pools_crescent_df['pool_coin_supply'] = _pools_crescent_df['pool_coin_supply'].astype(float)
    _pools_crescent_df['price'] = _pools_crescent_df['price'].fillna(0).astype(float)

    if remove_disabled_pools:
        _pools_crescent_df = _pools_crescent_df[~_pools_crescent_df.disabled]

    if enrich_data:
        _pools_crescent_df.loc[:, ['calculated_price',
                                   'a',
                                   'b',
                                   'balances_with_a_b',
                                   'base_coin_amount',
                                   'quote_coin_amount']] = \
            _pools_crescent_df.apply(lambda row: pd.Series(get_crescent_pool_params(row)), axis=1).to_numpy()

    if display_data:
        print(f'{network.capitalize()} Pools')
        display(HTML(_pools_crescent_df.to_html(index=False, notebook=True, show_dimensions=False)))
    return _pools_crescent_df


def get_pools(display_data: bool = False,
              recalculate_pools: bool = True,
              networks: Optional[list[str]] = None,
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
    if 'crescent' in networks:
        _pools_crescent_df = get_pools_crescent(display_data=display_data, recalculate_pools=recalculate_pools)
        _pools_df = pd.concat([_pools_df, _pools_crescent_df])
    return _pools_df


def get_pool_ids_by_denoms(denoms: list[str], pools_df: pd.DataFrame) -> list[int]:
    """
    Extract pool ids from pool data for 2 given denoms
    :param denoms: list of 2 given denoms
    :param pools_df: pool data dataframe
    :return: list of pool ids
    """
    assert len(denoms) == 2
    return pools_df[pools_df.reserve_coin_denoms.isin([denoms, denoms[::-1]])].id.to_list()


def get_prices(pools_df: pd.DataFrame, zero_fee: bool = False, display_data: bool = False,
               extra_coins: Optional[list[str]] = None) -> pd.DataFrame:
    """
    Calculate direct prices from pools data
    :param pools_df: dataframe with pools data
    :param zero_fee: calculations without|with pool fees
    :param display_data: display or not price data
    :param extra_coins: coins that are not in a pools, but are needed to calculate a price
    :return: dataframe with price data
    """
    _coins_list = list(pools_df['reserve_coin_denoms'])
    if extra_coins is None:
        extra_coins = ['uatom', 'ujuno']
    _coins_unique_list = list(set(np.concatenate(_coins_list).flat)) + extra_coins
    _price_df = pd.DataFrame(columns=_coins_unique_list, index=_coins_unique_list)

    for _, _pool_row in pools_df.iterrows():
        _price_row_list = []
        _coins_pair = _pool_row.reserve_coin_denoms
        _balances = \
            {item['denom']: np.float64(item['amount']) / np.float64(item['weight']) if 'weight' in item.keys() else int(
                item['amount'])
             for item in _pool_row['balances_with_a_b' if 'balances_with_a_b' in _pool_row.keys() else 'balances']}
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
    for _col in INTERCHANGEABLE_IBC_COINS:
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
    coins_in_different_chains = \
        list(chain.from_iterable([list(combinations(item, 2)) for item in COINS_IN_DIFFERENT_CHAINS]))
    for _col in coins_in_different_chains:
        if _col[0] in _price_enriched_df.index and _col[1] in _price_enriched_df.index:
            for _index in _price_enriched_df.index:
                if isnan(_price_enriched_df.loc[_index, _col[0]]):
                    _price_enriched_df.loc[_index, _col[0]] = _price_enriched_df.loc[_index, _col[1]]
                    _price_enriched_df.loc[_col[0], _index] = _price_enriched_df.loc[_col[1], _index]
                elif isnan(_price_enriched_df.loc[_index, _col[1]]):
                    _price_enriched_df.loc[_index, _col[1]] = _price_enriched_df.loc[_index, _col[0]]
                    _price_enriched_df.loc[_col[1], _index] = _price_enriched_df.loc[_col[0], _index]
    # add prices with base liquid coin
    if 'boot' in _price_enriched_df.index:
        for _index in _price_enriched_df.index:
            if isnan(_price_enriched_df.loc[_index, base_coin_denom]) and ~isnan(
                    _price_enriched_df.loc[_index, 'boot']):
                _price_enriched_df.loc[_index, base_coin_denom] = \
                    _price_enriched_df.loc[_index, 'boot'] * _price_enriched_df.loc['boot', base_coin_denom]
            if isnan(_price_enriched_df.loc[base_coin_denom, _index]) and ~isnan(
                    _price_enriched_df.loc[_index, 'boot']):
                _price_enriched_df.loc[base_coin_denom, _index] = \
                    _price_enriched_df.loc['boot', _index] * _price_enriched_df.loc[base_coin_denom, 'boot']
    # add prices for space-pussy coins
    if 'liquidpussy' in _price_enriched_df.index:
        for _index in _price_enriched_df.index:
            if isnan(_price_enriched_df.loc[_index, base_coin_denom]) and \
                    ~isnan(_price_enriched_df.loc[_index, 'liquidpussy']):
                _price_enriched_df.loc[_index, base_coin_denom] = \
                    _price_enriched_df.loc[_index, 'liquidpussy'] * _price_enriched_df.loc[
                        'liquidpussy', base_coin_denom]
            if isnan(_price_enriched_df.loc[base_coin_denom, _index]) and \
                    ~isnan(_price_enriched_df.loc[_index, 'liquidpussy']):
                _price_enriched_df.loc[base_coin_denom, _index] = \
                    _price_enriched_df.loc['liquidpussy', _index] * _price_enriched_df.loc[
                        base_coin_denom, 'liquidpussy']

    if display_data:
        display(HTML(_price_enriched_df.to_html(notebook=True, show_dimensions=False)))
    return _price_enriched_df


def get_pools_and_prices(networks: Optional[list[str]],
                         pools_isin: Optional[dict[str, list]],
                         pools_notisin: Optional[dict[str, list]]) -> [pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Get pool, direct price, and enriched price data
    :param networks: a list of `bostrom`, `space-pussy` or `osmosis` networks, all of them are extracted by default
    :param pools_isin: dictionary with pools which must be in result
    :param pools_notisin: dictionary with pools which must not be in result
    :return: pool, direct price, and enriched price dataframes
    """
    _pools_df = get_pools(networks=networks)
    if pools_isin:
        _pools_df = _pools_df[
            _pools_df.apply(
                lambda row: True if row['network'] in pools_isin.keys() and row.id in pools_isin[
                    row['network']] else False,
                axis=1)]
    if pools_notisin:
        _pools_df = _pools_df[
            _pools_df.apply(
                lambda row: True if row['network'] in pools_notisin.keys() and row.id not in pools_notisin[
                    row['network']] else False,
                axis=1)]
    _price_df = get_prices(pools_df=_pools_df)
    _price_enriched_df = get_price_enriched(price_df=_price_df)
    return _pools_df, _price_df, _price_enriched_df
