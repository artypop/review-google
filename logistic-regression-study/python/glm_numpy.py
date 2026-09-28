"""
Régression logistique en numpy, pour les postes où statsmodels ne se charge
pas. Écrit le 2026-09-28 : sur le poste Windows de Matthieu, la politique de
sécurité bloque les DLL de scipy, donc statsmodels et scikit-learn.

Reproduit ce que les scripts 07 font avec statsmodels :

    sm.GLM(y, X, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": ...})

  - ajustement par Newton-Raphson (identique à l'IRLS de statsmodels pour une
    logistique), jusqu'à une variation relative de déviance sous 1e-12 ;
  - marges groupées par fiche, avec la correction de petit échantillon de
    statsmodels : G / (G − 1) × (N − 1) / (N − K) ;
  - p-values et fourchettes sur la loi normale, comme statsmodels pour un GLM.

S'utilise à la place de `statsmodels.api` : `installer()` l'enregistre sous ce
nom quand statsmodels ne se charge pas. Vérifié le 2026-09-28 contre
`07B_coefficients_tous.csv` : voir `07C_regression_reduite.py --valider-07B`.
"""
from __future__ import annotations

import sys
import types
from math import erfc, sqrt

import numpy as np
import pandas as pd

Z_95 = 1.959963984540054


class Resultat:
    def __init__(self, params: pd.Series, cov: np.ndarray, nobs: int, deviance: float):
        self.params = params
        self.cov_params_ = cov
        self.bse = pd.Series(np.sqrt(np.diag(cov)), index=params.index)
        self.tvalues = self.params / self.bse
        self.pvalues = pd.Series([erfc(abs(z) / sqrt(2)) for z in self.tvalues],
                                 index=params.index)
        self.nobs, self.deviance = nobs, deviance

    def conf_int(self) -> pd.DataFrame:
        return pd.DataFrame({0: self.params - Z_95 * self.bse,
                             1: self.params + Z_95 * self.bse})

    def predict(self, X) -> np.ndarray:
        X = np.asarray(X, dtype="float64")
        return 1 / (1 + np.exp(-(X @ self.params.to_numpy())))

    def summary(self) -> str:
        t = pd.DataFrame({"coef": self.params, "std err": self.bse, "z": self.tvalues,
                          "P>|z|": self.pvalues,
                          "[0.025": self.conf_int()[0], "0.975]": self.conf_int()[1]})
        return (f"Régression logistique (glm_numpy), {self.nobs} observations, "
                f"déviance {self.deviance:.3f}\nCovariance : groupée par fiche\n\n"
                + t.to_string(float_format=lambda v: f"{v:.4f}"))


class GLM:
    def __init__(self, y, X, family=None):
        self.y = np.asarray(y, dtype="float64")
        self.X = X

    def fit(self, cov_type: str = "cluster", cov_kwds: dict | None = None,
            max_iter: int = 100) -> Resultat:
        X = np.asarray(self.X, dtype="float64")
        y = self.y
        n, k = X.shape
        b = np.zeros(k)
        deviance_avant = np.inf
        for _ in range(max_iter):
            eta = X @ b
            p = 1 / (1 + np.exp(-eta))
            w = p * (1 - p)
            H = X.T @ (X * w[:, None])
            b = b + np.linalg.solve(H, X.T @ (y - p))
            p = np.clip(1 / (1 + np.exp(-(X @ b))), 1e-300, 1 - 1e-16)
            deviance = -2 * np.sum(y * np.log(p) + (1 - y) * np.log1p(-p))
            if abs(deviance_avant - deviance) <= 1e-12 * (abs(deviance) + 1):
                break
            deviance_avant = deviance
        else:
            raise RuntimeError("glm_numpy : l'ajustement n'a pas convergé")

        p = 1 / (1 + np.exp(-(X @ b)))
        H_inv = np.linalg.inv(X.T @ (X * (p * (1 - p))[:, None]))
        if cov_type != "cluster":
            cov = H_inv
        else:
            groupes = pd.factorize(np.asarray(cov_kwds["groups"]))[0]
            scores = pd.DataFrame(X * (y - p)[:, None]).groupby(groupes).sum().to_numpy()
            g = scores.shape[0]
            cov = H_inv @ (scores.T @ scores) @ H_inv
            cov *= (g / (g - 1)) * ((n - 1) / (n - k))
        noms = getattr(self.X, "columns", range(k))
        return Resultat(pd.Series(b, index=noms), cov, n, float(deviance))


def add_constant(X: pd.DataFrame, has_constant: str = "add") -> pd.DataFrame:
    X = X.copy()
    X.insert(0, "const", 1.0)
    return X


def installer() -> None:
    """Enregistre ce module sous le nom `statsmodels.api`."""
    api = types.ModuleType("statsmodels.api")
    api.GLM = GLM
    api.add_constant = add_constant
    api.families = types.SimpleNamespace(Binomial=lambda: None)
    paquet = types.ModuleType("statsmodels")
    paquet.api = api
    sys.modules["statsmodels"] = paquet
    sys.modules["statsmodels.api"] = api
