from PySide6.QtWidgets import QHBoxLayout, QWidget, QMainWindow
from PySide6.QtGui import QColor
from PySide6.QtCore import QTimer, Qt, QUrl, QCoreApplication
from PySide6.QtMultimedia import QSoundEffect
import sys
import os, random
from Framework.ImageButton import ImageButton
from Framework.TrainingImage import TrainingImage
from Framework.ImageCategory import ImageCategory
from Framework.SessionConfig import SessionConfig
import logging
from datetime import datetime

class TrainingWindow(QMainWindow):
    def __init__(self, sessionConfig: SessionConfig, parent=None):
        super().__init__(parent=parent)
        
        self.soundEffect = QSoundEffect(QCoreApplication.instance())

        logDir = os.path.join("SessionLogs", sessionConfig.trainingName.replace(' ', '_'))
        if not os.path.exists(logDir):
            os.makedirs(logDir)
        
        logFilePath = os.path.join("SessionLogs", sessionConfig.trainingName.replace(' ', '_'), str(datetime.now()).replace(' ', '_').replace(':', '-') + ".csv")
        logging.basicConfig(filename=logFilePath,
                    filemode='a',
                    format='%(asctime)s, %(message)s',
                    level=logging.INFO)

        self.sessionConfig = sessionConfig
        self.trialNr = 0
        
        self.viewLayout= QHBoxLayout()
        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0,0,0,0)

        self.view = QWidget()
        self.view.setAutoFillBackground(True)
        self.viewLayout.addWidget(self.view)

        self.setCentralWidget(self.view)
        
        if not sessionConfig.cursorVisible:
            self.view.setCursor(Qt.BlankCursor)

        self.setBackgroundColor(self.sessionConfig.backgroundColor)
        
        containerLayout = QHBoxLayout(self.view)
        containerLayout.setSpacing(0)
        containerLayout.setContentsMargins(0,0,0,0)
        
        self.container = QWidget()
        containerLayout.addWidget(self.container)

        self.logSessionStart()

    def imageClicked(self, trainingImage: TrainingImage, event):
        if trainingImage.imageCategory == ImageCategory.CORRECT:
            self.trialCompletedSuccessful()
        elif trainingImage.imageCategory == ImageCategory.WRONG:
            self.trialCompletedUnscucessful()

        self.logImageClicked(trainingImage, event)

    def startFirstTrial(self):
        raise NotImplementedError("Please Implement this method")

    def startNextTrial(self):
        raise NotImplementedError("Please Implement this method")

    def startCorrectionTrial(self):
        raise NotImplementedError("Please Implement this method")

    def endSession(self):
        self.container.hide()
        palette = self.view.palette()
        palette.setColor(self.view.backgroundRole(), QColor(0,0,0,255))
        self.view.setPalette(palette)
        
        self.logSessionEnd()

    def trialCompletedSuccessful(self):
        self.playSuccessSound()
        self.logTrialEnd(True)

        self.trialNr += 1
        if self.trialNr < self.sessionConfig.numberOfTrials:
            self.startInterTrialInterval()
        else:
            self.endSession()        

    def trialCompletedUnscucessful(self):
        self.playFailureSound()
        self.logTrialEnd(False)

        self.showErrorScreen()

    def showErrorScreen(self):
        self.container.hide()
        self.setBackgroundColor(self.sessionConfig.errorScreenColor)

        timer = QTimer(self)
        timer.setTimerType(Qt.PreciseTimer)
        timer.setSingleShot(True)
        timer.timeout.connect(self, self.hideErrorScreen)
        timer.start(self.sessionConfig.errorScreenDuration)
    
    def setBackgroundColor(self, color: QColor):
        palette = self.view.palette()
        palette.setColor(self.view.backgroundRole(), color)
        self.view.setPalette(palette)

    def hideErrorScreen(self):
        self.setBackgroundColor(self.sessionConfig.backgroundColor)

        self.trialNr += 1
        if self.trialNr < self.sessionConfig.numberOfTrials:
            if self.sessionConfig.correctionTrialsActive:
                self.startFunctionTimer(self.sessionConfig.correctionTrialInterTrialInterval, self.startCorrectionTrial)
            else:
                self.startFunctionTimer(self.sessionConfig.interTrialInterval, self.startNextTrial)
        else:
            self.endSession()

    def startInterTrialInterval(self):
        self.container.hide()

        self.startFunctionTimer(self.sessionConfig.interTrialInterval, self.startNextTrial)

    def startFunctionTimer(self, interval: int, function):
        timer = QTimer(self)
        timer.setTimerType(Qt.PreciseTimer)
        timer.setSingleShot(True)
        timer.timeout.connect(self, function)
        timer.start(interval)

        return timer

    def playSuccessSound(self):
        self.playSound(self.sessionConfig.successSoundFilePath)

    def playFailureSound(self):
        self.playSound(self.sessionConfig.failureSoundFilePath)

    def playSound(self, filePath):
        if filePath is None:
            return

        self.soundEffect.setSource(QUrl.fromLocalFile(filePath))
        self.soundEffect.setVolume(1)
        self.soundEffect.play()

    def logSessionStart(self):
        logging.info("Session Start")
        
    def logSessionEnd(self):
        logging.info("Session End")
    
    def logTrialStart(self):
        logging.info("Trial Start")
        
    def logTrialEnd(self, successful):
        logging.info(f"Trial End, trial success: {successful}")
    
    def logImageClicked(self, trainingImage, event):
        logging.info(f"Image clicked, file path: {trainingImage.filePath}, click location: ({event.position().x()}|{event.position().y()}), image category: {trainingImage.imageCategory}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Q:
            sys.exit()