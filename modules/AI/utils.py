import cv2
import numpy as np

PADDING = 10 # Padding for the bounding box

def prepare(image):
    images = []
    debug = image.copy()

    gray = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    blur = cv2.GaussianBlur(gray, (19, 19), 0)

    circles = cv2.HoughCircles(
        blur,  # source image
        cv2.HOUGH_GRADIENT,  # type of detection
        1,
        50,
        param1=100,
        param2=30,
        minRadius=5,  # minimal radius
        maxRadius=180,  # max radius
    )

    # No circle detected
    if (circles is None):
        return image, None, []

    for i in range(len(circles[0])):
        circle = circles[0][i]

        x, y, r = circle.astype(int)
        w, h = r * 2, r * 2
        
        # Define Bouding box
        yMin, yMax = y - r - PADDING, y + r + PADDING
        xMin, xMax = x - r - PADDING, x + r + PADDING
        # Correct Bouding box if it is out of the image
        if (yMin < 0):
            yMin = 0
        if (yMax > image.shape[0]):
            yMax = image.shape[0]
        if (xMin < 0):
            xMin = 0
        if (xMax > image.shape[1]):
            xMax = image.shape[1]

        data = {
            "id": i,
            "image": image[yMin:yMax, xMin:xMax],
            "area": {
                "x": xMin,
                "y": yMin,
                "width": xMax,
                "height": yMax
            },
            "radius": r,
            "center": {
                "x": x,
                "y": y
            }
        }
        images.append(data)

        cv2.circle(
            debug,
            (int(x), int(y)),
            int(r),
            (0, 255, 0),
            4,
        )
        cv2.putText(debug, str(data["id"]), (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    return image, debug, images

def test():
    image, images = prepare(cv2.imread("test.png"))
    cv2.imshow("image", image)
    cv2.waitKey(0)
