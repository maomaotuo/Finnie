# Finnie capstone demo

Aim for about eight minutes across seven clips. The times below refer to the combined video. Open Finnie in a browser and have the README and terminal ready. Allow microphone access before recording if you plan to show voice input. Use the sample portfolio and fictional savings figures.

## Clip 1 · Introduction (0:00–0:40)

**Show on screen.** Open Finnie and point to the four tabs. Show the architecture diagram in the README while introducing LangGraph.

**Suggested narration**

> Hi, this is Finnie, my Applied Agentic AI capstone. I built it for people who want to learn financial concepts and see how they apply to a portfolio or a savings goal.
>
> The interface has four tabs. Chat is where I ask questions. Portfolio, Market, and Goals let me work with the data directly. Behind the interface, LangGraph coordinates six specialists for financial education, portfolio analysis, market analysis, goal planning, news, and tax education.

## Clip 2 · Multi-turn chat and voice (0:40–1:55)

**Show on screen.** Leave routing on **Automatic**. Ask “What is an ETF?” Follow up with “How does it differ from a mutual fund?” Open **Sources** and point to a citation and the specialist label.

**Suggested narration**

> I’ll start with a question a new investor might ask. Finnie sends it to Finance Q&A. That specialist retrieves passages from the knowledge base using FAISS and uses the passages to write an answer with citations.
>
> My follow-up is “How does it differ from a mutual fund?” The word “it” refers to the ETF from the previous turn. Finnie uses that context to answer the comparison without asking me to repeat the subject.
>
> I can open Sources to see which documents were retrieved. The match distance shows how close a retrieved passage was to the search query. Lower distance means a closer match.

**Optional voice narration.** Use the microphone for the follow-up and pause to show the transcript before sending.

> I’ll click the microphone, say my question, and click the square to stop. Whisper puts the transcript in the chat box. I can fix a word or ticker, then click the arrow to send it.

## Clip 3 · Portfolio analysis (1:55–3:05)

**Show on screen.** In Portfolio, click **Load illustrative sample portfolio**, then **Analyze holdings**. In **Prices used in this analysis**, point to one holding’s quantity, USD unit price, holding value, and quote timestamp. Show the portfolio total and allocation chart.

**Suggested narration**

> I’ll load the sample tickers and share counts. The valuation appears after I click Analyze holdings and Finnie successfully fetches the prices.
>
> Here’s the USD price per share, the number of shares, and the value of this holding. Finnie multiplies price by quantity and adds up the holding values to get the portfolio total. Each analysis fetches quotes from Yahoo Finance. If the market is closed, a fresh request can still return a price from the last trading session. The timestamp tells me when the quote was recorded.
>
> The allocation chart makes it easy to see which position accounts for the largest share. Finnie also shows a concentration score based on the holdings entered here. That score measures how much value is concentrated in a few positions.

If a price refresh fails during recording, Finnie names the ticker and clears the valuation. Retry **Analyze holdings** before recording the results.

## Clip 4 · Market data and the News handoff (3:05–4:55)

**Show on screen.** Select Costco in the Market watchlist. Show the price timestamp and switch chart periods. In Chat, ask “Explain what drove Costco’s stock to move differently from the broader U.S. market today.” Point to **Market → News**, **What the reporting says**, and the source links when available.

**Suggested narration**

> I’ll select Costco from the Market watchlist. Finnie shows its latest available quote and the time of that quote. Here I can switch from the latest trading session to a longer history. If I’m recording outside market hours, the timestamp tells me which session the price comes from.
>
> Now I’ll ask what drove Costco to move differently from the broader U.S. market. The supervisor recognizes that answering this takes both market data and news context. Market Analysis measures Costco’s return and compares it with SPY over the same period. It then passes the ticker and comparison to News.
>
> The price comparison shows how far the two moved. The reporting section tells me what the sources say about possible drivers. If the available reporting leaves the reason unclear, Finnie says so and still shows recent headlines for context. The label below the response shows that both specialists worked on the question.

## Clip 5 · Savings goal (4:55–6:05)

**Show on screen.** In Goals, enter a $50,000 target, a 10-year timeline, $0 in current savings, $250 per month, a 4% assumed annual return, and Moderate risk appetite. Click **Calculate projection**. Point to the projected balance, shortfall, required monthly contribution, and chart.

**Suggested narration**

> I’ll set a goal of saving fifty thousand dollars in ten years. I’m starting from zero, putting in two hundred and fifty dollars at the end of each month, and assuming a four percent annual return.
>
> Over ten years, I’d put in thirty thousand dollars. With growth, Finnie projects a balance of about thirty-six thousand six hundred and seventy-four dollars. That leaves me about thirteen thousand three hundred and twenty-six dollars short. To reach my target in ten years at the same assumed return, I’d need about three hundred and forty-one dollars a month, or roughly ninety-one dollars more than I’m saving now.
>
> On the chart, I can see my total deposits and my projected balance month by month. The gap between those lines is the growth from the four percent assumption. Moderate records my risk preference, and the four percent is an assumption for this example.

## Clip 6 · Tax Education (6:05–6:45)

**Show on screen.** Return to Chat and ask “What is a long-term capital gain?” Show the **Tax Education** label and expand **Sources**.

**Suggested narration**

> This question goes to Tax Education. It shares the retrieval pipeline I showed earlier, with its own instructions and a preference for IRS sources when explaining U.S. federal tax concepts.
>
> Here I can review how the answer explains the concept and open the cited material. If I ask for a specific rate or threshold, the jurisdiction and tax year matter.

## Clip 7 · Technical evidence and close (6:45–8:00)

**Show on screen.** Point to the README setup steps, test results, and MCP tool list. If an MCP client is ready, use it to run the savings projection.

**Suggested narration**

> The README shows how to run Finnie locally and how the six specialists fit together. The portfolio and goal numbers come from Python calculators. The language model helps route questions and explain results.
>
> The verification notes show eighty-one passing tests and ninety-one percent coverage across the measured backend modules. The tests cover retrieval, session isolation, calculator results, and the handoff from Market to News.
>
> Finnie also exposes three tools through MCP. A compatible client can ask for a portfolio analysis, a savings projection, or a market quote. For example, it can ask the goal tool how much to save each month to reach a target.
>
> That’s Finnie. The same app can answer a follow-up question, explain a market move using sources, and show the numbers behind a savings plan. Thanks for watching.

Rehearse the Chat and Market prompts before recording. Live services can take time and return different quotes or headlines. The goal example uses fixed inputs so you can verify the result. Trim long waits between actions when you join the clips.
