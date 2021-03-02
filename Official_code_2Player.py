import numpy as np
import pandas as pd
import random
from time import sleep
import turtle


########################################################################################################################

class Planet:

    def __init__(self, name, tau, amount, distribution, distParams):
        # name of the planet
        self.name = name
        # distance (in terms of time) from the ships' planet
        self.tau = tau
        # amount of crystals on the planet
        self.amount = amount
        # distribution of crystal production 'per time step'
        self.distribution = distribution
        # parameters of the distribution (it is a dictionary)
        self.distParams = distParams

    def getName(self):
        return self.name

    def getTau(self):
        return self.tau

    def getAvailableCrystals(self):
        return self.amount

    def differenceCrystals(self, x: int):
        self.amount = self.amount - x

    def updateProduction(self):
        if self.distribution == 'normal':  # mu = 4, sigma = 2
            self.amount += round(np.random.normal(loc=self.distParams['mu'], scale=self.distParams['sigma']))
        if self.distribution == 'poisson':  # mu = 2
            self.amount += round(np.random.poisson(lam=self.distParams['mu']))
        if self.distribution == 'negative_binomial':  # mu = 20, sigma = 0.75
            self.amount += round(np.random.negative_binomial(n=self.distParams['mu'], p=self.distParams['sigma']))


########################################################################################################################

class Ship:

    def __init__(self, name, capacity, cost, strategy, planets):
        # Spacecraft's name
        self.name = name
        # Spacecraft's capacity
        self.capacity = capacity
        # Spacecraft's travelling cost per time step
        self.cost = cost
        # Amount of crystals over the spacecraft
        self.crystals = 0
        # Spacecraft's state
        self.state = 'ready'  # state can be 'ready', 'travelling' or 'operating'
        # When the spacecraft left the planet
        self.leftAt = None
        # Origin of the travel
        self.fromPlanet = None
        # Destination of the travel
        self.toPlanet = None
        # Planet selection strategy of the player
        self.strategy = strategy
        # Possible planets to collect crystals
        self.planets = planets
        # total amount of crystals
        self.totalCrystals = 100
        # useful for the 'epsilonGreedy' method
        self.destination = None
        self.crystals_mined = [0] * len(self.planets)
        self.new_list = np.arange(0, len(self.planets))
        self.mean_available_crystals_list = [0] * len(self.planets)
        # useful for the 'UCB' method
        self.mean_std_available_crystals_list = [0] * len(self.planets)
        self.crystals_seen = [[], [], []]
        self.list_of_crystals_carried = [[], [], []]
        # useful for the 'mab_tempo' method
        self.numbers_of_selections = [0] * len(self.planets)
        self.mab_crystals_list = [0] * len(self.planets)
        # useful for the 'thompson_sampling' method
        self.planets_selected = []
        self.numbers_of_selections = [0] * len(self.planets)
        # useful for the 'thompson_sampling_2' method


# TODO (just to divide the blocks):  Random strategy

    # Random strategy
    def chooseRandomPlanet(self):
        destination = np.random.randint(0, len(self.planets))
        return destination

# TODO (just to divide the blocks): functions for Epsilon-Greedy strategy

    # get the index of the planet
    def destination_name(self, destination):
        if destination == 0:
            return "Marte"
        elif destination == 1:
            return "Venere"
        else:  # 3
            return "Urano"

    # it take the rows of the ship we are working on, when were operating and on the actual destination.
    def memory_ship_df(self):
        memory_ship = game.df.loc[(game.df['Ship_name'] == self.name) & (game.df['State'] == 'operating') & (
            game.df['destination'] == self.destination_name(self.destination))]
        return memory_ship

    # it take the rows of the ship we are working on, when it was travelling (this because otherwise if in ready
    # the crystals loaded would be 0.
    def crystals_uploaded_df(self):
        crystals_uploaded = game.df.loc[(game.df['Ship_name'] == self.name) & (game.df['State'] == 'travelling')]
        return crystals_uploaded

    # updating 'crystals_mined[self.destination]' by adding the last value of 'crystals_uploaded'.
    def crystals_mined_uploading(self):
        self.crystals_mined[self.destination] += self.crystals_uploaded_df()['crystal loaded'].iloc[-1]
        return self.crystals_mined

    def mean_available_crystals_Greedy(self):
        self.mean_available_crystals_list[self.destination] = ((self.mean_available_crystals_list[self.destination]) * (
                    self.numbers_of_selections[self.destination] - 1) + (self.crystals_uploaded_df()['crystal loaded'].iloc[-1])/200) / \
                    self.numbers_of_selections[self.destination]
        print('============================================GIORGOS')
        print(self.mean_available_crystals_list)
        return self.mean_available_crystals_list

