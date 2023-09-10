import pandas as pd
import numpy as np
import json
from typing import Optional, Union
from math import ceil

from cyber_sdk.core.bech32 import AccAddress
from cyber_sdk.core.coins import Coin, Coins
from cyber_sdk.core.liquidity import MsgSwapWithinBatch
from cyberutils.bash import execute_bash, get_json_from_bash_query

from src.denom_utils import rename_denom, reverse_rename_denom
from config import BOSTROM_CHAIN_ID, BOSTROM_NODE_RPC_URL, POOL_FEE, BOSTROM_LCD_CLIENT, OSMOSIS_LCD_CLIENT, \
    OSMOSIS_NODE_RPC_URL, OSMOSIS_CHAIN_ID, PUSSY_LCD_CLIENT, COSMOSHUB_LCD_CLIENT, CRESCENT_LCD_CLIENT, \
    JUNO_LCD_CLIENT, CLI_WALLET, OSMOSIS_BASH_PRECOMMAND


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
        address: Union[str, AccAddress],
        price_df: Optional[pd.DataFrame] = None,
        base_coin_denom: Optional[str] = 'hydrogen',
        display_exceptions: bool = False) -> [int, Coins]:
    """
    Extract address balance by coins and convert it to base denomination
    :param address: address
    :param price_df: dataframe with price data
    :param base_coin_denom: a base denom
    :param display_exceptions: display or not exceptions about finding coin in price_df
    :return: address balance converted to base denomination and address balance by coins
    """
    assert address[:4] in ('osmo', 'puss', 'bost', 'cosm', 'cre1', 'juno')
    if address[:4] == 'osmo':
        _lcd_client = OSMOSIS_LCD_CLIENT
    elif address[:4] == 'puss':
        _lcd_client = PUSSY_LCD_CLIENT
    elif address[:4] == 'cosm':
        _lcd_client = COSMOSHUB_LCD_CLIENT
    elif address[:3] == 'cre':
        _lcd_client = CRESCENT_LCD_CLIENT
    elif address[:4] == 'juno':
        _lcd_client = JUNO_LCD_CLIENT
    else:
        _lcd_client = BOSTROM_LCD_CLIENT

    _balance_all_coins = _lcd_client.bank.balance(address=AccAddress(address))[0]

    _balance_in_base_coin = 0
    if price_df is not None and base_coin_denom:
        for _coin in _balance_all_coins.to_list():
            _coin_denom = rename_denom(_coin.denom)
            try:
                _balance_in_base_coin += _coin.amount * price_df.loc[base_coin_denom, _coin_denom] \
                    if price_df.loc[base_coin_denom, _coin_denom] > 0 else 0
            except KeyError:
                if display_exceptions:
                    print(f'{_coin_denom} not found in price_df')
                pass
    return int(_balance_in_base_coin) if not np.isnan(_balance_in_base_coin) else 0, _balance_all_coins


def get_total_balance(
        addresses: list[Union[str, AccAddress]],
        price_df: Optional[pd.DataFrame] = None,
        base_coin_denom: Optional[str] = 'hydrogen',
        display_exceptions: bool = False) -> [int, Coins]:
    """
    Extract addresses balance by coins and convert it to base denomination
    :param addresses: list of addresses
    :param price_df: dataframe with price data
    :param base_coin_denom: a base denom
    :param display_exceptions: display or not exceptions about finding coin in price_df
    :return: total addresses balance converted to base denomination and total addresses balance by coins
    """
    _balance = 0
    _balance_all_coins = Coins()
    for _address in addresses:
        _balance_item, _balance_all_coins_item = get_balance(address=_address,
                                                             price_df=price_df,
                                                             base_coin_denom=base_coin_denom,
                                                             display_exceptions=display_exceptions)
        _balance += _balance_item
        _balance_all_coins = _balance_all_coins + _balance_all_coins_item
    return _balance, _balance_all_coins


def get_balance_for_coin(balance_coins: Coins, coin_denom: str) -> int:
    """
    Extract coin balance
    :param balance_coins: address balance by coins
    :param coin_denom: extracted coin denom
    :return: extracted coin balance
    """
    coin_balance = [item['amount'] for item in balance_coins.to_data()
                    if rename_denom(item['denom']) == rename_denom(coin_denom)]
    return int(coin_balance[0]) if len(coin_balance) > 0 else 0


