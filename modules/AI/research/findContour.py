import cv2
import numpy as np

image = cv2.imread('original.png')

gray = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
gray = cv2.equalizeHist(gray)
blur = cv2.GaussianBlur(gray, (19, 19), 0)
# Application d'un seuil pour obtenir une image binaire
thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 1)
kernel = np.ones((3, 3), np.uint8)
# Application d'érosion et d'ouverture pour supprimer les contours de petites pièces
closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)

contours, hierarchy = cv2.findContours(closing.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for contour in contours:
    area = cv2.contourArea(contour)
    if area < 10000 or area > 50000:
        continue
    print(area)

    if len(contour) < 5:
        continue

    try:
        ellipse = cv2.fitEllipse(contour)
        cv2.ellipse(image, ellipse, (0,255,0), 2)
    except:
        pass

# ecriture de l'image
cv2.imwrite('result.png', image)