# Pokemon GSC Trade Spoofer

Trade whatever Pokemon you want to your childhood Pokemon Gold/Silver/Crystal versions.


## Developer Guide

### Pokemon Trading State Machine 🎰

Pokemon trades involve a several [amount of states](https://blog.gbplay.io/2021/05/11/Emulating-a-Pokemon-Trade-with-Generated-Link-Cable-Data.html) 
(connecting with player, waiting in trade room, exchange random seed, etc...).

Managing those states and its associated behavior with `if` `else` statements is a pain in the ass. 
Engaging the developer to use bad practices and code smells like global states. 
Moreover, the code rapidly becomes hard and follow for people trying to go through it. 
Therefore, I decided to implement this logic of switching states and behaviors using a 
slight modification of the State pattern defined [here](https://python-3-patterns-idioms-test.readthedocs.io/en/latest/StateMachine.html).

State Machine Components:

- `State`: Has a `run` method which implements the behavior of the according state and 
returns an instance of the next state. Additionally, the `run` method receives a `Context`
object as a parameter. 

- `Context`: Contains the state machine shared information. In our case: the Pokemon to be traded, 
the received party from the other player, etc.

- `StateMachine`: The state machine itself is the owner of the `Context` and keeps a reference
to the current state. Every time, the `State.run` returns, the state machine manages the
execution of the new state.

See in the image below the state machine implemented:


## Shout-out and credits

- Thanks for the amazing [write up](https://blog.gbplay.io/2021/05/11/Emulating-a-Pokemon-Trade-with-Generated-Link-Cable-Data.html) 
on how to use BGB link cable data to emulate Pokemon R/B/Y trades.

- BGB Link Server base implementation from [Matt Penny](https://github.com/mwpenny)
