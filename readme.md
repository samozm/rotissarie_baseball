# Rotissarie Baseball Draft Optimizer

## About
See `writeup.pdf` for more details on the intuition behind this.

## Files
`draftbot3000.py` is the extent of the program. It relies on the data in `razzball-hitters-prices.csv`, `razzball-hitters.csv`, `razzball-pitchers-prices.csv`, and `razzball-pitchers.csv`. These are the razzball/steamer projections downloaded from razzball.com. All of the other csv files are left over from previous iterations of this project. 
`Baseball_Drafter.ipynb` is the notebook I used to explore solutions for the optimization portion of this project. Essentially, it is my notes.

## Notes
The commenting and cleanliness of `draftbot3000.py` is atrocious, owing to the rushed manner in which I put it together in time for the baseball season. 

## Future work
First and foremost, I need to modify the draftbot to use a database to improve performance and prevent the user from losing all of their work when exiting the program. I'd like to rewrite it to work in the browser with django. 
I also have some new thoughts about the problem itself. I think modeling it like a neural network, where the ranking function works as the activation function, would be more appropriate for the task, and I'd like to explore this further.