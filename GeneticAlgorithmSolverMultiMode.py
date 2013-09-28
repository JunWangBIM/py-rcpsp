'''
Created on 17 Aug 2013

@author: Aleksandra
'''
from GeneticAlgorithmSolver import SerialScheduleGenerationSchemeGenerator, crossover_sgs, crossover_sgs_nonrandom
from MultiModeClasses import Solution
from deap import base, creator, tools, algorithms
from random import randint, random, choice
from copy import copy

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

class MultiModeSgsMaker(object):
    def __init__(self, problem, retries):
        self.problem = problem
        self.retries = retries
        self.generator = SerialScheduleGenerationSchemeGenerator(problem)

    def generate_random_sgs(self):
        sgs = self.generator.generate_random_sgs()
        modes = self.generate_modes(sgs)

        return zip(sgs, modes)

    def generate_modes(self, sgs):
        modes =[choice(activity.mode_list) for activity in sgs]
        for _i in xrange(self.retries):
            temp_solution = Solution.makeSolution(sgs, modes)
            if self.problem.check_nonrenewable_resources(temp_solution):
                return modes
            else:
                self.modify_mode(sgs, modes)
        return modes

    def modify_mode(self, activities, modes):
        multimode_activities = \
        [(i,a) for (i,a) in enumerate(activities) if len(a.mode_list) > 1]
        index_to_improve, activity = choice(multimode_activities)
        wrong_mode = modes[index_to_improve]
        new_mode = choice([mode for mode in activity.mode_list if mode is not wrong_mode])
        modes[index_to_improve] = new_mode

class GeneticAlgorithmSolver(object):
    # n= 300 ; cxpb = 0.5 ; mutpb = 0.2 ; ngen = 40
    def __init__(self, problem, size_of_population = 300, crossover_probability = 0.5, mutation_probability = 0.2, number_of_generations = 40, retries_for_generation = 4):
        self.size_of_population = size_of_population
        self.crossover_probability = crossover_probability
        self.mutation_probability = mutation_probability
        self.number_of_generations = number_of_generations
        self.generator = MultiModeSgsMaker(problem, retries_for_generation)
        self.problem = problem

    def generate_toolbox_for_problem(self):
        toolbox = base.Toolbox()
        toolbox.register("individual", lambda: creator.Individual(self.generator.generate_random_sgs()))
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("evaluate", self.evaluate_sgs)
        toolbox.register("mate", crossover_sgs)
        toolbox.register("mutate", self.mutate_sgs, prob=0.05)
        toolbox.register("select", tools.selTournament, tournsize=3)
        toolbox.register("clone", copy)
        
        return toolbox
     
    def solve(self):    
        toolbox = self.generate_toolbox_for_problem()
        population = toolbox.population(n = self.size_of_population)
        algorithms.eaSimple(population, toolbox, cxpb = self.crossover_probability , mutpb = self.mutation_probability, ngen = self.number_of_generations, verbose=False)
        return Solution.generate_solution_from_serial_schedule_generation_scheme(tools.selBest(population, 1)[0], self.problem)
    
    def evaluate_sgs(self, sgs):
        solution = Solution.generate_solution_from_serial_schedule_generation_scheme(sgs, self.problem)
        return (self.problem.compute_makespan(solution),)
        
    def mutate_sgs(self, sgs, prob = 0.05):
        new_sgs = sgs
        for i in xrange(len(new_sgs) - 1):
            copy_of_sgs = copy(new_sgs)
            if random() < prob:
                copy_of_sgs[i] = new_sgs[i+1]
                copy_of_sgs[i+1] = new_sgs[i]
            if self.problem.is_valid_sgs(copy_of_sgs):
                new_sgs = copy_of_sgs
        return (new_sgs,)
                
