from flask import Flask, render_template, Response
from handTracker import HandTracker
import cv2
import numpy as np
import random
import threading

app = Flask(__name__)

class ColorRect():
    def __init__(self, x, y, w, h, color, text='', alpha=0.5):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.text = text
        self.alpha = alpha

    def drawRect(self, img, text_color=(255, 255, 255), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8,
                 thickness=2):
        alpha = self.alpha
        bg_rec = img[self.y: self.y + self.h, self.x: self.x + self.w]
        white_rect = np.ones(bg_rec.shape, dtype=np.uint8)
        white_rect[:] = self.color
        res = cv2.addWeighted(bg_rec, alpha, white_rect, 1 - alpha, 1.0)

        # Putting the image back to its position
        img[self.y: self.y + self.h, self.x: self.x + self.w] = res

        # Put the letter
        text_size = cv2.getTextSize(self.text, fontFace, fontScale, thickness)
        text_pos = (int(self.x + self.w / 2 - text_size[0][0] / 2), int(self.y + self.h / 2 + text_size[0][1] / 2))
        cv2.putText(img, self.text, text_pos, fontFace, fontScale, text_color, thickness)

    def isOver(self, x, y):
        if (self.x + self.w > x > self.x) and (self.y + self.h > y > self.y):
            return True
        return False

# Initialize the hand detector
detector = HandTracker(detectionCon=int(0.8))

# Initialize the camera
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# Creating canvas to draw on it
canvas = np.zeros((720, 1280, 3), np.uint8)

# Define a previous point to be used with drawing a line
px, py = 0, 0
# Initial brush color
color = (255, 0, 0)
brushSize = 5
eraserSize = 20

########### Creating colors ########
# Colors button
colorsBtn = ColorRect(200, 0, 100, 100, (120, 255, 0), 'Colors')

colors = []
# Random color
b = int(random.random() * 255) - 1
g = int(random.random() * 255)
r = int(random.random() * 255)
print(b, g, r)
colors.append(ColorRect(300, 0, 100, 100, (b, g, r)))
# Red
colors.append(ColorRect(400, 0, 100, 100, (0, 0, 255)))
# Blue
colors.append(ColorRect(500, 0, 100, 100, (255, 0, 0)))
# Green
colors.append(ColorRect(600, 0, 100, 100, (0, 255, 0)))
# Yellow
colors.append(ColorRect(700, 0, 100, 100, (0, 255, 255)))
# Erase (black)
colors.append(ColorRect(800, 0, 100, 100, (0, 0, 0), "Eraser"))

# Clear
clear = ColorRect(900, 0, 100, 100, (100, 100, 100), "Clear")

########## Pen sizes #######
pens = []
for i, penSize in enumerate(range(5, 25, 5)):
    pens.append(ColorRect(1100, 50 + 100 * i, 100, 100, (50, 50, 50), str(penSize)))

penBtn = ColorRect(1100, 0, 100, 50, color, 'Pen')

# White board button
boardBtn = ColorRect(50, 0, 100, 100, (255, 255, 0), 'Board')

#define a white board to draw on
whiteBoard = ColorRect(50, 120, 1020, 580, (255, 255, 255), alpha=0.6)

@app.route('/')
def index():
    return render_template('index.html')

