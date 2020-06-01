"""
This module is a program that manages processes in a brewhouse
with a basic user interface
"""
import time
import logging
from datetime import datetime
from typing import Tuple
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from tkinter.font import Font
import brewery
import prediction

beers = ("Organic Pilsner", "Organic Dunkel", "Organic Red Helles")
logging.basicConfig(filename='logfile.log', level=logging.DEBUG,
                    format='%(asctime)s %(message)s')


def planning_algorithm() -> None:
    """
    Finds the most appropriate beer to brew next and prints it

    This subroutine finds the most appropriate beer by considering
    the current inventory of beers, and the batches currently inside
    the tanks. It calculates using the predictions which beer will
    run out of stock first, and on which month. If all of the equipment
    is in use, the function will not make a prediction until a tank is
    empty.
    """
    found = False
    months = 1
    production_totals = []
    total_bottles = sum_all_beers()  # sums all stock and batches in tanks
    for beer, total in total_bottles.items():
        production_totals.append(total)  # total bottles for beer added to list
    while not found:
        ratio, predictions = prediction.growth_rate(months)  
        # prediction calculated
        min_amount, index_of_beer = find_most_understocked_beer(predictions
                                                        , production_totals)
        if min_amount < 0:
            found = True  # first understocked beer found
        else:  # predictions are subtracted from stock
            production_totals[0] -= predictions['Organic Red Helles']['prediction']
            production_totals[1] -= predictions['Organic Pilsner']['prediction']
            production_totals[2] -= predictions['Organic Dunkel']['prediction']
            months += 1  # if beers are not understocked check for next month
    if index_of_beer == 0:
        beer = 'Organic Red Helles'
    elif index_of_beer == 1:
        beer = 'Organic Pilsner'
    elif index_of_beer == 2:
        beer = 'Organic Dunkel'
    # checks to see if there are available tanks
    availability = brewery.check_equipment_availability()
    if availability:  # if tanks are available
        planning_prediction = Label(PLANNING_FRAME,
            text="%s is the best choice based on\nthe current demand,\
stock and batches in production." % (beer))
        planning_prediction.grid(row=0, column=0)  # labels created and placed
        stock_label = Label(PLANNING_FRAME, text="You have enough \
stock to last for %d month(s)" % months)
        stock_label.grid(row=1, column=0)  # recommendation printed
        prediction_label = Label(PLANNING_FRAME, text="In month %d you \
should only have %d bottles" %
                        (months, int(production_totals[index_of_beer])))
        prediction_label.grid(row=2, column=0)
        month_sale = int(predictions[beer]['prediction'])
        label_sale = Label(
            PLANNING_FRAME, text="In month %d you are expected to sell %d bottles" %
            (months, month_sale))
        label_sale.grid(row=3, column=0)
        logging.info(
            "%s recommended as the most viable beer to produce" %
            beer)
    else:
        planning_prediction = Label(
            PLANNING_FRAME,
            text="There are no available facilities to start a new batch right now.")
        planning_prediction.grid(row=0, column=0)


def update_predictions() -> None:
    """Updates the predictions table"""
    try:
        # gets the number of months from the text box
        timeframe = int(MONTHS.get())
    except BaseException:
        messagebox.showerror("Error", "Please enter a positive integer")
        logging.error(
            "ERROR User attempted to enter %s for the MONTHS" %
            MONTHS.get())
        return
    draw_predictions(timeframe)  # prints the table of predictions
    logging.info("New prediction calculated for %s months" % timeframe)


def find_most_understocked_beer(predictions: dict, totals: list) -> Tuple:
    """
    This function finds the most understocked beer based on the predictions

    Arguments:
    predictions - dictionary containing the month prediction for the beer.
    """
    month_predictions = []
    for beer, prediction in predictions.items():
        month_predictions.append(prediction['prediction'])
    difference = []
    for i in range(3):  # predicted sales for each beer subtracted from stock
        difference.append(totals[i] - month_predictions[i])
    minimum_stock = min(difference)  # beer with least stock left found
    beer = difference.index(minimum_stock)
    return minimum_stock, beer


