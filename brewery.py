"""
This module handles the information required to track brewing processes
for each batch in production, as well as the states of each batch and
the equipment.
"""
import json
from datetime import datetime, timedelta


def read_data(type: str = "") -> dict:
    """
    Reads container and inventory data into a list of dictionaries

    Arguments:
    type - The category of data to be fetched from the JSON file.
    """
    try:
        with open('config.json', 'r') as f:  # all json file data is loaded
            data = json.load(f)
    except BaseException:
        logging.error("FATAL ERROR: config.json file missing")
        return
    if type == "containers":  # only container data is returned
        return data["containers"]
    elif type == "inventory":  # only inventory data is returned
        return data["inventory"]
    else:
        return data


def get_possible_containers(
        volume: int,
        fermenter: bool,
        conditioner: bool,
        batch: dict) -> dict:
    """
    Returns all the possible containers a batch can go into

    This function searches a list of all containers and returns a dictionary
    of all possible tanks that a batch can go into, based on its volume,
    availability of other tanks, whether a tank has the right capabilities,
    and whether or not the batch is already in a tank.

    Arguments:
    volume - the volume of the batch to be added
    fermenter - boolean value indicating if the tank needs to ferment
    conditioner - boolean indicating if the tank needs to be a conditioner
    batch - dictionary containing the current batch data
    """
    possible_containers = {}
    containers = read_data("containers")  # container data read in
    for container, data in containers.items():
        if (data["fermenter"] == fermenter or data["conditioner"]
                == conditioner) and data["volume"] >= volume:
            if data["occupied"] == False:  # if criteria for possible container met
                possible_containers[container] = data  # container added
            else:
                if data['id'] == batch['id']:
                    if data['conditioner']:
                        if batch['state'] == 'fermentation':
                            # batches can use the container they are in
                            possible_containers[container] = {
                                'state': "Can be used again by this batch"}
    for container, data in possible_containers.items():
        for attribute, value in data.items():
            if attribute in ("volume", "fermenter", "conditioner", "state"):
                output = value
                if value or value == False:
                    output = ("No", "Yes")[value]  # False/True converted
    return possible_containers  # list of possible containers returned


def get_batch_data(batch_to_edit: str) -> dict:
    """Takes a gyle number for a batch and returns the batch data"""
    data = read_data()
    for batch, batchdata in data['inventory'].items():
        if batch == batch_to_edit:  # batch found from file
            current_batch = batchdata
    return current_batch  # batch data return


def get_production_batches() -> list:
    """
    Returns a list of strings containing information about all batches

    This function reads in every batch in production from a JSON file,
    and constructs a string containing the recipe, gyle number,
    container (if applicable), the state time remaining, and volume of#
    the batch in production.
    This string is later printed to the form in a list of production
    batches.
    """
    strings = []
    data = read_data()
    for batch, batchdata in data['inventory'].items():
        time_remaining = "Less than 5 hours"
        if batchdata['id'] != -1:  # if batch is in production
            batch_container = None
            for container, info in data['containers'].items():
                if batchdata['id'] == info['id']:  # if batch in container
                    batch_container = container
                    time_remaining = calculate_time(info)
            if batchdata['id'] == 10:  # if batch is in bottling phase
                time_remaining = "Less than 12 hours"  # bottling time
            strings.append(
                "Recipe: %s\nGyle Number: %s\nContainer: %s\nState: %s\nTime Remaining: %s\nVolume: %d litres\n" %
                (batchdata['recipe'],
                 batch,
                 batch_container,
                 batchdata['state'],
                    time_remaining,
                    batchdata['volume']))
    return strings


def update_containers(
        batchdata: dict,
        finish_time: str,
        state: str,
        selection: str) -> None:
    """
    Updates the state of batches and containers and writes them to the file

    When a batch is moved to a new tank this subroutine updates the states
    of the batch and the containers and writes the new states to the file.

    Arguments:
    batchdata - dictionary which contains data about the batch
    finish_time - string which contains the date on which the stage finishes
    state - the state in which the batch is being moved into
    selection - the container which the user has selected
    """
    data = read_data()
    if batchdata['id'] > 0:
        for container, values in data['containers'].items():
            if values['id'] == batchdata['id']:
                values['occupied'] = False
                values['finish'] = "-1"
    if selection == "bottling":
        batchdata['id'] = 10
    batchdata['state'] = state
    for container, values in data['containers'].items():
        if container == selection:
            values['occupied'] = True
            values['finish'] = finish_time
            batchdata['id'] = values['id']
    batch = {str(batchdata['gyle']): batchdata}
    data['inventory'].update(batch)
    with open("config.json", "w") as f:
        json.dump(data, f)