# TODO (just to divide the blocks): functions for UCB strategy

    def update_of_crystals_loaded(self):
        self.list_of_crystals_carried[self.destination].append(self.crystals_uploaded_df()['crystal loaded'].iloc[-1] / 200)
        return self.list_of_crystals_carried

    def update_crystals_seen(self):
        self.crystals_seen[self.destination].append((self.memory_ship_df()[
            f'AvailableCrystals {self.destination_name(self.destination)}'].iloc[-1] -
            self.crystals_uploaded_df()['crystal loaded'].iloc[-1] + self.crystals_mined[self.destination]))
        return self.crystals_seen

    def mean_std_available_crystals_UCB(self):
        self.mean_std_available_crystals_list[self.destination] = \
            ((self.mean_available_crystals_list[self.destination]) +
             np.std(self.list_of_crystals_carried[self.destination]))
        return self.mean_std_available_crystals_list

# TODO (just to divide the blocks): functions for mab_tempo strategy

    def round_counter(self):
        counter = (game.df.loc[(game.df['Ship_name'] == self.name) & (game.df['State'] == 'ready')].shape[0]) - 1
        return counter

    def add_planet_selected(self):
        self.numbers_of_selections[self.destination] = self.numbers_of_selections[self.destination] + 1
        return self.numbers_of_selections

    def mean_bonus(self):
        # TODO: TO ADD: self.mean_std_available_crystals_UCB()
        # application of the formula
        self.mab_crystals_list[self.destination] = self.mean_available_crystals_list[self.destination] + \
            np.sqrt((2 * np.log(self.round_counter())/self.numbers_of_selections[self.destination]))



# TODO (just to divide the blocks): functions for thompson_sampling strategy

    def choose_highest_value_old(self):
        sampled_values = [[random.sample(self.crystals_seen[0], 30)], [random.sample(self.crystals_seen[1], 30)],
                          [random.sample(self.crystals_seen[2], 30)]]
        single_list = (list(map(max, sampled_values)))
        highest_index = single_list.index(max(single_list))
        return highest_index

    def choose_highest_value(self):
        sampled_values = [[random.sample(self.list_of_crystals_carried[0], 30)],
                          [random.sample(self.list_of_crystals_carried[1], 30)],
                          [random.sample(self.list_of_crystals_carried[2], 30)]]
        mean_std_sampled_values = [[max(np.mean(sampled_values[0]), np.std(sampled_values[0]))],
                                   [max(np.mean(sampled_values[1]), np.std(sampled_values[1]))],
                                   [max(np.mean(sampled_values[2]), np.std(sampled_values[2]))]]
        highest_index = mean_std_sampled_values.index(max(mean_std_sampled_values))
        print(mean_std_sampled_values)
        return highest_index

# TODO (just to divide the blocks): functions for thompson_sampling_2 strategy

    def creation_distribution_old(self):
        # creation of a std list of all the planets
        std = [[np.std(self.crystals_seen[0])], [np.std(self.crystals_seen[1])], [np.std(self.crystals_seen[2])]]
        # creation of a distribution list of 3 lists based on distributions of mean and std of each planet.
        distribution = [np.random.normal(loc=self.mean_available_crystals_list[0], scale=std[0], size=100),
                        np.random.normal(loc=self.mean_available_crystals_list[1], scale=std[1], size=100),
                        np.random.normal(loc=self.mean_available_crystals_list[2], scale=std[2], size=100)]
        single_list = (list(map(max, distribution)))
        self.destination = single_list.index(max(single_list))
        return self.destination

    def creation_distribution(self):
        # creation of a distribution list of 3 lists based on distributions of mean and std of each planet.
        distribution = [np.random.normal(loc=np.mean(self.list_of_crystals_carried[0]),
                                         scale=np.std(self.list_of_crystals_carried[0]), size=100),
                        np.random.normal(loc=np.mean(self.list_of_crystals_carried[1]),
                                         scale=np.std(self.list_of_crystals_carried[0]), size=100),
                        np.random.normal(loc=np.mean(self.list_of_crystals_carried[2]),
                                         scale=np.std(self.list_of_crystals_carried[0]), size=100)]
        single_list = (list(map(max, distribution)))
        self.destination = single_list.index(max(single_list))
        return self.destination


