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
x_flat = x.ravel()
y_flat = y.ravel()

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
    r1 = np.array([x_flat[LNODES[n, 0]], y_flat[LNODES[n, 0]]])
    r2 = np.array([x_flat[LNODES[n, 1]], y_flat[LNODES[n, 1]]])
    r3 = np.array([x_flat[LNODES[n, 2]], y_flat[LNODES[n, 2]]])
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
    if x_flat[i] == 0 or y_flat[i] == 0 or x_flat[i] == xmax or y_flat[i] == xmax:
        LV[i] = 0
        SP[i, :] = 0
        SP[i, i] = 1

SP = sp.csr_matrix(SP)
U = spla.spsolve(SP, LV)

# Compute exact solution
u_exact = np.sin(np.pi * x_flat) * np.sin(2 * np.pi * y_flat)

# Compute L2 error
Error = np.sum(np.abs(U - u_exact)**2)
print("L2 Error:", Error)

# **Shift Exact Solution to the Right for Side-by-Side Comparison**
x_shifted = x_flat + 1.2  # Offset exact solution to the right

# Create interactive 3D plot using Plotly
fig = go.Figure()

# Plot Numerical Solution (Left Side)
fig.add_trace(go.Mesh3d(
    x=x_flat, y=y_flat, z=U,
    i=LNODES[:, 0], j=LNODES[:, 1], k=LNODES[:, 2],
    color='blue',
    opacity=0.8,
    name="Numerical Solution",
    flatshading=True
))

# Plot Exact Solution (Right Side, Shifted)
fig.add_trace(go.Mesh3d(
    x=x_shifted, y=y_flat, z=u_exact,
    i=LNODES[:, 0], j=LNODES[:, 1], k=LNODES[:, 2],
    color='red',
    opacity=0.8,
    name="Exact Solution",
    flatshading=True
))

# **Add Black Wireframe Edges**
def get_edges(nodes, x_vals, y_vals, z_vals):
    """Generate black wireframe edges for the mesh."""
    edge_x, edge_y, edge_z = [], [], []
    for tri in nodes:
        for i in range(3):
            j = (i + 1) % 3  # Get the next vertex in the triangle
            edge_x.extend([x_vals[tri[i]], x_vals[tri[j]], None])  # None for discontinuity
            edge_y.extend([y_vals[tri[i]], y_vals[tri[j]], None])
            edge_z.extend([z_vals[tri[i]], z_vals[tri[j]], None])
    return edge_x, edge_y, edge_z

# Generate wireframe edges for numerical and exact solutions
num_edge_x, num_edge_y, num_edge_z = get_edges(LNODES, x_flat, y_flat, U)
exact_edge_x, exact_edge_y, exact_edge_z = get_edges(LNODES, x_shifted, y_flat, u_exact)

# Add wireframe to numerical solution
fig.add_trace(go.Scatter3d(
    x=num_edge_x, y=num_edge_y, z=num_edge_z,
    mode='lines',
    line=dict(color='black', width=2),
    name='Mesh Edges (Numerical)'
))

# Add wireframe to exact solution
fig.add_trace(go.Scatter3d(
    x=exact_edge_x, y=exact_edge_y, z=exact_edge_z,
    mode='lines',
    line=dict(color='black', width=2),
    name='Mesh Edges (Exact)'
))

# Update layout
fig.update_layout(
    title="Numerical vs Exact Solution (With Black Triangulation Edges)",
    scene=dict(
        xaxis_title="X (Left: Numerical, Right: Exact)",
        yaxis_title="Y",
        zaxis_title="U(x, y)"
    ),
    legend=dict(x=0, y=1)
)

# Show the plot in browser
import plotly.io as pio
pio.renderers.default = "browser"
fig.show()