def gen_frames():
    global cap, canvas, px, py, color, brushSize, eraserSize, hideBoard, hideColors, hidePenSizes

    while True:
        if 'coolingCounter' not in globals():
            coolingCounter = 20

        if 'hideBoard' not in globals():
            hideBoard = True

        if 'hideColors' not in globals():
            hideColors = True

        if 'hidePenSizes' not in globals():
            hidePenSizes = True

        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.resize(frame, (1280, 720))
        frame = cv2.flip(frame, 1)

        detector.findHands(frame)
        positions = detector.getPostion(frame, draw=False)
        upFingers = detector.getUpFingers(frame)

        if upFingers:
            x, y = positions[8][0], positions[8][1]
            if upFingers[1] and not whiteBoard.isOver(x, y):
                px, py = 0, 0

                ##### pen sizes ######
                if not hidePenSizes:
                    for pen in pens:
                        if pen.isOver(x, y):
                            brushSize = int(pen.text)
                            pen.alpha = 0
                            print("Pen size selected:", brushSize)
                        else:
                            pen.alpha = 0.5

                ####### chose a color for drawing #######
                if not hideColors:
                    for cb in colors:
                        if cb.isOver(x, y):
                            color = cb.color
                            cb.alpha = 0
                            print("Color selected:", color)
                        else:
                            cb.alpha = 0.5

                    # Clear
                    if clear.isOver(x, y):
                        clear.alpha = 0
                        canvas = np.zeros((720, 1280, 3), np.uint8)
                        print("Canvas cleared")
                    else:
                        clear.alpha = 0.5

                # color button
                if colorsBtn.isOver(x, y) and not coolingCounter:
                    coolingCounter = 10
                    colorsBtn.alpha = 0
                    hideColors = not hideColors
                    colorsBtn.text = 'Colors' if hideColors else 'Hide'
                    print("Colors button clicked, hideColors:", hideColors)
                else:
                    colorsBtn.alpha = 0.5

                # Pen size button
                if penBtn.isOver(x, y) and not coolingCounter:
                    coolingCounter = 10
                    penBtn.alpha = 0
                    hidePenSizes = not hidePenSizes
                    penBtn.text = 'Pen' if hidePenSizes else 'Hide'
                    print("Pen button clicked, hidePenSizes:", hidePenSizes)
                else:
                    penBtn.alpha = 0.5

                # white board button
                if boardBtn.isOver(x, y) and not coolingCounter:
                    coolingCounter = 10
                    boardBtn.alpha = 0
                    hideBoard = not hideBoard
                    boardBtn.text = 'Board' if hideBoard else 'Hide'
                    print("Board button clicked, hideBoard:", hideBoard)
                else:
                    boardBtn.alpha = 0.5

            elif upFingers[1] and not upFingers[2]:
                if whiteBoard.isOver(x, y) and not hideBoard:
                    cv2.circle(frame, positions[8], brushSize, color, -1)
                    # drawing on the canvas
                    if px == 0 and py == 0:
                        px, py = positions[8]
                    if color == (0, 0, 0):
                        cv2.line(canvas, (px, py), positions[8], color, eraserSize)
                    else:
                        cv2.line(canvas, (px, py), positions[8], color, brushSize)
                    px, py = positions[8]

            else:
                px, py = 0, 0

        # put colors button
        colorsBtn.drawRect(frame)
        cv2.rectangle(frame, (colorsBtn.x, colorsBtn.y), (colorsBtn.x + colorsBtn.w, colorsBtn.y + colorsBtn.h),
                      (255, 255, 255), 2)

        # put white board buttin
        boardBtn.drawRect(frame)
        cv2.rectangle(frame, (boardBtn.x, boardBtn.y), (boardBtn.x + boardBtn.w, boardBtn.y + boardBtn.h),
                      (255, 255, 255), 2)

        # put the white board on the frame
        if not hideBoard:
            whiteBoard.drawRect(frame)
            ########### moving the draw to the main image #########
            canvasGray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
            _, imgInv = cv2.threshold(canvasGray, 20, 255, cv2.THRESH_BINARY_INV)
            imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
            frame = cv2.bitwise_and(frame, imgInv)
            frame = cv2.bitwise_or(frame, canvas)

        ########## pen colors' boxes #########
        if not hideColors:
            for c in colors:
                c.drawRect(frame)
                cv2.rectangle(frame, (c.x, c.y), (c.x + c.w, c.y + c.h), (255, 255, 255), 2)

            clear.drawRect(frame)
            cv2.rectangle(frame, (clear.x, clear.y), (clear.x + clear.w, clear.y + clear.h), (255, 255, 255), 2)

        ########## brush size boxes ######
        penBtn.color = color
        penBtn.drawRect(frame)
        cv2.rectangle(frame, (penBtn.x, penBtn.y), (penBtn.x + penBtn.w, penBtn.y + penBtn.h), (255, 255, 255), 2)
        if not hidePenSizes:
            for pen in pens:
                pen.drawRect(frame)
                cv2.rectangle(frame, (pen.x, pen.y), (pen.x + pen.w, pen.y + pen.h), (255, 255, 255), 2)

        # Convert frame to bytes
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def start_camera():
    global cap
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)

if __name__ == '__main__':
    t = threading.Thread(target=start_camera)
    t.start()
    app.run(debug=True, threaded=True)
