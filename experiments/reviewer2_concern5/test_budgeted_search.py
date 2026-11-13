import itertools
import unittest
import numpy as np
from budgeted_search import best_feasible_triple


class BudgetSearchTests(unittest.TestCase):
    def test_matches_brute_force_and_can_drop_first_two(self):
        scores=np.array([.99,.98,.97,.96,.95,.94]);cost=np.array([100,100,15,15,15,15])
        acceptable=lambda ids:sum(cost[i] for i in ids)<=50
        got,proof=best_feasible_triple(scores,range(6),range(6),range(6),acceptable)
        brute=max((ids for ids in itertools.combinations(range(6),3) if acceptable(ids)),key=lambda ids:sum(scores[list(ids)]))
        self.assertEqual(got,list(brute));self.assertEqual(got,[2,3,4]);self.assertTrue(proof['best_first_certificate'])

    def test_nonadditive_feasibility_distinct_documents_and_ties(self):
        scores=[.9,.9,.8,.7,.6];rows=[10,2,3,4,5];docs=['a','a','b','c','d']
        feasible=lambda ids:set(ids) in ({0,2,4},{1,2,3})
        got,_=best_feasible_triple(scores,rows,docs,range(5),feasible)
        self.assertEqual(got,[1,2,3])

    def test_limit_fails_without_short_example_fallback(self):
        with self.assertRaises(RuntimeError):
            best_feasible_triple([.9,.8,.7,.6],range(4),range(4),range(4),lambda ids:False,max_checks=1)


if __name__=='__main__':unittest.main()
