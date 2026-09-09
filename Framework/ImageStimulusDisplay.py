from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtCore import QRect, QSize
from Framework.TrainingStimulus import TrainingStimulus

class ImageStimulusDisplay(QWidget):
    def __init__(self, trainingImage: TrainingStimulus, imageSize=None, parent=None):
        super(ImageStimulusDisplay, self).__init__(parent)
        self.changeImage(trainingImage)
        self.imageSize = imageSize

    def paintEvent(self, event):
        painter = QPainter(self)

        if self.imageSize is None:
            painter.drawPixmap(event.rect(), self.pixmap)
        else:
            painter.drawPixmap(QRect(0,0,self.imageSize[0],self.imageSize[1]), self.pixmap)

    def sizeHint(self):
        if self.imageSize is None:
            return self.pixmap.size()
        else:
            return QSize(self.imageSize[0],self.imageSize[1])

    def changeImage(self, trainingImage: TrainingStimulus):
        self.trainingImage = trainingImage
        if trainingImage is not None:
            self.pixmap = QPixmap(trainingImage.filePath)
        else:
            self.pixmap = QPixmap(0,0)
        self.update()