# Brewhouse Software
This software is for managing the processes, equipment, and inventory for the brewhouse company, whilst also making predictions of future sales and recommendations on what to brew next. The software is displayed with a basic user interface, in order for the features to be visually monitored. 

### Prerequisites
In order for the software to work on your system, you should have python 3.8 or higher installed (install it here: https://www.python.org/downloads/release/python-380/).

### Getting started
Extract all of the files of repositry to the **same directory**,
Open a cmd terminal by going to the search bar and entering cmd,
Enter cd <your directory where you extracted the files>,
Enter 	python main.py
The program should compile and the software window should appear.

### Manual
Follow the 'Getting started' section to get the program running. 

Adding a new batch to the production line
	* Under the 'Add New Batch' tab on the left-hand side of the form you can select the type of brew that you would like to produce using the buttons
	* Enter the volume of the batch (in litres) in the text box. Batches must be between 1 and 1000 litres inclusively.
	* Add the new batch to the system by selecting the Add batch to hot brew button.
	
View the current inventory of filled bottles
	* On the left-hand side of the form select the 'Current Inventory' tab. The number of bottles of each type of beer will be displayed.
	
Calculate a prediction of demand for a month in the future
	* At the top of the form inside the 'Calculate sales prediction' section you can enter the number of months in the future that you would like to predict for.
	* Click the calculate button after entering a value and the table will update with the predicted sale values for that month.

Move a batch to the next stage of production
	* On the right hand side of the form there is a list of all current batches in production.
	* Find the batch you would like to move to the next stage, and enter it's gyle number in the text box below the list.
	* Press the 'Update' button, and the list box below will populate with the names of all possible containers which the batch can go into.
	* Select which container you would like the batch to go into (batches which are going into the conditioning stage and are in tanks with both fermenting and conditioning capabilities can stay in the same tank if needed)
	* Once the container is selected, click the 'Use this container' button. The batch will be moved to the next stage of production.
	
View Container Statuses
	* On the left hand side of the form there is a list of all tanks.
	* Select a tank to view it's relevant information
	* The information will be printed besides the list.
	
View brew recommendation
	* At the bottom left hand corner of the form there is a recommendation on which type of brew is best to make next, with some short reasoning
	* This recommendation updates automatically whilst using the program.
	




