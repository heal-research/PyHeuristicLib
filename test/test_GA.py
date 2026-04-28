import pyheuristiclib
from pyheuristiclib.Problems.TestFunctions.SingleObjectives import AckleyFunction # type: ignore
from pyheuristiclib.Problems.TestFunctions import TestFunctionProblem # type: ignore
from pyheuristiclib.Algorithms.Evolutionary import GeneticAlgorithm # type: ignore
from pyheuristiclib.Operators.Crossovers.RealVectorCrossovers import SimulatedBinaryCrossover # type: ignore
from pyheuristiclib.Operators.Creators.RealVectorCreators import UniformDistributedCreator # type: ignore
from pyheuristiclib.Operators.Mutators.RealVectorMutators import PolynomialMutator # type: ignore
from pyheuristiclib.Genotypes.Vectors import RealVector # type: ignore
from pyheuristiclib.SearchSpaces.Vectors import RealVectorSearchSpace # type: ignore
from pyheuristiclib.Problems import IProblem # type: ignore
from pyheuristiclib.Random import RandomNumberGenerator # type: ignore
from pyheuristiclib.Algorithms.MetaAlgorithms import TerminatableAlgorithmExtensions # type: ignore
from pyheuristiclib.States import PopulationState # type: ignore
from pyheuristiclib.Algorithms import AlgorithmExtensions # type: ignore


def test_genetic_algrithm():
    p = AckleyFunction(200)
    p1 = TestFunctionProblem(p)
    creator = UniformDistributedCreator()
    cross = SimulatedBinaryCrossover()
    mut = PolynomialMutator()
    myrand = RandomNumberGenerator.Create(42)
    ga = GeneticAlgorithm.GetBuilder[RealVector, RealVectorSearchSpace, IProblem[RealVector, RealVectorSearchSpace]](creator, cross , mut)
    ga.PopulationSize = 100
    ga2 = ga.Build()
    ga3 = TerminatableAlgorithmExtensions.WithMaxIterations[RealVector, RealVectorSearchSpace, IProblem[RealVector, RealVectorSearchSpace], PopulationState[RealVector]](ga2, 1000)
    res = AlgorithmExtensions.RunToCompletion[RealVector, RealVectorSearchSpace, IProblem[RealVector, RealVectorSearchSpace], PopulationState[RealVector]](ga3, p1, myrand)
    res2 = [x.Genotype.ToString() for x in res.Population]
    assert len(res2) == 100