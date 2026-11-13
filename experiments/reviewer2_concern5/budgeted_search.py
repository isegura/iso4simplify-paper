"""Best-first search of three-document sets by sum of source-similarity scores."""
import heapq
import numpy as np


def best_feasible_triple(scores, training_rows, document_ids, source_keys, feasible,
                         eligible=None, max_checks=5000):
    scores=np.asarray(scores,dtype=np.float64)
    if not np.isfinite(scores).all():raise ValueError('Nonfinite similarities')
    if eligible is None:eligible=range(len(scores))
    order=sorted(eligible,key=lambda i:(-scores[i],int(training_rows[i])))
    if len(order)<3:raise ValueError('Fewer than three candidates')
    def priority(ranks):return -float(sum(scores[order[i]] for i in ranks))
    queue=[(priority((0,1,2)),(0,1,2))];seen={(0,1,2)};checked=0;popped=0
    while queue:
        objective,ranks=heapq.heappop(queue);popped+=1
        ids=[order[i] for i in ranks]
        distinct=len({document_ids[i] for i in ids})==3 and len({source_keys[i] for i in ids})==3
        if distinct:
            if checked>=max_checks:
                raise RuntimeError('Search limit reached before finding a feasible triple; no fallback or false optimality claim.')
            checked+=1
            if feasible(ids):
                return ids,dict(mean_cosine=-objective/3,ranks=[i+1 for i in ranks],
                    checked=checked,popped=popped,best_first_certificate=True,
                    next_frontier_mean_bound=(-queue[0][0]/3 if queue else None))
        for pos in range(3):
            child=list(ranks);child[pos]+=1
            if child[2]>=len(order) or not child[0]<child[1]<child[2]:continue
            child=tuple(child)
            if child not in seen:
                seen.add(child);heapq.heappush(queue,(priority(child),child))
    raise ValueError('No feasible distinct three-document set in the eligible pool')