def sum_all_beers() -> dict:
    """Calculates the total bottles of each beer in the inventory"""
    data = brewery.read_data('inventory')  # inventory data read in
    total_bottles = {
        'Organic Red Helles': 0,
        'Organic Pilsner': 0,
        'Organic Dunkel': 0}
    for key, batchdata in data.items():
        bottles = batchdata['volume'] // 0.5  # number of bottles calculated
        total_bottles[batchdata['recipe']] += bottles  # bottles added to list
    return total_bottles


def create_new_batch() -> None:
    """
    Adds a new batch of a user-specified brew to the production line

    This subroutine adds a new batch to the hot brew phase of
    production, after the user enters the volume, and what
    type of beer the brew is. The subroutine automatically applies
    a new unique gyle number to the batch.
    """
    recipe = beers[int(VAR.get())]  # beer retrieved from radiobuttons
    valid = True
    try:
        volume = int(VOLUME_ENTRY.get())  # volume retrieved from text box
    except BaseException:
        messagebox.showerror("Error", "Please enter a positive integer.")
        valid = False
    if valid:  # if the user enters a valid volume
        if volume <= 1000 and volume > 0:
            gyle = calculate_gyle_number()  # new gyle number made
            next_batch = {str(gyle): {  # batch created
                "id": 0,
                "gyle": gyle,
                "state": "hot brew",
                "volume": volume,
                "recipe": recipe
            }}
            brewery.add_brew(next_batch)  # batch written to file
            messagebox.showinfo(
                "Add brew",
                "New batch added to the hot brew stage successfully.")
            display_batches()  # batches updated on screen
            logging.info("New batch with gyle number %d created" % gyle)
        else:
            messagebox.showerror(
                "Error",
                "Incorrect batch size. Please enter a size between 0 and 1000 litres.")
            logging.error("ERROR User entered incorrect batch size")


def batch_exists(gyleNumber: int) -> bool:
    """Checks if a batch exists under a given gyle number"""
    batches = brewery.read_data('inventory')  # inventory data read in
    for key, value in batches.items():
        if key == str(gyleNumber):  # checks if the batch is in the file
            return True  # returns true if the batch exists
    return False


def calculate_gyle_number() -> int:
    """
    Calculates a new unique gyle number for the next batch to be produced

    Reads through the list of sold batches and batches currently in
    production and finds the highest past gyle number, and adds 1 to it
    to create a new unique gyle number.
    """
    orders = prediction.csv_read()  # reads in list of all past orders
    highest_gyle = 0
    def list_sort(k): return int(k['Gyle Number'])  # sorts list by gyle no.
    # highest gyle number from the past orders chosen
    gyle = sorted(orders, key=list_sort)[-1]['Gyle Number']
    current_batches = brewery.read_data("inventory")
    if current_batches:
        for batch in current_batches:  # highest gyle from stock chosen
            if int(current_batches[batch]['gyle']) > highest_gyle:
                highest_gyle = int(current_batches[batch]['gyle'])
    if int(gyle) > highest_gyle:  # highest gyle found
        highest_gyle = gyle
    return int(highest_gyle) + 1  # new gyle number created


def draw_predictions(timeframe: int = 1) -> None:
    """
    Draws out the prediction table with headers and prefilled data

    This subroutine creates a table of predicted sale values for
    all 3 beers, and includes the average monthly sale for each beer,
    and the ratio of sales between all 3 beers, as well as the predicted
    sale for the month given by the user.

    Arguments:
    timeframe - the number of months in the future to predict for (default 1)
    """
    ratio, predictions = prediction.growth_rate(timeframe)
    # predictions calculated
    i = 2
    for key, value in predictions.items():  # rows
        b = Entry(LABELFRAME)  # vertical headers drawn
        b.insert(END, str(key))
        b.grid(row=i, column=0)
        b.config(state="disabled")
        i += 1
        j = 1
        for name, data in value.items():
            b = Entry(LABELFRAME)  # horizontal headers drawn
            b.insert(END, str(name).capitalize())
            b.grid(row=1, column=j)
            b.config(state="disabled")
            j += 1
    i = 2
    for key, value in predictions.items():
        j = 1
        for name, data in value.items():
            output = str(data)
            if name in ('average', 'prediction'):
                output += " bottles"
            elif name == "growth":
                output = float(output) * 100
                output = "+%.1f%%" % float(output)
            b = Entry(LABELFRAME)  # prediction data drawn
            b.insert(END, output)
            b.grid(row=i, column=j)
            b.config(state="disabled")
            j += 1
        i += 1
    i = 2
    for item in ratio:  # ratios drawn
        b = Entry(LABELFRAME)
        b.insert(END, item)
        b.grid(row=i, column=4)
        b.config(state="disabled")
        i += 1
    labelMonths = Label(LABELFRAME, text="Months: %d" % int(timeframe))
    labelMonths.grid(row=6, column=0)
    b = Entry(LABELFRAME)
    b.insert(END, "Ratio of past sales")
    b.grid(row=1, column=4)
    b.config(state="disabled")


