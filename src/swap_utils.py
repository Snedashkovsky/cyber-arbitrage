import pandas as pd
from cyber_sdk.core.bech32 import AccAddress
from cyber_sdk.core.coins import Coins

from config import CHAIN_ID, BOSTROM_NODE_RPC_URL, POOL_FEE, CYBER_LCD_CLIENT


def get_pool_balance_by_coin(pool_balances: list, coin: str) -> int:
    try:
        return [int(item['amount']) for item in pool_balances if item['denom'] == coin][0]
    except Exception as e:
        print(pool_balances, coin, e)


def get_balance(address: str, price_df: pd.DataFrame, base_denom: str = 'hydrogen') -> [int, Coins]:
    balance = 0
    balance_all_coins = CYBER_LCD_CLIENT.bank.balance(address=AccAddress(address))[0]
    for coin in balance_all_coins.to_list():
        balance += coin.amount * price_df.loc[base_denom, coin.denom]
    return int(balance), balance_all_coins


def generate_swap_query(coin_from_amount: float,
                        coin_from: str,
                        coin_to: str,
                        coins_pool_df: pd.DataFrame,
                        price_df: pd.DataFrame,
                        max_slippage: float = 0.03,
                        wallet: str = '$WALLET',
                        chain_id: str = CHAIN_ID,
                        node_rpc_url=BOSTROM_NODE_RPC_URL) -> str:
    _pool_id = coins_pool_df.loc[:, 'id'].to_list()[0]
    _pool_type = coins_pool_df.loc[:, 'type_id'].to_list()[0]
    _price = price_df.loc[coin_from, coin_to] * (1 + max_slippage)
    return f'cyber tx liquidity swap {_pool_id} {_pool_type} {int(coin_from_amount)}{coin_from} {coin_to} ' \
           f'{_price:.6f} 0.003 --from {wallet} 'f'--chain-id {chain_id} --gas 200000 --gas-prices 0.01boot --yes ' \
           f'--node {node_rpc_url} --broadcast-mode block'


def generate_swap_queries(way: list,
                          coin1_amount: float,
                          pools_df: pd.DataFrame,
                          price_df: pd.DataFrame) -> [float, list]:
    _coin_from_amount = coin1_amount
    coin2_way_queries = []
    for way_item in way:
        _coin_from = way_item[0]
        _coin_to = way_item[1]
        _coins_pool_df = pools_df[(pools_df.reserve_coin_denoms.isin([[_coin_from, _coin_to]])) | (
            pools_df.reserve_coin_denoms.isin([[_coin_to, _coin_from]]))]
        _coin_from_pool_amount = get_pool_balance_by_coin(_coins_pool_df.balances.values[0], _coin_from)
        _coin_to_pool_amount = get_pool_balance_by_coin(_coins_pool_df.balances.values[0], _coin_to)
        _coin_to_amount = _coin_from_amount * _coin_to_pool_amount / (
                    _coin_from_pool_amount + 2 * _coin_from_amount) * (1 - POOL_FEE)
        coin2_way_queries.append(
            generate_swap_query(coin_from_amount=_coin_from_amount, coin_from=_coin_from, coin_to=_coin_to,
                                coins_pool_df=_coins_pool_df, price_df=price_df))
        _coin_from_amount = _coin_to_amount
    coin2_way_amount = _coin_from_amount
    return coin2_way_amount, coin2_way_queries