def calculate_time(info: dict) -> str:
    """
    Calculates the remaining time of the batch process and returns a string

    Arguments:
    info - dictionary containing the batch information
    """
    time = info['finish']
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    a = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
    b = datetime.strptime(time, "%Y-%m-%d")
    difference = b - a
    time_string = ""
    if difference.seconds >= 1:
        time_string += ("%d days " % difference.days)
        time_string += ("%d hours " % (difference.seconds // 3600))
        time_string += ("%d minutes " % ((difference.seconds // 60) % 60))
    else:
        time_string += ("Finished")
    return time_string


def delete_batch(batch: int) -> None:
    """
    Removes a batch from the system

    Arguments:
    batch - the gyle number of the batch to be removed
    """
    data = read_data()
    for id, batches in data['inventory'].items():
        if id == str(batch):
            batchdata = batches
    for container, values in data['containers'].items():
        if values['id'] == batchdata['id']:
            values['occupied'] = False
            values['finish'] = "-1"
    data['inventory'].pop(str(batch))
    with open("config.json", "w") as f:
        json.dump(data, f)


def add_batch_to_inventory(batch: dict) -> None:
    """Adds a batch to the inventory"""
    batch['id'] = -1
    batch['state'] = "bottled"
    batch_to_update = {str(batch['gyle']): batch}
    add_brew(batch_to_update)


def calculate_finish_time(fermenting: bool) -> str:
    """
    Calculates the expected finish time of the production stage

    Arguments:
    fermenting - boolean which indicates if the stage is fermentation
    """
    today = datetime.today().strftime('%Y-%m-%d')
    today_date = datetime.strptime(today, '%Y-%m-%d')
    if fermenting:
        process_time = timedelta(days=28)
    elif fermenting == False:
        process_time = timedelta(days=14)
    finish = today_date + process_time
    finish_time = datetime.strftime(finish, '%Y-%m-%d')
    return finish_time


def check_equipment_availability() -> bool:
    """
    Checks if any containers are available

    Arguments:
    volume - the volume of the batch that needs to fit in the tanks
    """
    possible_containers = {}
    data = read_data()
    for container, value in data['containers'].items():
        if (value["fermenter"]):
            if not value["occupied"]:
                possible_containers[container] = data
    if possible_containers:
        return True
    else:
        return False


def get_container(container_to_get: str) -> dict:
    """
    Takes a container name and returns information about that container

    This function returns the useful information about a specific container
    when the user selects the container from a list of containers,
    and returns the information in a dictionary in a comprehensive form.

    Arguments:
    container_to_get - the container whose information should be fetched.
    """
    data = read_data()
    for container, value in data['containers'].items():
        if container == container_to_get.lower():
            container_data = {}
            container_data['name'] = container
            recipe = ""
            if value['occupied']:
                container_data['status'] = "In Use"
                for id, brew in data['inventory'].items():
                    if brew['id'] == value['id']:
                        container_data['recipe'] = brew['recipe']
            else:
                container_data['status'] = "Available"
            for attribute, info in value.items():
                if attribute in (
                    "volume",
                    "fermenter",
                    "conditioner",
                        "state"):
                    output = info
                    if info in (False, True):
                        output = ("No", "Yes")[info]
                    container_data[str(attribute).capitalize()] = str(output)
    return container_data


def add_brew(batch: dict) -> None:
    """Adds a new batch to the system"""
    data = read_data()
    data['inventory'].update(batch)
    with open("config.json", "w") as f:
        json.dump(data, f)


def bottled_beers() -> dict:
    """
    Calculates the number of bottled beers from the finished batches

    This function calculates the number of bottles of each beer in the
    inventory by dividing the volume (in litres) by 0.5 (as each bottle
    is 500ml, half a litre). The function returns a dictionary with the
    beer counts.
    """
    data = read_data('inventory')
    beers = {
        'Organic Red Helles': 0,
        'Organic Dunkel': 0,
        'Organic Pilsner': 0}
    for id, beer in data.items():
        if beer['id'] == -1:
            bottles = beer['volume'] // 0.5
            beers[beer['recipe']] += bottles
    return beers
