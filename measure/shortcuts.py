import numpy as np
from scipy.sparse.csgraph import johnson


def normalize(dm: np.matrixlib.defmatrix.matrix):
    return dm / dm.std() if dm.std() != 0 else dm


def getD(A: np.matrixlib.defmatrix.matrix):
    return np.diag(np.sum(A, axis=0))


def getL(A: np.matrixlib.defmatrix.matrix):
    return getD(A) - A


def H0toH(H0: np.matrixlib.defmatrix.matrix):
    """
    H = element - wise log(H0)
    """
    return np.log(H0)


def HtoD(H: np.matrixlib.defmatrix.matrix):
    """
    D = (h * 1^T + 1 * h^T - H - H ^ T) / 2
    """
    size = H.shape[0]
    h = np.diagonal(H).reshape(-1, 1)
    i = np.ones((size, 1))
    return 0.5 * ((h.dot(i.transpose()) + i.dot(h.transpose())) - H - H.transpose())


def DtoK(D: np.matrixlib.defmatrix.matrix):
    """
    K = -1 / 2 HΔH
    """
    size = D.shape[0]
    H = np.eye(size) - (np.ones((size, size)) / size)
    K = -0.5 * np.dot(H, D).dot(H)
    return K


def D_SP(A: np.matrixlib.defmatrix.matrix):
    """
    Johnson's Algorithm
    """
    return johnson(A, directed=False)


def H_R(A: np.matrixlib.defmatrix.matrix):
    """
    H = (L + J)^{-1}
    """
    size = A.shape[0]
    L = getL(A)
    J = np.ones((size, size)) / size
    return np.linalg.pinv(L + J)


def H_CCT(A: np.matrixlib.defmatrix.matrix):
    """
    H = I - E / n
    M = D^{-1/2}(A - dd^T/vol(G))D^{-1/2},
        d is a vector of the diagonal elements of D,
        vol(G) is the volume of the graph
    K_CCT = HD^{-1/2}M(I - M)^{-1}MD^{-1/2}H
    """
    size = A.shape[0]
    I = np.eye(size)
    d = np.sum(A, axis=0).reshape((-1, 1))
    D05 = np.diag(np.power(d, -0.5)[:, 0])
    H = np.eye(size) - np.ones((size, size)) / size
    volG = np.sum(A)
    M = D05.dot(A - d.dot(d.transpose()) / volG).dot(D05)
    return H.dot(D05).dot(M).dot(np.linalg.pinv(I - M)).dot(M).dot(D05).dot(H)