def display_inventory(event="") -> None:
    """Displays the number of bottles of each beer in the inventory"""
    beers = brewery.bottled_beers()  # number of bottles of each beer found
    i = 0
    for beer, bottles in beers.items():  # values printed to form
        INVENTORY_LABELS[i].config(text="%s: %d bottles" % (beer, bottles))
        i += 1


def display_containers(event="") -> None:
    """
    Displays information about the currently selected container

    Each container is listed on the left side of the screen.
    Next to the list is information about the currently selected
    tank. By default, the information for 'albert' is displayed.
    """
    try:
        if not event:
            container = "albert"  # by default 'albert' is displayed
        else:
            container = CONTAINER_LIST.get(CONTAINER_LIST.curselection())
        containers = brewery.get_container(container)  # container data
        string = ""
        containers['Volume'] += " litres"
        for key, value in containers.items():  # container data printed to form
            string += ("%s: %s\n" %
                       (str(key.capitalize()), str(value.capitalize())))
        CONTAINER_LABEL.config(text=string)
    except TclError:
        pass


def display_container_data(event="") -> None:
    """
    Displays information about the tank to be used in the next stage
    """
    # gets container from user selection
    container = POSSIBLE_CONTAINER_LIST.get(
        POSSIBLE_CONTAINER_LIST.curselection())
    string = ""
    container_info = brewery.get_container(
        container.lower())  # gets container data
    string = ""
    container_info['Volume'] += " litres"
    for key, value in container_info.items():
        if value == "In Use":
            # if container is in use by current batch
            value = "Can be used again"
        string += ("%s: %s\n" % (str(key.capitalize()), 
                                str(value.capitalize())))
        # data printed to form
    BUTTON_UPDATE.config(state="normal")
    CONTAINER_DATA.config(text=string)


def display_batches() -> None:
    """Displays the list of all batches in production and data about them"""
    BATCHES.config(state="normal")
    strings = brewery.get_production_batches()
    BATCHES.delete('1.0', END)
    i = 1.0
    j = 1
    for batch in strings:
        BATCHES.insert(INSERT, batch)  # current batches displayed
        BATCHES.tag_add(str(i), i, i + 6)
        if j % 2 == 0:
            BATCHES.tag_config(str(i), background="#E0E0E0")
            # background colour changed to make it easier to read
        else:
            BATCHES.tag_config(str(i), background="white")
        i += 6.0
        j += 1
    BATCHES.config(state="disabled")


def remove_batch() -> None:
    """Deletes a batch from the system when the user chooses to"""
    try:
        gyle_number = int(gyle.get())
        # gyle number retrieved from user input
    except ValueError:
        messagebox.showerror("Error", "Enter an integer value.")
        return  # exits subroutine
    if batch_exists(gyle_number):  # if the batch requested exists
        if gyle_number:  # if the user made a valid input
            MsgBox = messagebox.askquestion(
                'Delete Batch', 'Are you sure you want to delete the batch number %s?' %
                gyle_number, icon='warning')
            if MsgBox == 'yes':  # if the user selects 'yes' from the prompt
                brewery.delete_batch(gyle_number)  # batch removed from file
                display_batches()  # batches refreshed
                messagebox.showinfo(
                    "Delete Batch", "Batch successfully deleted.")
                logging.info("Batch %d deleted" % gyle_number)
        else:
            messagebox.showerror(
                "Error", "Please enter the gyle number of the batch you would like to delete.")

    else:
        messagebox.showerror(
            "Error",
            "There are no batches with the gyle number %d" %
            gyle_number)
        logging.error("ERROR User entered wrong gyle number to delete")