# TODO (just to divide the blocks): Epsilon-Greedy strategy

    def epsilonGreedy(self):
        epsilon = 0.15
        explore = np.random.binomial(1, epsilon)
        ship_df = game.df.loc[game.df.Ship_name == self.name]

        if (('Venere' not in ship_df['destination'].values) or ('Urano' not in ship_df['destination'].values) or
            ('Home' not in ship_df['destination'].values) or ('Marte' not in ship_df['destination'].values)):
            if game.t <= 2:
                self.mean_available_crystals_list = self.mean_available_crystals_list
            else:
                self.add_planet_selected()
                self.crystals_mined_uploading()
                self.mean_available_crystals_list = self.mean_available_crystals_Greedy()
            self.destination = random.choice(self.new_list)
            self.new_list = self.new_list[self.new_list != self.destination]
            print(self.destination, 'FASE 1!', self.name, self.mean_available_crystals_list)
            return self.destination
        if explore == 1:
            self.new_list = np.arange(0, len(self.planets))
            self.add_planet_selected()
            self.crystals_mined_uploading()
            self.mean_available_crystals_list = self.mean_available_crystals_Greedy()
            self.destination = self.chooseRandomPlanet()
            print(self.destination, 'FASE 2!', self.name, self.mean_available_crystals_list)
            return self.destination
        else:  # go to the planet with the highest mean
            self.new_list = np.arange(0, len(self.planets))
            self.add_planet_selected()
            self.crystals_mined_uploading()
            self.mean_available_crystals_list = self.mean_available_crystals_Greedy()
            self.destination = max(range(len(self.mean_available_crystals_list)),
                              key=self.mean_available_crystals_list.__getitem__)
            print(self.destination, 'FASE 3!', self.name, self.mean_available_crystals_list)
            return self.destination

    # TODO (just to divide the blocks): UCB strategy

    def UCB(self):
        epsilon = 0.15
        explore = np.random.binomial(1, epsilon)
        ship_df = game.df.loc[game.df.Ship_name == self.name]

        if (('Venere' not in ship_df['destination'].values) or ('Urano' not in ship_df['destination'].values) or
            ('Home' not in ship_df['destination'].values) or ('Marte' not in ship_df['destination'].values)):
            if game.t <= 2:
                self.mean_std_available_crystals_list = self.mean_std_available_crystals_list
            else:
                self.add_planet_selected()
                self.crystals_mined_uploading()
                self.mean_available_crystals_Greedy()
                self.update_of_crystals_loaded()
                self.mean_std_available_crystals_list = self.mean_std_available_crystals_UCB()
            self.destination = random.choice(self.new_list)
            self.new_list = self.new_list[self.new_list != self.destination]
            print(self.destination, 'FASE 1!', self.name, self.mean_std_available_crystals_list)
            return self.destination
        elif explore == 1:
            self.new_list = np.arange(0, len(self.planets))
            self.add_planet_selected()
            self.crystals_mined_uploading()
            self.mean_available_crystals_Greedy()
            self.update_of_crystals_loaded()
            self.mean_std_available_crystals_list = self.mean_std_available_crystals_UCB()
            self.destination = self.chooseRandomPlanet()
            print(self.destination, 'FASE 2!', self.name, self.mean_std_available_crystals_list)
            return self.destination
        else:  # go to the planet with the highest mean
            self.new_list = np.arange(0, len(self.planets))
            self.add_planet_selected()
            self.crystals_mined_uploading()
            self.mean_available_crystals_Greedy()
            self.update_of_crystals_loaded()
            self.mean_std_available_crystals_list = self.mean_std_available_crystals_UCB()
            self.destination = max(range(len(self.mean_std_available_crystals_list)),
                              key=self.mean_std_available_crystals_list.__getitem__)
            print(self.destination, 'FASE 3!', self.name, self.mean_std_available_crystals_list)
            return self.destination

