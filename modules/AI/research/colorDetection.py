from collections import Counter
import cv2
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

n_clusters = 1

def RGB2HEX(color):
    return "#{:02x}{:02x}{:02x}".format(int(color[0]), int(color[1]), int(color[2]))

# Read image
original = cv2.imread('coin.png')

# Convert to RGB
image = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
# Resize
image = cv2.resize(image, (600, 600), interpolation = cv2.INTER_AREA)
# Crop center to avoid border effects
image = image[275:325, 275:325]
# Flat to 1D array
image = image.reshape(image.shape[0]*image.shape[1], 3)

# Compute K-Means
clf = KMeans(n_clusters = n_clusters)
colors = clf.fit_predict(image)

# Create a pie chart
counts = Counter(colors)
center_colors = clf.cluster_centers_

ordered_colors = [center_colors[i] for i in counts.keys()]
hex_colors = [RGB2HEX(ordered_colors[i]) for i in counts.keys()]
rgb_colors = [ordered_colors[i] for i in counts.keys()]

plt.figure(figsize = (8, 6))
plt.pie(counts.values(), labels = hex_colors, colors = hex_colors)

plt.show()
