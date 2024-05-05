import math
from dataclasses import dataclass


@dataclass
class Pf2eElement:
    name: str
    level: int = 0
    cost: float = 0.0
    rarity: int = 0
    quantity: int = 1


@dataclass
class EttGamePlayer:
    player_name: str
    name: str
    gained_karma: int


STARTING_GOLD = 15.0
XP_PER_LEVEL = 12
STARTING_SLOTS = 5
STARTING_KARMA = 1
NEW_FACE_BASE_COST = 5
NEW_FACE_COST_PER = 1
NEW_FACE_FIXED_COST = True
# for karma - name = name, level = cost (sorry),
# rarity = 0 -> instant consumable, 1 -> character, 2 -> player
KARMA_REWARDS = [Pf2eElement("Mini Rework", 1), Pf2eElement("Full Rework", 3),
                 Pf2eElement("Return Policy (Specify cost as quantity)", 1),
                 Pf2eElement("Look What I Found", 4), Pf2eElement("Personal Staff", 5, rarity = 1),
                 Pf2eElement("PS Uncommon Spell", 2, rarity = 1), Pf2eElement("PS Rare Spell", 4, rarity = 1),
                 Pf2eElement("Skeleton Key", level=5, rarity=1), Pf2eElement("No Interest Loan", 10),
                 Pf2eElement("New Face", level=5, rarity=2),
                 Pf2eElement("Family Heirloom", level=10, rarity=1),
                 Pf2eElement("Upgrade Please", level=10, rarity=1)
                 ]


def get_new_face_karma_cost(new_face: Pf2eElement, upgrades: str):
    upgrades_elements = string_to_pf2e_element_list(upgrades)
    new_faces = 0
    for i in upgrades_elements:
        if i.name == "New Face":
            new_faces += i.quantity
            break
    # New Face now has fixed cost
    if NEW_FACE_FIXED_COST:
        return new_face.quantity * NEW_FACE_BASE_COST
    # Karma to buy the first newface
    start_cost = NEW_FACE_BASE_COST + (new_faces * NEW_FACE_COST_PER)
    # Karma to buy the one after the last newface
    end_cost = start_cost + (new_face.quantity * NEW_FACE_COST_PER)
    return sum(range(start_cost, end_cost, NEW_FACE_COST_PER))


def get_available_slots(upgrades: str, characters: list):
    upgrades_elements = string_to_pf2e_element_list(upgrades)
    new_faces = 0
    for i in upgrades_elements:
        if i.name == "New Face":
            new_faces += i.quantity
            break
    return STARTING_SLOTS + new_faces - len(characters)


def get_ultimate_tt(upgrades: str):
    upgrades_elements = string_to_pf2e_element_list(upgrades)
    true_tt = False
    for i in upgrades_elements:
        if i.name == "True Time Traveler" and i.quantity > 0:
            true_tt = True
    return true_tt


def get_level(xp):
    lv = 1 + math.floor(xp / XP_PER_LEVEL)
    if lv > 20:
        lv = 20
    return lv


# June Bonus XP
XP_MULTIPLIER = 1


def ett_xp_rate(player_level, party_level):

    # GMs get 1.5x xp regardless. GM "Players" have a level of 0
    if player_level == 0:
        return 1.5 * XP_MULTIPLIER

    # example: party level = 3, player level = 5. party - player = -2
    # 2 ** (-2 /2) = 2 ** -1 = 0.5
    # Example 2: party level = 3, player level = 2. party - player = 1
    # 2 ** (1/2) ~= 1.4
    # All of the XP calculations follow this format
    # But should be rounded to 1 decimal
    print("party level and player level are ", party_level, player_level)
    level_diff = party_level - player_level
    if level_diff < -3:
        level_diff = -3
    if level_diff > 3:
        level_diff = 3
    return round(2 ** (level_diff / 2), 1) * XP_MULTIPLIER


# This does three things. 1. it removes any NON RARE unlocks at or below the PC level
# 2. it appends any NEW unlocks to the list if applicable.
# 3. it removes any items from the remove_unlocks list
def ett_parse_unlocks(cur_unlocks: list[Pf2eElement], new: list[Pf2eElement], remove: list[Pf2eElement]):
    # Remove non rare unlocks at or below the PC level
    items = []
    for i in cur_unlocks:
        items += [i]

    for i in new:
        # Do not add redundant items that do not need unlocking
        exists = False
        for j in items:
            if j.name == i.name:
                exists = True
                break
        if not exists:
            items += [i]

    # Remove any items to remove with this disgustingly inefficient loop.
    items2 = []
    for j in items:
        keep_item = True
        for i in remove:
            if i.name == j.name:
                keep_item = False
        if keep_item:
            items2 += [j]
    return items2


def pf2e_element_list_to_string(elements: list[Pf2eElement]):
    output_str = ''
    for element_index in range(len(elements)):
        i = elements[element_index]
        output_str += i.name + "|" + str(i.level) + "|" + str(i.cost) + "|" + str(i.rarity) + "|" + str(i.quantity)
        if element_index < (len(elements) - 1):
            output_str += "\n"
    return output_str


def string_to_pf2e_element_list(elements: str):
    if not elements:
        return []
    e_str = elements.splitlines(False)
    element_list = []
    for line in e_str:
        a = line.split("|")
        element_list.append(Pf2eElement(a[0], int(a[1]), float(a[2]), int(a[3]), int(a[4])))
    return element_list