# TODO (just to divide the blocks): mab_tempo strategy

    def mab_tempo(self):
        epsilon = 0.15
        explore = np.random.binomial(1, epsilon)
        ship_df = game.df.loc[game.df.Ship_name == self.name]

        if (('Venere' not in ship_df['destination'].values) or ('Urano' not in ship_df['destination'].values) or
            ('Home' not in ship_df['destination'].values) or ('Marte' not in ship_df['destination'].values)):
            if game.t <= 2:
                self.mab_crystals_list = self.mab_crystals_list
            else:
                self.add_planet_selected()
                self.crystals_mined_uploading()
                self.mean_available_crystals_Greedy()
                self.mean_bonus()
            self.destination = random.choice(self.new_list)
            self.new_list = self.new_list[self.new_list != self.destination]
            print(self.destination, 'FASE 1!', self.name, self.mab_crystals_list)
            return self.destination
        elif explore == 1:
            self.add_planet_selected()
            self.crystals_mined_uploading()
            self.mean_available_crystals_Greedy()
            self.mean_bonus()
            self.destination = self.chooseRandomPlanet()
            print(self.destination, 'FASE 2!', self.name, self.mab_crystals_list)
            return self.destination
        else:  # go to the planet with the highest mean
            self.new_list = np.arange(0, len(self.planets))
            self.add_planet_selected()
            self.crystals_mined_uploading()
            self.mean_available_crystals_Greedy()
            self.mean_bonus()
            # destination = max value of 'mab_crystals_list'
            self.destination = max(range(len(self.mab_crystals_list)), key=self.mab_crystals_list.__getitem__)
            print(self.destination, 'FASE 3!', self.name, self.mab_crystals_list)
            return self.destination

# TODO (just to divide the blocks): thompson_sampling strategy
    def thompson_sampling(self):
        epsilon = 0.15
        explore = np.random.binomial(1, epsilon)

        if self.round_counter() <= 120:
            if game.t <= 2:
                self.list_of_crystals_carried = self.list_of_crystals_carried
            else:
                self.update_of_crystals_loaded()
            self.destination = self.chooseRandomPlanet()
            print(self.destination, 'FASE 1!', self.name)
            return self.destination
        elif explore == 1:
            self.update_of_crystals_loaded()
            self.destination = self.chooseRandomPlanet()
            print(self.destination, 'FASE 2!', self.name)
            return self.destination
        else:  # go to the planet with the highest value
            self.update_of_crystals_loaded()
            self.destination = self.choose_highest_value()
            print(self.destination, 'FASE 3!', self.name)
            return self.destination

    # TODO (just to divide the blocks): thompson_sampling_2 strategy
    def thompson_sampling_2(self):
        epsilon = 0.15
        explore = np.random.binomial(1, epsilon)

        if self.round_counter() <= 120:
            if game.t <= 2:
                self.list_of_crystals_carried = self.list_of_crystals_carried
            else:
                self.update_of_crystals_loaded()
            self.destination = self.chooseRandomPlanet()
            print(self.destination, 'FASE 1!', self.name)
            return self.destination
        elif explore == 1:
            self.update_of_crystals_loaded()
            self.destination = self.chooseRandomPlanet()
            print(self.destination, 'FASE 2!', self.name)
            return self.destination
        else:  # go to the planet with the highest value #
            self.update_of_crystals_loaded()
            self.destination = self.creation_distribution()
            print(self.destination, 'FASE 3!', self.name)
            return self.destination


    # charge full crystals (1 player)
    def fullLoad(self):
        self.crystals = min(self.capacity, self.planets[self.toPlanet].getAvailableCrystals())

    # charge half crystals (2 players)
    # TODO: GUARDA 'PROBLEMA' DESKTOP: PROBLEMA NELLA SUDDIVISIONE DEI CRISTALLI
    def shipsOnTheSamePlanet(self):
        if game.ship1.state == game.ship2.state == 'operating' and \
                game.ship1.toPlanet == game.ship2.toPlanet and \
                self.planets[game.ship1.toPlanet].getAvailableCrystals() < 2 * self.capacity:
            self.crystals = min(self.capacity, self.planets[self.toPlanet].getAvailableCrystals() / 2)
        else:  # full load crystals
            self.crystals = min(self.capacity, self.planets[self.toPlanet].getAvailableCrystals())

    # Updating spacecraft's state
    def update(self, t):

        if self.state == 'ready':
            ix = None  # To solve the warning 'Local variable 'ix' might be referenced before assignment'

            if self.strategy == 'random':
                ix = self.chooseRandomPlanet()  # selecting destination
            if self.strategy == 'epsilonGreedy':
                ix = self.epsilonGreedy()
            if self.strategy == 'UCB':
                ix = self.UCB()
            if self.strategy == 'mab_tempo':
                ix = self.mab_tempo()
            if self.strategy == 'thompson_sampling':
                ix = self.thompson_sampling()
            if self.strategy == 'thompson_sampling_2':
                ix = self.thompson_sampling_2()

            # check if there are enough chrystal to be able to leave
            if self.totalCrystals < (2 * self.planets[ix].getTau() + 2) * self.cost:
                print('Game Over!')
                game.t = game.T

            self.toPlanet = ix  # setting up the destination planet
            self.fromPlanet = -1  # setting up the origin planet ('home'==-1)
            self.totalCrystals -= (2 * self.planets[ix].getTau() + 2) * self.cost  # paying for travel
            self.state = 'travelling'  # changing the spacecraft's state
            self.leftAt = t  # setting the starting time

        elif self.state == 'travelling':
            if self.toPlanet != -1:
                if t - self.leftAt == self.planets[self.toPlanet].getTau():  # the spacecraft reached its destination
                    self.state = 'operating'
            else:
                if t - self.leftAt == self.planets[self.fromPlanet].getTau():  # the spacecraft reached its destination
                    self.state = 'operating'

        else:  # state=='operating':
            if self.toPlanet == -1:  # spacecraft is at home
                # download crystals
                self.totalCrystals += self.crystals
                self.crystals = 0
                # return in a 'ready' state
                self.toPlanet = None
                self.fromPlanet = None
                self.leftAt = None
                self.state = 'ready'
            else:
                # load crystals, considering if both spacecraft are on the same planet (for 2 players)
                self.shipsOnTheSamePlanet()
                # Full load crystals (for 1 player)
                # self.fullLoad()
                # reducing crystals from planets
                self.planets[self.toPlanet].differenceCrystals(self.crystals)
                # switch to a 'travelling' state
                self.fromPlanet = self.toPlanet
                self.toPlanet = -1
                self.leftAt = t
                self.state = 'travelling'

    def toString(self):
        string = self.name + " (" + self.state + "): "
        if self.state == 'travelling':
            if self.fromPlanet == -1:
                string += "home"
            else:
                string += self.planets[self.fromPlanet].getName()
            string += " --> "
            if self.toPlanet == -1:
                string += "home"
            else:
                string += self.planets[self.toPlanet].getName()
            string += " (left at " + str(self.leftAt) + ") - "
        string += "[" + str(self.crystals) + " crystal loaded] " + str(self.totalCrystals) + " crystals owned"
        return string

