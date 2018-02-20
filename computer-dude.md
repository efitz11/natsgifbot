## The reddit COMPUTER-DUDE bot (/u/COMPUTER-DUDE)

### What is it?
Computer-Dude is a reddit bot that allows users on /r/Nationals (and perhaps other subs later) to search the /r/NationalsGIFs subreddit for a gif. It'll respond to username mentions with a gif.

### How does it work?
Computer-Dude only responds to username mentions. Summon Computer-Dude with `/u/computer-dude <query>` and he'll respond with a gif that matches your query. All the gif titles are taken from the subreddit /r/NationalsGIFs (so submit your future gifs with descriptive titles). You can see the list of gifs [here](postlist.csv).

To go more in depth about the gif matching algorithm: each word is treated as its own keyword. Therefore, the query `max pump` will match `max pump` exactly but also `max fist pump`, even though there's a word in between the two words in the query. This is so you can add additional words to narrow down your search but not eliminate any gifs that don't match exactly how you searched it. Another thing to note is it's a simple pattern match where you don't have to match the whole word: `stras` will match both `stras` and `strasburg`.

Next thing to know is that in the event your query matches multiple gifs, computer-dude will respond with 1 of the matches *at random*. So if you're looking for a specific gif, use more words in your query to narrow the search down!

The last thing to know is you can have multiple gif requests in a single comment! Just have each query on a different line, and the bot will respond with a gif for each query!
