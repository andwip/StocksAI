# Stock Market Analysis
# Description: Using Genetic Algorithms to make predictions on whether to buy
# or short stocks.
#


from yahoo_finance import Share
import numpy
import random
import operator
import datetime

# Set the Constants ---------------
StartingDate = '2015-04-01'
PopulationSize = 200
DataSize = 0
NumberOfGenerations = 0
MutationRate = 5
MutationChange = 2
#----------------------------------

class Chromosome():
    def __init__(self, min=None, max=None, prev_min=None, prev_max=None, buy=None, score =None):
        self.min = min
        self.max = max
        self.prev_min = prev_min
        self.prev_max = prev_max
        self.buy = buy
        self.score = score

    def mutate(self):
        mu, sigma = 0, 0.15 # mean and standard deviation
        s = numpy.random.normal(mu, sigma, 1)
        x = iter(s)
        toChange = random.randint(0,5)
        if toChange == 0:
           self.buy = random.randint(0,999)%2
        if toChange == 1:
            self.min = x.next()
        if toChange == 2:
            self.max = x.next()
        if toChange == 3:
            self.prev_min = x.next()
        if toChange == 4:
            self.prev_max = x.next()
        if self.min > self.max:
            self.min, self.max = self.max, self.min
        if self.prev_min > self.prev_max:
            self.prev_min, self.prev_max = self.prev_max, self.prev_min

class TrainingData(object):
    population = []
    nextGeneration = []
    dayChange = []
    nextDayChange = []
    profit = []

    def __init__(self, stockName = '', popSize = None, mRate = None, mChange = None):
        self.stockName = stockName
        self.popSize= popSize
        self.mRate = mRate
        self.mChange= mChange

    #Generate Data from chosen stock
    def generateData(self):
        global StartingDate
        global DataSize
        i = datetime.datetime.now()
        EndingDate = '%s-%s-%s' % (i.year,i.month,i.day)
        stock = Share('AAPL')
        data = stock.get_historical(StartingDate,EndingDate)
        file = open('stock_data', 'w')
        closes = [c['Close'] for c in data]
        opens = [o['Open'] for o in data]
        oArray = []
        cArray = []

        for c in closes:
            cArray.append(c)

        for o in opens:
            oArray.append(o)

        for x in range(len(data)-2):
            #  %Difference, Next Day %Difference, Money Made Holding for a Day
            file.write(str((float(cArray[x])-float(oArray[x+1]))/100) + ' ' + str((float(cArray[x+1]) - float(oArray[x+2]))/100) + ' ' + str((float(oArray[x]) - float(oArray[x+1]))) + '\n')

            self.dayChange.append((float(cArray[x])-float(oArray[x+1]))/100)
            self.nextDayChange.append((float(cArray[x+1]) - float(oArray[x+2]))/100)
            self.profit.append(float(oArray[x]) - float(oArray[x+1]))
        #Makes sure the population size is
        DataSize = len(self.dayChange)
        file.close()

    #Initializes the population of random chromosomes
    def populationInit(self):

        #Create N Chromosomes with N being the Population Size
        #Each variable of Chromosome is assigned a number from a normal distribution
        #with the mean being 0 and the Standard Deviation being 1.5

        mu, sigma = 0, 0.15 # mean and standard deviation
        s = numpy.random.normal(mu, sigma, 4*PopulationSize)
        x = iter(s)
        for i in range(PopulationSize):
            temp = Chromosome(x.next(),x.next(),x.next(),x.next(),random.randint(0,999)%2, 0)

            #If the mininum is assigned a higher value than the max swap them
            #so that it makes sense.
            if temp.min > temp.max:
                temp.min, temp.max = temp.max, temp.min
            if temp.prev_min > temp.prev_max:
                temp.prev_min, temp.prev_max = temp.prev_max, temp.prev_min

            #Push the Chromosome into the population array.
            self.population.append(temp)

    #Determines score for each chromosome in self.population
    def fitnessFunction(self):
        for i in range(len(self.population)):
            match = False
            for j in range(DataSize):

                #print(self.population[i].min, self.nextDayChange[j], self.population[i].max)
                #If match is found we BUY
                if(self.population[i].prev_min < self.dayChange[j] and self.population[i].prev_max > self.dayChange[j]):
                    if(self.population[i].min < self.nextDayChange[j] and self.population[i].max > self.nextDayChange[j]):
                        if(self.population[i].buy == 1):
                            match = True
                            self.population[i].score += self.profit[j]

                #Match is found and we short
                if(self.population[i].prev_min < self.dayChange[j] and self.population[i].prev_max > self.dayChange[j]):
                    if(self.population[i].min < self.nextDayChange[j] and self.population[i].max > self.nextDayChange[j]):
                        if(self.population[i].buy == 0):
                            match = True
                            self.population[i].score -= self.profit[j]

                #We have not found any matches = -5000
                if match == False:
                    self.population[i].score = -5000
            #print(self.population[i].score)

    #Weighted random choice selection
    def weighted_random_choice(self):
        self.fitnessFunction()
        max = self.population[0].score
        for i in self.population[1:]:
            max+= i.score
        pick = random.uniform(0,max)
        current = 0
        for i in range(len(self.population)):
            current += self.population[i].score
            if current > pick:
                self.nextGeneration.append(self.population[i])

    #Removes the indices in self.population that have a score of None
    def exists(self):
        i = 0
        while i <len(self.population):
            if self.population[i].score is None:
                del self.population[i]
            else:
                i+=1

    #Uniform Crossover
    def uniformCross(self, z):
        children = []
        for i in range(PopulationSize-len(self.nextGeneration)):
            child = Chromosome(0,0,0,0,0)
            chromosome1 = self.nextGeneration[random.randint(0,999999) % len(self.nextGeneration)]
            chromosome2 = self.nextGeneration[random.randint(0,999999) % len(self.nextGeneration)]
            if(random.randint(0,999) %2):
                child.min = chromosome1.min
            else:
                child.min = chromosome2.min

            if(random.randint(0,999) %2):
                child.max = chromosome1.max

            else:
                child.max = chromosome2.max

            #Check to make sure the swap yields viable chromosome
            if child.max < child.min:
                    child.max, child.min = child.min, child.max

            if(random.randint(0,999) %2):
                child.prev_min = chromosome1.prev_min
            else:
                child.prev_min = chromosome2.prev_min

            if(random.randint(0,999) %2):
                child.prev_max = chromosome1.prev_max
            else:
                child.prev_max = chromosome2.prev_max

            #Check if swap is needed
            if child.prev_max < child.prev_min:
                    child.prev_max, child.prev_min = child.prev_min, child.prev_max

            if(random.randint(0,999) %2):
                child.buy = chromosome1.buy
            else:
                child.buy = chromosome2.buy

            #Append
            children.append(child)

        #Mutation
        for i in range(len(children)):
            if random.randint(0,999) % 100 <= z:
                children[i].mutate()
        self.population[i] = children[i]
        for i in range(len(children),len(self.population),1):
            self.population[i] = self.nextGeneration[i-len(children)]
        self.exists()
        self.fitnessFunction()
        self.population.sort(key=operator.attrgetter('score'))

    #Print the scores of the chromosomes
    def printChromosomes(self):
        print(len(self.population))
        for i in range(len(self.population)):
            print(self.population[i].score)

if __name__ == '__main__':
    x = TrainingData()
    x.generateData()
    x.populationInit()
    x.weighted_random_choice()
    x.uniformCross(MutationRate)
    x.printChromosomes()