########################################################################################################################

def visualization():

    turtle.speed(0)
    turtle.delay(0)
    turtle.ht()

    #set up screen
    wn = turtle.Screen()
    wn.bgcolor('black')
    wn.title('Spacecraft_game')
    wn.bgpic('universo.gif')

    #register the shapes
    turtle.register_shape('marte.gif')
    turtle.register_shape('urano.gif')
    turtle.register_shape('venere.gif')
    turtle.register_shape('terra.gif')
    turtle.register_shape('ship1.gif')
    turtle.register_shape('ship2.gif')

    # draw the score_1
    turtle.ht()

    # Clear text
    turtle.setpos(-280, -220)
    turtle.color(turtle.bgcolor())
    turtle.begin_fill()
    turtle.fd(100)
    turtle.setheading(90)
    turtle.fd(30)
    turtle.setheading(180)
    turtle.fd(110)
    turtle.setheading(270)
    turtle.fd(30)
    turtle.setheading(0)
    turtle.fd(10)
    turtle.end_fill()
    # Write text
    turtle.color("white")


    # draw the score_2
    turtle.ht()

    # Clear text
    turtle.setpos(-280, -260)
    turtle.color(turtle.bgcolor())
    turtle.begin_fill()
    turtle.fd(100)
    turtle.setheading(90)
    turtle.fd(30)
    turtle.setheading(180)
    turtle.fd(110)
    turtle.setheading(270)
    turtle.fd(30)
    turtle.setheading(0)
    turtle.fd(10)
    turtle.end_fill()
    # Write text
    turtle.color("white")


    # create Home
    home = turtle.Turtle()
    home.color('red')
    home.shape('terra.gif')
    home.penup()
    home.speed(0)
    home.setposition(0, -250)

    # create Marte
    marte = turtle.Turtle()
    marte.color('red')
    marte.shape('marte.gif')
    marte.penup()
    marte.speed(0)
    marte.setposition(-150, 250) 

    # create Venere
    venere = turtle.Turtle()
    venere.color('red')
    venere.shape('venere.gif')
    venere.penup()
    venere.speed(0)
    venere.setposition(0, 250)

    # create Urano
    venere = turtle.Turtle()
    venere.color('red')
    venere.shape('urano.gif')
    venere.penup()
    venere.speed(0)
    venere.setposition(150, 250)