def generate_swap_bash_query(
        coin_from_amount: float,
        coin_from_denom: str,
        coin_to_denom: str,
        coins_pool_df: pd.DataFrame,
        price_df: pd.DataFrame,
        max_slippage: float = 0.15,
        wallet: str = CLI_WALLET,
        cli_name: str = 'cyber',
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
    :param cli_name: name of a CLI application for bash execution
    :param chain_id: chain id
    :param node_rpc_url: URL of RPC node
    :return: swap bash query for bostrom network
    """
    _pool_id = coins_pool_df.loc[:, 'id'].to_list()[0]
    _pool_type = coins_pool_df.loc[:, 'type_id'].to_list()[0]
    _price = price_df.loc[coin_from_denom, coin_to_denom] * (1 + max_slippage)
    return f'{cli_name} tx liquidity swap {_pool_id} {_pool_type} ' \
           f'{int(coin_from_amount)}{reverse_rename_denom(coin_from_denom)}' \
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


def generate_swap_cyber_msg(
        coin_from_amount: float,
        coin_from_denom: str,
        coin_to_denom: str,
        coins_pool_df: pd.DataFrame,
        price_df: pd.DataFrame,
        wallet_address: Union[str, AccAddress],
        max_slippage: float = 0.05,
        swap_fee: float = POOL_FEE) -> MsgSwapWithinBatch:
    """
    Generate a swap message for the liquidity module of the cyber protocol (bostrom and space-pussy chains)
    :param coin_from_amount: initial coin amount
    :param coin_from_denom: initial coin denom
    :param coin_to_denom: received coin denom
    :param coins_pool_df: dataframe with pool data
    :param price_df: dataframe with price data
    :param wallet_address: wallet address in a cyber chain
    :param max_slippage: maximum slippage
    :param swap_fee: pool fee
    :return: swap message
    """
    _pool_id = coins_pool_df.loc[:, 'id'].to_list()[0]
    _pool_type = coins_pool_df.loc[:, 'type_id'].to_list()[0]
    _coin_from_denom = reverse_rename_denom(coin_from_denom)
    _coin_to_denom = reverse_rename_denom(coin_to_denom)
    _order_price = \
        str(
            int(
                1e18 * (
                    price_df.loc[coin_from_denom, coin_to_denom] * (1 + max_slippage) \
                        if _coin_from_denom < _coin_to_denom \
                        else price_df.loc[coin_to_denom, coin_from_denom] * (1 - max_slippage)
                )
            )
        )

    return MsgSwapWithinBatch(
        swap_requester_address=AccAddress(wallet_address),
        pool_id=int(_pool_id),
        swap_type_id=_pool_type,
        offer_coin=Coin(amount=int(coin_from_amount), denom=_coin_from_denom),
        demand_coin_denom=_coin_to_denom,
        offer_coin_fee=Coin(amount=ceil(coin_from_amount * swap_fee / 2), denom=_coin_from_denom),
        order_price=_order_price
    )


def swap_osmosis(
        coin_from_amount: int,
        coin_from_denom: str,
        coin_to_denom: str,
        pools_df: pd.DataFrame,
        price_df: pd.DataFrame,
        osmosis_wallet_address: str,
        fee_amount: int,
        tx_unsigned_file_name: str,
        tx_signed_file_name: str,
        max_slippage: float = 0.05,
        gas_limit: int = 200_000,
        fee_denom: str = 'uosmo') -> str:
    """
    Swap in the gamm module of Osmosis
    :param coin_from_amount: initial coin amount
    :param coin_from_denom: initial coin denom
    :param coin_to_denom: received coin denom
    :param pools_df: dataframe with pool data
    :param price_df: dataframe with price data
    :param osmosis_wallet_address: wallet address in osmosis
    :param fee_amount: fee amount
    :param tx_unsigned_file_name: file name with unsigned transaction
    :param tx_signed_file_name: file name with signed transaction
    :param max_slippage: maximum slippage
    :param gas_limit: gas limit
    :param fee_denom: fee denom
    :return: transaction hash
    """
    _coins_pool_df = pools_df.loc[
        pools_df.apply(
            lambda x: coin_from_denom in x.reserve_coin_denoms and coin_to_denom in x.reserve_coin_denoms,
            axis=1)
    ]
    _pool_id = _coins_pool_df.loc[:, 'id'].to_list()[0]

    _routes = [
        {"pool_id": str(_pool_id),
         "token_out_denom": reverse_rename_denom(coin_to_denom)}
    ]
    _msgs = [
        {"@type": "/osmosis.gamm.v1beta1.MsgSwapExactAmountIn",
         "sender": osmosis_wallet_address,
         "routes": _routes,
         "token_in":
             {"denom": reverse_rename_denom(coin_from_denom), "amount": str(int(coin_from_amount))},
         "token_out_min_amount": str(
             int(coin_from_amount * price_df.loc[coin_to_denom, coin_from_denom] * (1 - max_slippage)))}
    ]
    _tx_unsigned = {
        "body":
            {"messages": _msgs,
             "memo": "",
             "timeout_height": "0",
             "extension_options": [],
             "non_critical_extension_options": []
             },
        "auth_info":
            {"signer_infos": [],
             "fee": {
                 "amount": [{"denom": fee_denom, "amount": str(fee_amount)}],
                 "gas_limit": str(gas_limit),
                 "payer": "",
                 "granter": ""}
             },
        "signatures": []
    }

    with open(tx_unsigned_file_name, 'w') as _outfile:
        _outfile.write(json.dumps(_tx_unsigned, indent=4))

    execute_bash(
        bash_command=f'{OSMOSIS_BASH_PRECOMMAND}osmosisd tx sign {tx_unsigned_file_name} '
                     f'--output-document {tx_signed_file_name} --from {osmosis_wallet_address} '
                     f'--chain-id {OSMOSIS_CHAIN_ID} --node {OSMOSIS_NODE_RPC_URL}',
        shell=True
    )
    _res_json = get_json_from_bash_query(
        bash_command=f'osmosisd tx broadcast {tx_signed_file_name} --output json '
                     f'--chain-id {OSMOSIS_CHAIN_ID} --node {OSMOSIS_NODE_RPC_URL}'
    )

    return _res_json["txhash"]
