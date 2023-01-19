## Arbitrage in Bostrom Network

### Pools

[Bostrom Pools](https://cyb.ai/teleport/pools)  
[Osmosis Pool BOOT-ATOM](https://info.osmosis.zone/pool/596)  
[Osmosis Pool BOOT-OSMO](https://info.osmosis.zone/pool/597)  
[Osmosis Pool ATOM-OSMO](https://info.osmosis.zone/pool/1)

### Pools Liquidity

[Pools Liquidity in GH](pools_liquidity_in_gh.ipynb)

### Search the Best Arbitrage

[Search the Best Arbitrage in Bostrom and Osmosis Pools](search_arbitrage.ipynb)

### Swap Optimization
[Finding the Best Way to Swap Coins](swap_optimization.ipynb)

### Price Calculation
#### Bostrom

[Tendermint Liquidity Module Light Paper](https://github.com/tendermint/liquidity/blob/develop/doc/LiquidityModuleLightPaper_EN.pdf)

Formulas without orderbook matching (Liquidity Pool Model only)   

<img src="https://latex.codecogs.com/png.image?\inline\dpi{200}\bg{white}Price&space;=&space;\frac{Target\&space;Coin\&space;Pool\&space;Amount\&space;*\&space;(1&space;-&space;Pool\&space;Fee)}{Source\&space;Coin\&space;Pool\&space;Amount\&space;&plus;\&space;2\&space;*\&space;Source\&space;Coin\&space;Amount}" />
<br>
<br>
<img src="https://latex.codecogs.com/png.image?\inline\dpi{200}\bg{white}Target\&space;Coin\&space;Amount&space;=&space;\frac{Source\&space;Coin\&space;Amount\&space;*\&space;Target\&space;Coin\&space;Pool\&space;Amount\&space;*\&space;(1&space;-&space;Pool\&space;Fee)}{Source\&space;Coin\&space;Pool\&space;Amount\&space;&plus;\&space;2\&space;*\&space;Source\&space;Coin\&space;Amount}" />

where _Pool Fee = 0.003_ as most common value

#### Osmosis
[Module Gamm documentation](https://docs.osmosis.zone/osmosis-core/modules/gamm)

<img src="https://latex.codecogs.com/png.image?\inline\dpi{200}\bg{white}Price&space;=&space;\frac{Target\&space;Coin\&space;Pool\&space;Amount\&space;*\&space;(1&space;-&space;Pool\&space;Fee)}{Source\&space;Coin\&space;Pool\&space;Amount\&space;&plus;\&space;(1&space;-&space;Pool\&space;Fee)\&space;*\&space;Source\&space;Coin\&space;Amount}\&space;*\&space;\frac{Source\&space;Coin\&space;Pool\&space;Weight}{Target\&space;Coin\&space;Pool\&space;Weight}" />
<br>
<br>
<img src="https://latex.codecogs.com/png.image?\inline\dpi{200}\bg{white}Target\&space;Coin\&space;Amount&space;=&space;\frac{Source\&space;Coin\&space;Amount\&space;*\&space;Target\&space;Coin\&space;Pool\&space;Amount\&space;*\&space;(1&space;-&space;Pool\&space;Fee)}{Source\&space;Coin\&space;Pool\&space;Amount\&space;&plus;\&space;(1&space;-&space;Pool\&space;Fee)\&space;*\&space;Source\&space;Coin\&space;Amount}\&space;*\&space;\frac{Source\&space;Coin\&space;Pool\&space;Weight}{Target\&space;Coin\&space;Pool\&space;Weight}" />
