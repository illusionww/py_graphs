import argparse
import sys

import numpy as np
from joblib import Parallel, delayed
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from tqdm import tqdm

sys.path.append('../../..')
from pygkernels.cluster import KKMeans
from pygkernels.data import Datasets
from pygkernels.measure import kernels
from pygkernels.util import load_or_calc_and_save
from pygkernels.score import sns1

CACHE_ROOT = '/media/illusionww/68949C3149F4E819/phd/pygkernels/kkmeans_init_datasets_modularity'
dataset_names = [
    'cora_DB',
    'cora_EC',
    'cora_HA',
    'cora_HCI',
    'cora_IR',
    'cora_Net',
    'dolphins',
    'eu-core',
    'eurosis',
    'football',
    'karate',
    'news_2cl_1',
    'news_2cl_2',
    'news_2cl_3',
    'news_3cl_1',
    'news_3cl_2',
    'news_3cl_3',
    'news_5cl_1',
    'news_5cl_2',
    'news_5cl_3',
    'polblogs',
    'polbooks',
    'sp_school_day_1',
    'sp_school_day_2'
]


def perform_param(param_flat, graph, kernel_class, estimator):
    A, y_true = graph
    kernel = kernel_class(A)

    param_results = []
    try:
        param = kernel.scaler.scale(param_flat)
        K = kernel.get_K(param)
        inits = estimator.predict(K, explicit=True, A=A)
        for init in inits:
            y_pred = init['labels']
            param_results.append({
                'labels': y_pred,
                'inertia': init['inertia'],
                'init': init['init'],
                'score_ari': adjusted_rand_score(y_true, y_pred),
                'score_nmi': normalized_mutual_info_score(y_true, y_pred, average_method='geometric'),
                'score_sns1': sns1(y_true, y_pred)
            })
    except Exception or ValueError or FloatingPointError or np.linalg.LinAlgError:
        pass

    return param_flat, param_results


def perform_graph(graph, kernel_class, k):
    params = np.linspace(0, 1, N_PARAMS)
    results = dict(Parallel(n_jobs=N_JOBS)(delayed(perform_param)(
        param_flat, graph, kernel_class,
        KKMeans(k, device=param_idx % N_GPU, random_state=2000 + param_idx, n_init=N_INITS)
    ) for param_idx, param_flat in enumerate(params)))
    return results


def perform_kernel(dataset_name, graphs, kernel_class, k, root=f'{CACHE_ROOT}/by_column_and_kernel'):
    @load_or_calc_and_save(f'{root}/{dataset_name}_{kernel_class.name}_results.pkl')
    def _calc(n_graphs=None, n_params=None, n_jobs=None):
        results = []
        for graph_idx, graph in enumerate(graphs):
            result = perform_graph(graph, kernel_class, k)
            results.append(result)
        return results

    return _calc(n_graphs=None, n_params=None, n_jobs=None)


def perform_column(dataset_name, graphs, k):
    for kernel_class in tqdm(kernels, desc=dataset_name):
        perform_kernel(dataset_name, graphs, kernel_class, k)


def perform():
    for dataset_name in dataset_names:
        graphs, _, info = Datasets()[dataset_name]
        graphs = graphs * N_GRAPHS
        perform_column(dataset_name, graphs, info['k'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--n_jobs', type=int, default=6, required=False)
    parser.add_argument('--n_gpu', type=int, default=2, required=False)
    parser.add_argument('--n_graphs', type=int, default=20, required=False)
    parser.add_argument('--n_inits', type=int, default=30, required=False)
    parser.add_argument('--n_params', type=int, default=51, required=False)

    args = parser.parse_args()
    print(args)

    N_JOBS = args.n_jobs
    N_GPU = args.n_gpu
    N_GRAPHS = args.n_graphs
    N_INITS = args.n_inits
    N_PARAMS = args.n_params
    perform()