########################################################################################################################


class Game:

    def __init__(self, T):
        self.df = pd.DataFrame(dtype=float)
        # Initial time for the game
        self.t = 1
        # Max time for the game
        self.T = T
# TODO: NORMAL #########################################################################################################
        # Creation of the planets
        #self.planets = [Planet('Marte', 1, 10, 'normal', {'mu': 9, 'sigma': 2}),
        #                Planet('Venere', 2, 10, 'normal', {'mu': 11, 'sigma': 3}),
        #                Planet('Urano', 3, 10, 'normal', {'mu': 12, 'sigma': 4})]
        ## Creation of the first spacecraft (aka ship)
        #self.ship1 = Ship('Enterprise', 200, 1, 'epsilonGreedy', self.planets)
        ## Creation of the second spacecraft (aka ship)
        #self.ship2 = Ship('Millennium Falcon', 200, 1, 'epsilonGreedy', self.planets)
# TODO: DIFFERENT ######################################################################################################
        # Creation of the planets
        self.planets = [Planet('Marte', 1, 10, 'normal', {'mu': 11, 'sigma': 3}),
                        Planet('Venere', 2, 10, 'poisson', {'mu': 11}),
                        Planet('Urano', 3, 10, 'negative_binomial', {'mu': 35, 'sigma': 0.75})]
        # Creation of the first spacecraft (aka ship)
        self.ship1 = Ship('Enterprise', 200, 1, 'epsilonGreedy', self.planets)
        # Creation of the second spacecraft (aka ship)
        self.ship2 = Ship('Millennium Falcon', 200, 1, 'epsilonGreedy', self.planets)