def save_state() -> None:
    """
    Saves the new state of the batch after being moved to next phase

    This subroutine handles saving the new state of the batch after
    the user moves it to the next stage of production, and also
    handles clearing the state of the previous tank, if the batch
    has changed tanks.
    """
    # full batch data retrieved
    batch_data = brewery.get_batch_data(str(gyleNumber))
    finish_time = ""
    volume = batch_data['volume']
    if batch_data['state'] == "hot brew":
        # get name of fermenting tank for next stage
        container = POSSIBLE_CONTAINER_LIST.get(
            POSSIBLE_CONTAINER_LIST.curselection())
        finish_time = brewery.calculate_finish_time(True)  # get finish time
        state = "fermentation"  # new state declared
    elif batch_data['state'] == "fermentation":
        # get name of conditioning tank for next stage
        container = POSSIBLE_CONTAINER_LIST.get(
            POSSIBLE_CONTAINER_LIST.curselection())
        finish_time = brewery.calculate_finish_time(False)
        state = "conditioning"
    elif batch_data['state'] == "conditioning":
        state = "bottling"  # new state declared
        container = state
    elif batch_data['state'] == "bottling":
        brewery.add_batch_to_inventory(batch_data)  # batch added to stock
        logging.info(
            "Batch %d successfully moved to the inventory." %
            gyleNumber)
    brewery.update_containers(
        batch_data,
        finish_time,
        state,
        container.lower())
    display_batches()  # batches refreshed
    POSSIBLE_CONTAINER_LIST.delete(0, END)  # clear possible container list
    CONTAINER_DATA.config(text="")
    BUTTON_UPDATE.config(state="disabled")
    messagebox.showinfo(
        "Success", "Batch %d successfully moved to the %s phase." %
        (gyleNumber, state))
    logging.info(
        "Batch %d successfully moved to the %s phase." %
        (gyleNumber, state))


def update() -> None:
    """
    Displays all the possible containers a batch can go into when updating

    This subroutine is triggered after pressing the 'update' button, and
    handles the updating of the list box which contains all of the
    possible containers a specific batch of beer can go into when it needs
    to be moved to the next stage of production.
    """
    global containers
    global gyleNumber
    containers = {}
    POSSIBLE_CONTAINER_LIST.delete(0, END)
    try:
        gyleNumber = int(gyle.get())  # gets the gyle number from user
    except ValueError:
        messagebox.showerror("Error", "Enter an integer value.")
        return
    if batch_exists(gyleNumber):  # if the batch exists
        batch_data = brewery.get_batch_data(str(gyleNumber))
        volume = batch_data['volume']
        if batch_data['state'] == "hot brew":
            # get list of all possible fermenting tanks
            containers = brewery.get_possible_containers(
                volume, True, False, batch_data)
        elif batch_data['state'] == "fermentation":
            # get list of all possible conditioning tanks
            containers = brewery.get_possible_containers(
                volume, False, True, batch_data)
        elif batch_data['state'] == "conditioning":
            MsgBox = messagebox.askquestion(
                'Batch Processing',
                'The batch %d is in a conditioning tank and needs to be moved to the bottling stage. Are you sure you want to move this batch from this tank to the bottling stage?' %
                gyleNumber,
                icon='warning')
            if MsgBox == 'yes':
                save_state()  # move batch to bottling phase
            state = "bottling"
            selection = state
        elif batch_data['state'] == "bottling":
            MsgBox = messagebox.askquestion(
                'Batch Processing',
                'Add batch %d to the inventory of bottled beers?' %
                gyleNumber,
                icon='warning')
            if MsgBox == 'yes':
                brewery.add_batch_to_inventory(batch_data)  # add to stock
                display_batches()  # refresh inventory
                logging.info(
                    "Batch %d successfully moved to the inventory." %
                    (gyleNumber, state))
        if batch_data['state'] in ("fermentation", "hot brew"):
            if containers:
                for key, value in containers.items():
                    POSSIBLE_CONTAINER_LIST.insert(END, key.capitalize())
            else:
                messagebox.showerror(
                    "Error", "There are no containers available for a batch of this size.")
                logging.warning("WARNING All containers unavailable")
    else:
        messagebox.showerror(
            "Error",
            "There are no batches with the gyle number %d" %
            gyleNumber)
        logging.error("ERROR User entered wrong gyle number")


