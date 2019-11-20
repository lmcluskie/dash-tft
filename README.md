# dash-tft
 TFT shop odds calculator presented in a dash app
 
 
 Inputs:
 * level when rolling 
 * tier of champion being looked for 
 * desired number of copies 
 * all players collective ownership of copies of the champion 
 * all players collective ownership of copies of champions in the tier 
 
 
 For each scenario determined by the input an absorbing Markov chain is created. An initial state vector where the user is guaranteed to start with 0 copies is multiplied by this Markov chain raised to powers from 1-100 to find the likelihood of having reached the absorbing state (signalling objective success) after each roll from 1 to 100.
 

Last updated 20/Nov/2019 (Patch 9.23)
