import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import plotly.graph_objects as go
from pathlib import Path

# Ensure the figures directory exists
figures_dir = Path("figures")
figures_dir.mkdir(parents=True, exist_ok=True)

# Define parameters
xmax = 1
N = 20
X = np.linspace(0, xmax, N+1)
x, y = np.meshgrid(X, X)
x = x.ravel()
y = y.ravel()

NNODES = (N+1)**2
NTRI = 2 * N**2
LNODES = np.zeros((NTRI, 3), dtype=int)

# Generate triangulation
for i in range(N):
    for j in range(N):
        idx = i + j * (N + 1)
        LNODES[2 * (i + j * N), :] = [idx, idx + (N + 1), idx + 1]
        LNODES[2 * (i + j * N) + 1, :] = [idx + 1, idx + (N + 1), idx + (N + 2)]

SP = sp.lil_matrix((NNODES, NNODES))
LV = np.zeros(NNODES)

for n in range(NTRI):
    r1 = np.array([x[LNODES[n, 0]], y[LNODES[n, 0]]])
    r2 = np.array([x[LNODES[n, 1]], y[LNODES[n, 1]]])
    r3 = np.array([x[LNODES[n, 2]], y[LNODES[n, 2]]])
    J = np.array([[r2[0] - r1[0], r2[1] - r1[1]], [r3[0] - r1[0], r3[1] - r1[1]]])
    detJ = np.linalg.det(J)
    if np.abs(detJ) < 1e-12:
        continue
    
    v1 = r2 - r3
    v2 = r3 - r1
    v3 = r1 - r2
    Astiff = (1 / (2 * detJ)) * np.array([
        [np.dot(v1, v1), np.dot(v1, v2), np.dot(v1, v3)],
        [np.dot(v2, v1), np.dot(v2, v2), np.dot(v2, v3)],
        [np.dot(v3, v1), np.dot(v3, v2), np.dot(v3, v3)]
    ])
    
    for i in range(3):
        for j in range(3):
            SP[LNODES[n, i], LNODES[n, j]] += Astiff[i, j]
    
    ksi, eta = 1/3, 1/3
    xx = (1 - ksi - eta) * r1[0] + ksi * r2[0] + eta * r3[0]
    yy = (1 - ksi - eta) * r1[1] + ksi * r2[1] + eta * r3[1]
    F = np.array([
        (1-ksi-eta) * 5 * np.pi**2 * np.sin(np.pi * xx) * np.sin(2 * np.pi * yy) * detJ / 2,
        ksi * 5 * np.pi**2 * np.sin(np.pi * xx) * np.sin(2 * np.pi * yy) * detJ / 2,
        eta * 5 * np.pi**2 * np.sin(np.pi * xx) * np.sin(2 * np.pi * yy) * detJ / 2
    ])
    
    for i in range(3):
        LV[LNODES[n, i]] += F[i]

for i in range(NNODES):
    if x[i] == 0 or y[i] == 0 or x[i] == xmax or y[i] == xmax:
        LV[i] = 0
        SP[i, :] = 0
        SP[i, i] = 1

SP = sp.csr_matrix(SP)
U = spla.spsolve(SP, LV)

u_exact = np.sin(np.pi * x) * np.sin(2 * np.pi * y)
Error = np.sum(np.abs(U - u_exact)**2)
print("Error:", Error)

# Create interactive 3D plot using Plotly
fig = go.Figure()

fig.add_trace(go.Mesh3d(
    x=x, y=y, z=U,
    i=LNODES[:, 0], j=LNODES[:, 1], k=LNODES[:, 2],
    color='lightblue', opacity=0.50,
    name='Numerical Solution'
))

fig.add_trace(go.Mesh3d(
    x=x, y=y, z=u_exact,
    i=LNODES[:, 0], j=LNODES[:, 1], k=LNODES[:, 2],
    color='red', opacity=0.50,
    name='Exact Solution'
))

fig.update_layout(
    title="Numerical vs Exact Solution",
    scene=dict(
        xaxis_title="X",
        yaxis_title="Y",
        zaxis_title="U(x, y)"
    ),
    legend=dict(x=0, y=1)
)

# Show the plot in browser
import plotly.io as pio
pio.renderers.default = "browser"
fig.show()

