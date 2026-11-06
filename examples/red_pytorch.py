# Ejemplo de lectura estática: las variables de entrada se aportan en el notebook.
import torch
from torch import nn
red = nn.Sequential(nn.Linear(8, 16), nn.ReLU(), nn.Linear(16, 1))
criterio = nn.MSELoss()
opt = torch.optim.Adam(red.parameters(), lr=0.001)
opt.zero_grad()
pred = red(X)
error = criterio(pred, y)
error.backward()
opt.step()
red.eval()