if __name__ == "__main__":
    containers = {}
    prediction.csv_read()
    WINDOW = Tk()
    WINDOW.title("Barnaby's Brewhouse")  # form drawn
    WINDOW.geometry("+0+0")
    WINDOW.geometry('655x625')

    # draws the prediction section
    LABELFRAME = LabelFrame(WINDOW, text="Calculate sales prediction")
    LABELFRAME.grid(row=0, column=0, columnspan=4,
                    padx=5, pady=5, ipadx=5, sticky="NW")
    LBLMONTHS = Label(LABELFRAME, text="Enter months: ")
    LBLMONTHS.grid(row=0, column=0, sticky="E")
    MONTHS = Entry(LABELFRAME)
    MONTHS.grid(row=0, column=1, columnspan=1, padx=5, sticky="W")
    ACCEPTBUTTON = ttk.Button(
        LABELFRAME,
        text="Calculate",
        command=update_predictions)
    ACCEPTBUTTON.grid(row=0, column=2, columnspan=1, pady=5)
    draw_predictions()

    # draws the 'add a batch' and 'display inventory' section
    BATCH_TABS = ttk.Notebook(WINDOW)
    BATCH_TAB_1 = Frame(BATCH_TABS)
    BATCH_TABS.add(BATCH_TAB_1, text="Add New Batch")
    BATCH_TAB_2 = Frame(BATCH_TABS)
    BATCH_TABS.add(BATCH_TAB_2, text="Current Inventory")
    BATCH_TAB_2.bind("<Visibility>", display_inventory)
    BATCH_TABS.grid(
        row=1,
        rowspan=2,
        column=0,
        columnspan=2,
        padx=5,
        pady=5,
        sticky="NW")
    VAR = StringVar(value="0")
    for beer in beers:
        R1 = Radiobutton(
            BATCH_TAB_1,
            text=beer,
            variable=VAR,
            value=beers.index(beer))
        R1.grid(
            row=beers.index(beer),
            column=0,
            columnspan=1,
            padx=1,
            pady=1,
            sticky="W")
    VOLUME_LABEL = Label(BATCH_TAB_1, text="Enter the volume of the batch:")
    VOLUME_LABEL.grid(row=0, column=1, padx=1, sticky="W")
    VOLUME_ENTRY = Entry(BATCH_TAB_1)
    VOLUME_ENTRY.grid(row=1, column=1, padx=5, sticky="EW")
    BATCH_BUTTON = ttk.Button(
        BATCH_TAB_1,
        text="Add batch to hot brew",
        command=create_new_batch)
    BATCH_BUTTON.grid(row=2, column=1, padx=2.5, pady=2.5, sticky="NSEW")

    # inventory drawn
    INVENTORY_LABELS = []
    for i in range(3):
        STOCK_LABEL = Label(BATCH_TAB_2, text="")
        STOCK_LABEL.grid(row=i, column=0, pady=5, padx=5, sticky="W")
        INVENTORY_LABELS.append(STOCK_LABEL)

    CONTAINER_FRAME = LabelFrame(
        WINDOW,
        text="View Container Statuses",
        width=250,
        height=195)
    CONTAINER_FRAME.grid(
        row=3,
        rowspan=6,
        columnspan=2,
        padx=5,
        pady=5,
        ipadx=5,
        sticky="NWE")
    CONTAINER_LIST = Listbox(CONTAINER_FRAME)
    CONTAINER_LIST.grid(row=0, column=0, padx=5, pady=5)
    containers = brewery.read_data('containers')
    for item in containers:
        CONTAINER_LIST.insert(END, item.capitalize())
    CONTAINER_LIST.bind('<<ListboxSelect>>', display_containers)
    CONTAINER_LABEL = ttk.Label(CONTAINER_FRAME, text="")
    CONTAINER_LABEL.grid(row=0, column=1, padx=10, pady=10, sticky="NSEW")
    CONTAINER_FRAME.grid_propagate(0)
    display_containers()

    # current production batches section drawn
    BATCH_FRAME = LabelFrame(
        WINDOW,
        text="View Current Production Batches",
        width=322,
        height=200)
    BATCH_FRAME.grid(
        row=1,
        rowspan=3,
        column=2,
        columnspan=2,
        padx=5,
        pady=5,
        ipadx=5,
        sticky="NWE")
    BATCH_FRAME.columnconfigure(0, weight=1)
    BATCH_FRAME.rowconfigure(0, weight=1)
    BATCH_FRAME.grid_propagate(0)
    BATCHES = ScrolledText(BATCH_FRAME)
    BATCHES.grid(row=0, column=0, columnspan=5)
    BATCHES['font'] = Font(family="Helvetica", size=8, weight="bold")
    display_batches()
    LBLGYLE = Label(BATCH_FRAME, text="Enter gyle number: ")
    LBLGYLE.grid(row=1, column=0, sticky="W")
    gyle = Entry(BATCH_FRAME)
    gyle.grid(row=1, column=1, sticky="W")
    UPDATEBUTTON = Button(BATCH_FRAME, text="Update", command=update)
    UPDATEBUTTON.grid(row=1, column=2, columnspan=1, padx=1)
    DELETE_BUTTON = Button(BATCH_FRAME, text="Delete", command=remove_batch)
    DELETE_BUTTON.grid(row=1, column=3, columnspan=1)

    # move current batches to next production stage section drawn
    gyleNumber = 0
    UPDATE_FRAME = LabelFrame(
        WINDOW,
        text="Move current batches to next production stage",
        width=250,
        height=250)
    UPDATE_FRAME.grid(
        row=4,
        rowspan=10,
        column=2,
        columnspan=2,
        padx=5,
        ipadx=5,
        sticky="NWE")
    SELECT_LABEL = Label(
        UPDATE_FRAME,
        text="Enter a gyle number above and click 'Update':")
    SELECT_LABEL.grid(row=0, columnspan=5, column=0, padx=5, sticky="W")
    POSSIBLE_LABEL = Label(
        UPDATE_FRAME,
        text="List of all available large enough containers:")
    POSSIBLE_LABEL.grid(row=1, columnspan=3, column=0, padx=5, sticky="NW")
    POSSIBLE_CONTAINER_LIST = Listbox(UPDATE_FRAME)
    POSSIBLE_CONTAINER_LIST.grid(row=2, column=0, padx=5, pady=5, sticky="NW")
    CONTAINER_DATA = ttk.Label(UPDATE_FRAME, text="")
    CONTAINER_DATA.grid(row=2, column=1, padx=10, pady=10, sticky="NW")
    POSSIBLE_CONTAINER_LIST.bind('<<ListboxSelect>>', display_container_data)
    UPDATE_FRAME.grid_propagate(0)
    BUTTON_UPDATE = ttk.Button(
        UPDATE_FRAME,
        text="Use this container",
        command=save_state,
        state="disabled")
    BUTTON_UPDATE.grid(column=1, row=2, sticky="SW")

    # planning/recommendation section drawn
    PLANNING_FRAME = LabelFrame(
        WINDOW,
        text="Planning what brew to make next",
        width=300,
        height=120)
    PLANNING_FRAME.grid(row=10, column=0, padx=5, pady=5, sticky="NWE")
    PLANNING_FRAME.grid_propagate(0)
    planning_algorithm()
    WINDOW.resizable(width=False, height=False)  # form is a fixed size
    WINDOW.mainloop()  # form loaded
