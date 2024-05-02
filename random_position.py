from Framework.ImageButton import ImageButton
from Framework.TrainingWindow import TrainingWindow
from Framework.TrainingImage import TrainingImage
from Framework.ImageCategory import ImageCategory
from Framework.SessionConfig import SessionConfig
from PySide6.QtWidgets import QApplication, QGridLayout, QWidget, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import sys
import random
import os

class RandomPositionTraining(TrainingWindow):
    def startFirstTrial(self):        
        self.layout = QGridLayout(self.container)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)

        trainingImage = self.getImage()
        column = random.randrange(5)
        row = random.randrange(4)

        self.cells = []

        for i in range(5):
            for j in range(4):
                cell = QWidget()
                cellLayout =  QHBoxLayout(cell)

                if i == column and j == row:
                    cellLayout.addWidget(ImageButton(trainingImage, self.imageClicked, imageSize=(250,250)), alignment=Qt.AlignCenter)
                
                self.layout.addWidget(cell, j, i, alignment=Qt.AlignCenter)
                self.cells.append(cellLayout)
        
        self.logTrialStart()

    def startNextTrial(self):
        trainingImage = self.getImage()
        
        cellIndex = random.randrange(len(self.cells))

        for i in range(len(self.cells)):
            item = self.cells[i].takeAt(0)
            if item is not None:
                item.widget().changeImage(None)
            if i == cellIndex:
                self.cells[i].addWidget(ImageButton(trainingImage, self.imageClicked, imageSize=(250,250)), alignment=Qt.AlignCenter)

        self.container.show()
        self.container.update()
        
        self.logTrialStart()
        
    def startCorrectionTrial(self):
        self.container.show()
        
        self.logTrialStart()

    def getImage(self):
        image = os.path.join("Training_Stimuli", "Geometric_Shapes", random.choice(os.listdir(os.path.join("Training_Stimuli", "Geometric_Shapes"))))

        trainingImage = TrainingImage(image, ImageCategory.CORRECT)

        return trainingImage

if __name__ == "__main__":
    app = QApplication([])

    sessionConfig = SessionConfig(interTrialInterval=2000,
                                  errorScreenDuration=1000, 
                                  correctionTrialInterTrialInterval=1000, 
                                  numberOfTrials=5, 
                                  correctionTrialsActive=True, 
                                  backgroundColor=QColor(255,255,255,255), 
                                  errorScreenColor=QColor(255,0,0,255), 
                                  successSoundFilePath=os.path.join("SoundEffects", "600hz.wav"), 
                                  failureSoundFilePath=os.path.join("SoundEffects", "200hz.wav"),
                                  cursorVisible=True,
                                  trainingName="Random Position")

    trainingWindow = RandomPositionTraining(sessionConfig)
    
    trainingWindow.startFirstTrial()

    trainingWindow.showFullScreen()
    
    sys.exit(app.exec())