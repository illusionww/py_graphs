from abc import ABC, abstractmethod

import numpy as np

from pygraphs.cluster import _kmeans_numpy, _kmeans_pytorch
from pygraphs.cluster.base import KernelEstimator


class KMeans_Fouss(KernelEstimator, ABC):
    def __init__(self, n_clusters, n_init=15, max_rerun=100, max_iter=100, init='any', random_state=None,
                 backend='pytorch', device='cuda:0'):
        super().__init__(n_clusters, device=device, random_state=random_state)

        self.init_names = ['one', 'all', 'k-means++']
        self.eps = 10 ** -10

        self.n_init = n_init
        self.max_rerun = max_rerun
        self.max_iter = max_iter
        self.init = init

        if backend == 'numpy':
            self.backend = _kmeans_numpy
        elif backend == 'pytorch':
            self.backend = _kmeans_pytorch

    def fit(self, K, y=None, sample_weight=None):
        self.labels_ = self.predict(K)
        return self

    def _init_simple(self, K, init):
        n = K.shape[0]
        q_idx = np.arange(n)
        np.random.shuffle(q_idx)

        h = np.zeros((self.n_clusters, n), dtype=np.float64)
        if init == 'one':  # one: choose one node for each cluster
            for i in range(self.n_clusters):
                h[i, q_idx[i]] = 1.
        elif init == 'all':  # all: choose (almost) all nodes to clusters
            nodes_per_cluster = n // self.n_clusters
            for i in range(self.n_clusters):
                for j in range(i * nodes_per_cluster, (i + 1) * nodes_per_cluster):
                    h[i, q_idx[j]] = 1. / nodes_per_cluster
        else:
            raise NotImplementedError()
        return h

    def _init_h(self, K: np.array):
        init = np.random.choice(self.init_names) if self.init == 'any' else self.init
        if init in ['one', 'all']:
            h = self._init_simple(K, init='one')
        elif init == 'k-means++':
            h = self.backend.kmeanspp(K, self.n_clusters, device=self.device)
        else:
            raise NotImplementedError()
        return h

    def _predict_successful_once(self, K: np.array):
        for i in range(self.max_rerun):
            K = K.astype(np.float64)
            labels, inertia, success = self._predict_once(K)
            if success:
                return labels, inertia
        # print('reruns exceeded, take last result')
        return labels, inertia

    @abstractmethod
    def _predict_once(self, K: np.array):
        pass

    def predict(self, K):
        np.random.seed(self.random_state)
        best_labels, best_inertia = [], np.inf
        for i in range(self.n_init):
            labels, inertia = self._predict_successful_once(K)
            if inertia < best_inertia or len(best_labels) == 0:
                best_labels = labels

        return best_labels


class KKMeans_vanilla(KMeans_Fouss):
    """Kernel K-means clustering
    Reference
    ---------
    Francois Fouss, Marco Saerens, Masashi Shimbo
    Algorithms and Models for Network Data and Link Analysis
    Algorithm 7.2: Simple kernel k-means clustering of nodes
    """

    name = 'KKMeans'

    def _predict_once(self, K: np.array):
        h_init = self._init_h(K)
        result = self.backend.vanilla_predict(K, h_init, self.max_iter, device=self.device)
        return result


class KKMeans_iterative(KMeans_Fouss):
    """Kernel K-means clustering
    Reference
    ---------
    Francois Fouss, Marco Saerens, Masashi Shimbo
    Algorithms and Models for Network Data and Link Analysis
    Algorithm 7.3: Simple iterative kernel k-means clustering of nodes
    """

    name = 'KKMeans_iterative'

    def _predict_once(self, K: np.array):
        h_init = self._init_h(K)
        result = self.backend.iterative_predict(K, h_init, self.max_iter, self.eps, device=self.device)
        return result
