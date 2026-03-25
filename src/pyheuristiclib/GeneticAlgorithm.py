from HeuristicLib.Algorithms import GeneticAlgorithm as CsGeneticAlgorithm
from HeuristicLib.Problems import TspProblem as CsTspProblem
from . import InteroptUtil

def _callbackWrapper(generationCallback):
    return lambda generation, bestTour, bestDistance: generationCallback(generation,InteroptUtil.csArrayToNumpy(bestTour),bestDistance)
class GeneticAlgorithm:
    def __init__(self, matrix, populationSize = 100,  mutationRate = 0.05, generations = 1000, generationCallback = None):
        cs_matrix = InteroptUtil.numpyToCsArray(np_array=matrix)
        self._problem = CsTspProblem(cs_matrix)

        if generationCallback:
           cs_callback = CsGeneticAlgorithm.GenerationCallback(_callbackWrapper(generationCallback))
           self._ga = CsGeneticAlgorithm(self._problem, populationSize, mutationRate, generations,cs_callback)
        else:
            self._ga = CsGeneticAlgorithm(self._problem, populationSize, mutationRate, generations)



    def run(self):
        res = self._ga.Run()

        return (InteroptUtil.csArrayToNumpy(res.Item1),res.Item2)