# TODO: ################################################################################################################

    def nextStep(self):
        self.ship1.update(self.t)  # updating the first spacecraft
        self.ship2.update(self.t)  # updating the second spacecraft
        for planet in self.planets:  # updating the crystals on the planets based to their own production distributions
            planet.updateProduction()
        self.t += 1  # increasing time

    def run_game(self):

        # visualization
        visualization()

        # create the Ship1
        ship1 = turtle.Turtle()
        ship1.color('blue')
        ship1.shape('ship1.gif')
        ship1.penup()
        ship1.speed(0)
        ship1.setheading(90)

        # create the Ship2
        ship2 = turtle.Turtle()
        ship2.color('green')
        ship2.shape('ship2.gif')
        ship2.penup()
        ship2.speed(0)
        ship2.setheading(90)

        random.seed(42)
        while self.t <= self.T:  # main loop
            self.printGameState()
            if game.ship1.state == 'ready':
                ship1.setposition(-15, -190)
            if game.ship1.state == 'operating' and game.ship1.toPlanet == -1:
                ship1.setposition(-15, -190)
            if game.ship1.state == 'travelling' and game.ship1.toPlanet == 0:
                ship1.setposition(-85, 0)
            if game.ship1.state == 'travelling' and game.ship1.fromPlanet == 0 and game.ship1.toPlanet == -1:
                ship1.setposition(-85, 0)
            if game.ship1.state == 'travelling' and game.ship1.toPlanet == 1:
                ship1.setposition(-15, 0)
            if game.ship1.state == 'travelling' and game.ship1.fromPlanet == 1 and game.ship1.toPlanet == -1:
                ship1.setposition(-15, 0)
            if game.ship1.state == 'travelling' and game.ship1.toPlanet == 2:
                ship1.setposition(85, 0)
            if game.ship1.state == 'travelling' and game.ship1.fromPlanet == 2 and game.ship1.toPlanet == -1:
                ship1.setposition(85, 0)
            if game.ship1.state == 'operating' and game.ship1.toPlanet == 0:
                ship1.setposition(-135, 190)
            if game.ship1.state == 'operating' and game.ship1.toPlanet == 1:
                ship1.setposition(-15, 190)
            if game.ship1.state == 'operating' and game.ship1.toPlanet == 2:
                ship1.setposition(135, 190)
            if game.ship2.state == 'ready':
                ship2.setposition(15, -190)
            if game.ship2.state == 'operating' and game.ship2.toPlanet == -1:
                ship2.setposition(15, -190)
            if game.ship2.state == 'travelling' and game.ship2.toPlanet == 0:
                ship2.setposition(-125, 0)
            if game.ship2.state == 'travelling' and game.ship2.fromPlanet == 0 and game.ship2.toPlanet == -1:
                ship2.setposition(-125, 0)
            if game.ship2.state == 'travelling' and game.ship2.toPlanet == 1:
                ship2.setposition(15, 0)
            if game.ship2.state == 'travelling' and game.ship2.fromPlanet == 1 and game.ship2.toPlanet == -1:
                ship2.setposition(15, 0)
            if game.ship2.state == 'travelling' and game.ship2.toPlanet == 2:
                ship2.setposition(125, 0)
            if game.ship2.state == 'travelling' and game.ship2.fromPlanet == 2 and game.ship2.toPlanet == -1:
                ship2.setposition(125, 0)
            if game.ship2.state == 'operating' and game.ship2.toPlanet == 0:
                ship2.setposition(-165, 190)
            if game.ship2.state == 'operating' and game.ship2.toPlanet == 1:
                ship2.setposition(15, 190)
            if game.ship2.state == 'operating' and game.ship2.toPlanet == 2:
                ship2.setposition(165, 190)
            turtle.clear()
            text_result2 = str(game.ship2.totalCrystals)
            turtle.setpos(-280, -260)
            #turtle.pendown()
            turtle.write('Ship2: '+ text_result2, False, align='left', font=('arial', 14, 'normal'))
            turtle.penup()
            text_result1 = str(game.ship1.totalCrystals)
            turtle.setpos(-280, -240)
            turtle.pendown()
            turtle.write('Ship1: '+ text_result1, False, align='left', font=('arial', 14, 'normal'))
            turtle.penup()
            self.nextStep()
            sleep(1)


    def printGameState(self):
        print("t=" + str(self.t))
        for planet in self.planets:
            print(planet.getName() + ": " + str(planet.getAvailableCrystals()) + " crystals [distant " + str(
                planet.getTau()) + "]")
        print(self.ship1.toString())
        print(self.ship2.toString() + "\n")
        self.final_df(self.ship1)
        self.final_df(self.ship2)

    # creation of final df

    def final_df(self, Ship):

        def destination():
            if Ship.toPlanet == None:
                return "Home"
            elif Ship.toPlanet == -1:
                return "Home"
            elif Ship.toPlanet == 0:
                return "Marte"
            elif Ship.toPlanet == 1:
                return "Venere"
            else:  # Ship.toPlanet == 2:
                return "Urano"

        available_crystals = [self.planets[0].getAvailableCrystals(),
                              self.planets[1].getAvailableCrystals(),
                              self.planets[2].getAvailableCrystals()]

        data = dict(zip(('t',
                         'Ship_name', 'State', 'destination', 'AvailableCrystals',
                         'AvailableCrystals Marte', 'AvailableCrystals Venere', 'AvailableCrystals Urano',
                         'crystal loaded', 'crystals owned'),
                        (self.t, Ship.name, Ship.state, destination(), available_crystals,
                         self.planets[0].getAvailableCrystals(),
                         self.planets[1].getAvailableCrystals(),
                         self.planets[2].getAvailableCrystals(),
                         Ship.crystals, Ship.totalCrystals
                         )))

        data = pd.DataFrame(data.items())
        data = data.transpose()
        data.columns = data.iloc[0]
        data = data.drop(data.index[[0]])
        game.df = game.df.append(data)
        return ()


########################################################################################################################
game = Game(10000)
game.run_game()

#writer = pd.ExcelWriter(
#    'C:/Users/davla/Desktop/output_per_prof/mab_tempo/1Player_42_gauss_poisson_NegativeBinomial_EpsilonGreedy_MeanStrategy.xlsx')
#game.df.to_excel(writer, 'Sheet1', index=False)
#writer.save()
