# Finnie capstone demo

Aim for about eight minutes. Open Finnie in a browser and have the README and terminal ready. Allow microphone access before recording if you plan to show voice input. Use the sample portfolio and fictional savings figures.

| Time | Show on screen | Suggested narration |
| --- | --- | --- |
| 0:00–0:40 | Open Finnie and show the architecture diagram in the README. | “Finnie is an educational finance assistant. LangGraph routes questions to six specialists. Finance Q&A and Tax Education retrieve evidence from a shared FAISS index and cite their sources.” |
| 0:40–1:55 | In Chat with Automatic routing, ask “What is an ETF?” and follow up with “How does it differ from a mutual fund?” Open **Sources**. Use the microphone for either question if convenient. | “Finnie carries context across turns. The Sources panel shows where the answer comes from. With voice input, I stop recording, review the transcript, then send it.” |
| 1:55–3:05 | In Portfolio, load the sample holdings and click **Analyze holdings**. Show the quote timestamps, portfolio value, and allocation chart. | “I give Finnie quantities and tickers. Finnie fetches the latest available prices and calculates the allocations. The concentration metric describes the holdings you entered.” |
| 3:05–4:55 | In Market, select Costco from the watchlist, show the price timestamp, and switch chart periods. In Chat ask “Why did Costco’s stock move differently from the broader U.S. market today?” Show the **Market → News** label and citations. | “Market compares Costco with SPY. News checks what the reporting says and cites its sources. If the reporting leaves the cause unclear, Finnie says so and lists recent headlines for context.” |
| 4:55–6:05 | In Goals, enter a $1,200 target, one year, $0 current savings, $80 per month, 0% return, and Moderate risk appetite. Click **Calculate projection**. | “The chart projects $960 and a $240 shortfall. The target requires $100 per month, so the plan needs another $20 each month. Moderate records the user’s risk preference. The stated return is the input used for growth.” |
| 6:05–6:45 | Ask “What is a long-term capital gain?” Show the Tax Education label and Sources. | “Tax has its own instructions and prioritizes IRS sources. The response can explain the U.S. federal concept and state which details depend on jurisdiction or year.” |
| 6:45–8:00 | Show the test result, the README setup steps, and the MCP tool list. If an MCP client is ready, demonstrate the savings calculator. | “Python computes the portfolio metrics and savings projection. An MCP client can also call the calculations and quote service. The tests cover the specialist handoff, session isolation, and failure cases.” |

Rehearse the Chat and Market prompts on the deployment before recording. Live services can take time and return different quotes or headlines when you record. The goal example uses fixed inputs so you can verify the result.
