from config import IBC_COIN_NAMES


def rename_denom(denom: str, denom_names_dict: dict = IBC_COIN_NAMES) -> str:
    """
    Rename denoms to human-readable names
    :param denom: network denom
    :param denom_names_dict: dictionary with human-readable names
    :return: human-readable name
    """
    return denom_names_dict[denom] if denom in denom_names_dict.keys() else denom


def reverse_rename_denom(denom: str, denom_names_dict: dict = IBC_COIN_NAMES) -> str:
    """
    Rename denoms from human-readable to network names
    :param denom: human-readable name
    :param denom_names_dict: dictionary with human-readable names
    :return: network name
    """
    denom_names_reverse_dict = {v: k for k, v in denom_names_dict.items()}
    return denom_names_reverse_dict.get(denom, denom.removesuffix('(pussy)'))
