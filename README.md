# StreamAlpha

## Getting Started (WIP)

1. Clone repo
2. `pip install -r requirements.txt`
3. Follow [configuration instructions](#ib-configuration-instructions) for your Interactive Brokers account
4. On terminal, navigate to the root directory
5. `flask run` to run API locally
6. `python run.py` to run dashboard

Note: most features require an active (i.e. open and logged in) instance of [Trader Workstation](https://www.interactivebrokers.com/en/index.php?f=14099#tws-software)

## IB Configuration Instructions
1. [Enable the API port](https://interactivebrokers.github.io/tws-api/initial_setup.html)
2. Create the necessary [Flex Queries](https://www.interactivebrokers.com/en/software/singlefunds/topics/flexqueries.htm) from the Interactive Brokers Account Management interface
   1. Create a Flex Query for your trading history
   2. Create a Flex Query for your dividend history

---

## Options trading assistant for Interactive Brokers (IBKR)

**Bolded** means I'm currently working on it

### Portfolio Analytics
1. **Visualize performance for some specified options strategy**
   * covered calls


### Historic Correlation
  


### Real time screener 
1. Potential opportunities for alpha
   * Deviations from historic correlation
   * Sharp deviations from historic implied volatility
   * Options mispricing (e.g. long-dated ITM)
   * Unusual options purchasing activity
   * Aggregate sentiment metrics (e.g. put to call ratio)



## Documentation

[Scratchpad](https://www.notion.so/StreamAlpha-ca70926638de42e0a90f6e0015555b52) (WIP)

[Roadmap](https://www.notion.so/ae782ee9864647568e341f2e2fbeb05b?v=72cc477867124f568cbb34b08ff14b58) (WIP)

technical architecture (coming soon)

## Reference Links
* https://github.com/erdewit/ib_insync
* https://interactivebrokers.github.io/tws-api/




