import cv2
import mediapipe as mp
import math
from loguru import logger


class HandTracker():
    def __init__(self):
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(min_detection_confidence=0.7)
        self.mpDraw = mp.solutions.drawing_utils
        self.fingersId=[4,8,12,16,20]
        self.palm=Palm()
        self.central_win_point=[330, 250]


    def find_hands(self,image,draw=True):#Функция определения руки на картинке
        self.win_size=image.shape

        imgRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.res = self.hands.process(imgRGB)

        if self.res.multi_hand_landmarks:
            for handLms in self.res.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(image, handLms, self.mpHands.HAND_CONNECTIONS)

        return image

    def findPos(self,img,handNum=0):#Находит возиции всех поинтов на руке
        self.LmList=[]

        if self.res.multi_hand_landmarks:
            MyHand=self.res.multi_hand_landmarks[handNum]
            for id, lm in enumerate(MyHand.landmark):
                # print(id, lm)
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                # print(id, cx, cy)
                self.LmList.append([id,cx,cy])
        if len(self.LmList)==0:
            self.hand_on_screen=False
        else:
            self.hand_on_screen=True
        return self.LmList

    def fingersUp(self,fingersNum=None,onlyListActive=False): #Определяет состояние пальцев руки или конкретного пальца/пальцев
        fingers=[]
        if len(self.LmList) !=0:
            if self.LmList[self.fingersId[0]][1] > self.LmList[self.fingersId[0]-1][1]:
                fingers.append(1)
            else:
                fingers.append(0)

            for id in range(1,5):
                if self.LmList[self.fingersId[id]][2]<self.LmList[self.fingersId[id]-2][2]:
                    fingers.append(1)
                else:
                    fingers.append(0)
        if fingersNum is None:
            return fingers
        if len(fingers)==0:
            return None
        try:
            if int(fingersNum): #возвращает состояние конкретного пальца
                if onlyListActive: #проверка на активность только указаного пальца
                    check=True
                    for id in range(len(fingers)):
                        if id != fingersNum and fingers[id]==0:
                            continue
                        elif id!=fingersNum and fingers[id]==1:
                            check=False
                            return None
                        if fingers[fingersNum]==1:
                            continue
                        else:
                            check=False
                            return None
                    if check:
                        # return True, lmlist[self.fingersId[fingersNum]]
                        return True, self.LmList[self.fingersId[fingersNum]][1:]
                    else:
                        return None
                else:
                    return fingers[fingersNum]
        except:
            if onlyListActive: #проверка на активность только указаных пальцев
                check=True
                for id in range(len(fingers)-1):
                    if not id in fingersNum:
                        if fingers[id]==0:
                            continue
                        else:
                            check=False
                            return None
                    if id in fingersNum:
                        for userNums in fingersNum:
                            if fingers[userNums] == 1:
                                continue
                            else:
                                check = False
                                return None
                if check:
                    return True
                else:
                    return None
            else:
                return [fingers[id] for id in fingersNum]
        else:
            return None

    def palmDet(self,img=None):
        if not img is None:
            image = self.palm.getPos(self.LmList, img)
            return image
        else:
            positions=self.palm.getPos(self.LmList, img)
            return positions

    def getPalmMoves(self,moves_numbers=None):
        return  self.palm.palmMoves(self.central_win_point,moves_numbers)


class Palm():
    def __init__(self):
        self.palmId=[0,5,9,13,17]
        self.positions=[]
        self.status="CENTER"
        self.onScreen=False
        self.moves = []

    def getPos(self,lmlist,img=None):#Определяет поцицию ладони через позицию точки в центре ладони созданую в центре отрезка между точками на ладони
        if len(lmlist)!=0:
            self.onScreen=True
            self.nowPos=[lmlist[id][1:] for id in self.palmId]#убрать срез дляполучения id точек
            # print(self.nowPos)
            x1, y1 = lmlist[0][1], lmlist[0][2]
            x2, y2 = lmlist[13][1], lmlist[13][2]
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            lenght = int(math.hypot(x2 - x1, y2 - y1))
            if not img is None:
                cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)
                return img
            else:
                # print(cx,cy)
                if len(self.positions)>100:#ограничение хранимых позиций
                    self.positions=[]
                self.positions.append([cx,cy])
                return self.positions
        else:
            self.onScreen=False

    def palmMoves(self,centPoint=None,moves_numbers=None):#
        if self.onScreen:
            if len(self.positions)>=20:
                now_pos=self.positions[len(self.positions)-1] #позиция после движения
                last_pos=self.positions[len(self.positions)-20] #позиция до движения
                x_moved=now_pos[0]-centPoint[0] #разница между х
                y_moved=now_pos[1]-centPoint[1] #разница между у


                if x_moved>180 and y_moved<-170:
                    self.status="LEFT_DIAGONAL"
                elif x_moved<-260 and y_moved<-130:
                    self.status="RIGHT_DIAGONAL"
                elif x_moved<-270 and y_moved>155:
                    self.status="RIGHT_DOWN_DIAGONAL"
                elif x_moved > 230 and y_moved > 160:
                    self.status = "LEFT_DOWN_DIAGONAL"
                elif y_moved<-150:
                    self.status="UP"
                elif y_moved>150:
                    self.status="DOWN"
                elif x_moved>145:
                    self.status="LEFT"
                elif x_moved<-155:
                    self.status="RIGHT"
                else:
                    self.status="CENTER"
                # lenght = int(math.hypot(now_pos[0] - last_pos[0], now_pos[1] - last_pos[1]))  #растояние от последней точки ладони до нынешней позиции
                if self.status is None:
                    self.status="CENTER"
                if not moves_numbers is None:
                    if len(self.moves) >= moves_numbers:
                        temp = self.moves
                        self.moves = []
                        return temp
                    if len(self.moves)<=moves_numbers:
                        if not self.status in self.moves:
                            self.moves.append(self.status)
                        return None
                    elif len(self.moves)>moves_numbers:
                        temp=self.moves
                        self.moves=[]
                        return temp
                if moves_numbers is None:
                    return self.status
        else:
            self.status="CENTER"
            return




if __name__ == '__main__':
    cap = cv2.VideoCapture(0)
    hand_detector=HandTracker()


    while True:
        suc, image = cap.read()
        image=hand_detector.find_hands(image)
        lmlist = hand_detector.findPos(image)
        fing=hand_detector.fingersUp(fingersNum=1)
        print(fing)


        cv2.imshow("image", image)
        cv2.waitKey(1)
