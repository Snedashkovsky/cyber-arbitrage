## Arbitrage in Bostrom, Space-Pussy, Osmosis and Crescent Networks
<p>
    <img alt="GitHub" src="https://img.shields.io/github/license/Snedashkovsky/cyber-arbitrage">
    <img alt="Python" src="https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue">
</p>

### Pools

#### [Bostrom Pools](https://cyb.ai/warp)  
#### [Space-Pussy Pools](https://cyb.ai/warp)  
#### [Osmosis Pools](https://frontier.osmosis.zone/pools)
- [BOOT-ATOM](https://info.osmosis.zone/pool/596)  
- [BOOT-OSMO](https://info.osmosis.zone/pool/597)  
- [BOOT-WETH (Gravity)](https://info.osmosis.zone/pool/911)  
- [BOOT-WETH (Axelar)](https://info.osmosis.zone/pool/912)  
- [BOOT-DOT](https://info.osmosis.zone/pool/919)  
#### [Crescent Pools](https://app.crescent.network/farm)

### Price Formulas
#### Bostrom and Space-Pussy

[Tendermint Liquidity Module Light Paper](https://github.com/tendermint/liquidity/blob/develop/doc/LiquidityModuleLightPaper_EN.pdf)

formulas without orderbook matching (Liquidity Pool Model only)   

```math
Price = \frac{Target Coin Pool Amount \times (1 - Pool Fee)}{Source Coin Pool Amount + 2 \times Source Coin Amount}
```
[//]: # (<img src="https://latex.codecogs.com/png.image?\inline\dpi{150}\bg{white}Price&space;=&space;\frac{Target\&space;Coin\&space;Pool\&space;Amount\&space;*\&space;&#40;1&space;-&space;Pool\&space;Fee&#41;}{Source\&space;Coin\&space;Pool\&space;Amount\&space;&plus;\&space;2\&space;*\&space;Source\&space;Coin\&space;Amount}" />)

```math
Target Coin Amount = \frac{Source Coin Amount \times Target Coin Pool Amount \times (1 - Pool Fee)}{Source Coin Pool Amount + 2 \times Source Coin Amount}
```
[//]: # (<img src="https://latex.codecogs.com/png.image?\inline\dpi{175}\bg{white}Target\&space;Coin\&space;Amount&space;=&space;\frac{Source\&space;Coin\&space;Amount\&space;*\&space;Target\&space;Coin\&space;Pool\&space;Amount\&space;*\&space;&#40;1&space;-&space;Pool\&space;Fee&#41;}{Source\&space;Coin\&space;Pool\&space;Amount\&space;&plus;\&space;2\&space;*\&space;Source\&space;Coin\&space;Amount}" />)

where _Pool Fee = 0.003_ as most common value

#### Osmosis
[Module Gamm documentation](https://docs.osmosis.zone/osmosis-core/modules/gamm)

```math
Price = \frac{Target Coin Pool Amount \times (1 - Pool Fee)}{Source Coin Pool Amount + (1 - Pool Fee) \times Source Coin Amount} \times \frac{Source Coin Pool Weight}{Target Coin Pool Weight}
```
[//]: # (<img src="https://latex.codecogs.com/png.image?\inline\dpi{200}\bg{white}Price&space;=&space;\frac{Target\&space;Coin\&space;Pool\&space;Amount\&space;*\&space;&#40;1&space;-&space;Pool\&space;Fee&#41;}{Source\&space;Coin\&space;Pool\&space;Amount\&space;&plus;\&space;&#40;1&space;-&space;Pool\&space;Fee&#41;\&space;*\&space;Source\&space;Coin\&space;Amount}\&space;*\&space;\frac{Source\&space;Coin\&space;Pool\&space;Weight}{Target\&space;Coin\&space;Pool\&space;Weight}" />)

```math
Target Coin Amount = \frac{Source Coin Amount \times Target Coin Pool Amount \times (1 - Pool Fee)}{Source Coin Pool Amount + (1 - Pool Fee) \times Source Coin Amount} \times \frac{Source Coin Pool Weight}{Target Coin Pool Weight}
```
[//]: # (<img src="https://latex.codecogs.com/png.image?\inline\dpi{175}\bg{white}Target\&space;Coin\&space;Amount&space;=&space;\frac{Source\&space;Coin\&space;Amount\&space;*\&space;Target\&space;Coin\&space;Pool\&space;Amount\&space;*\&space;&#40;1&space;-&space;Pool\&space;Fee&#41;}{Source\&space;Coin\&space;Pool\&space;Amount\&space;&plus;\&space;&#40;1&space;-&space;Pool\&space;Fee&#41;\&space;*\&space;Source\&space;Coin\&space;Amount}\&space;*\&space;\frac{Source\&space;Coin\&space;Pool\&space;Weight}{Target\&space;Coin\&space;Pool\&space;Weight}" />)

### Analytics

#### [Bostrom Revenue and Price Model](revenue_model.ipynb)

#### [Liquidity of Pools Related with Bostrom and Space-Pussy](pools_liquidity_in_gh.ipynb)

#### [Search the Best Arbitrage in Bostrom, Osmosis and Space-Pussy Pools](search_arbitrage.ipynb)

#### [Bostrom and Space-Pussy Swap Optimization. Finding the Best Way to Swap Coins](swap_optimization.ipynb)

#### [Bostrom and Space-Pussy Deposit Calculation for a direct transaction](deposit_calculation.ipynb)  
it's usually more convenient to use the [cyb.ai](https://cyb.ai/warp/add-liquidity)

### Get Data
#### Pools Data
```python
from src.data_extractors import get_pools, get_prices, get_price_enriched

pools_df = get_pools(networks=['bostrom', 'space-pussy', 'osmosis', 'crescent'], bostrom_related_osmo_pools=None)
```
#### Direct Prices
```python
price_df = get_prices(pools_df=pools_df)
```
#### Enriched Prices
```python
price_df = get_price_enriched(price_df=price_df, base_coin_denom='uosmo')
```

### How to start
you should have [python](https://www.python.org/downloads/) version 3.9, 3.10 or 3.11, check it
```bash
python --version
```
clone repo
```bash 
git clone https://github.com/Snedashkovsky/cyber-arbitrage && \
cd cyber-arbitrage
```
install [jupyter notebook](https://jupyter.org/install)
```bash
pip install notebook
```
install python requirements
```bash
pip install -r requirements.txt
```
run jupyter notebook
```bash
jupyter notebook
```
