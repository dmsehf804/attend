import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


df = pd.read_csv('1.csv')
ax = df.plot(kind='box', title='feature', figsize=(12, 4), legend=True, fontsize=12)
ax.set_ylabel('distance', fontsize=12)
plt.show()