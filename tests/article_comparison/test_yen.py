"""
Luh Yen: Graph Nodes Clustering based on the Commute-Time Kernel
https://pdfs.semanticscholar.org/1206/63cc9644efbd4a4f92f6dc3d83b78e11791f.pdf
"""

import logging
import unittest

import numpy as np
from sklearn.metrics import adjusted_rand_score

from pygkernels import util
from pygkernels.cluster import KKMeans
from pygkernels.data import Datasets
from pygkernels.measure import SCT_H
from pygkernels.score import rand_index


# Luh Yen: Graph Nodes Clustering based on the Commute-Time Kernel
# https://www.isys.ucl.ac.be/staff/marco/Publications/2007_GraphNodesClustering.pdf
class Table1Tests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        util.configure_logging()
        self.etalon = {  # SCT RI, SCT ARI
            'news_2cl1': (.975, .95),
            'news_2cl2': (.906, .83),
            'news_2cl3': (.955, .91),
            'news_3cl1': (.939, .91),
            'news_3cl2': (.936, .91),
            'news_3cl3': (.939, .91),
            'news_5cl1': (.830, .80),
            'news_5cl2': (.748, .77),
            'news_5cl3': (.764, .75)
        }
        self.datasets = Datasets()

    def _newsgroup_results(self, name, scorer_func, result_idx, atol=0.1):
        results = []
        for (A, gt), info in [
            self.datasets['news_2cl1'], self.datasets['news_2cl2'], self.datasets['news_2cl3'],
            # self.datasets['news_3cl1'], self.datasets['news_3cl2'], self.datasets['news_3cl3'],
            # self.datasets['news_5cl1'], self.datasets['news_5cl2'], self.datasets['news_5cl3']
        ]:
            K = SCT_H(A).get_K(22)
            true_nmi = self.etalon[info['name']][result_idx]

            y_pred = KKMeans(n_clusters=info['k'], n_init=30, device='cpu').predict(K, A=A)
            test_nmi = scorer_func(gt, y_pred)
            diff = np.abs(test_nmi - true_nmi)

            logging.info('measure\tgraph\ttest nmi\ttrue nmi\tdiff')
            logging.info(f'{name}\t{info["name"]}\t{test_nmi:.3f}\t{true_nmi:.3f}\t{diff:.3f}')

            results.append({
                'measure_name': name,
                'graph_name': info['name'],
                'test_nmi': test_nmi,
                'true_nmi': true_nmi,
                'diff': diff
            })

        for result in results:
            self.assertTrue(result['test_nmi'] + atol > result['true_nmi'],
                            f'{result["graph_name"]}, {result["measure_name"]}: '
                            f'ours:{result["test_nmi"]:.3f} != gt:{result["true_nmi"]:.3f}, diff={result["diff"]:.3f}')

    def test_SCT_RI(self):
        self._newsgroup_results('SCT RI', rand_index, 0)

    @unittest.skip
    def test_SCT_ARI(self):
        self._newsgroup_results('SCT ARI', adjusted_rand_score, 1)


if __name__ == "__main__":
    unittest.main()
