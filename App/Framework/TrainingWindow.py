from PySide6.QtWidgets import QHBoxLayout, QWidget
from PySide6.QtGui import QColor
from PySide6.QtCore import QTimer, Qt, QUrl, QCoreApplication
from PySide6.QtMultimedia import QSoundEffect
import os
import logging
from datetime import datetime
from Framework.TrainingStimulus import TrainingStimulus
from Framework.StimulusCategory import StimulusCategory
from Framework.SessionConfig import SessionConfig
from Framework.paths import get_log_root

class TrainingWindow(QWidget):
    def __init__(self, sessionConfig: SessionConfig, parent=None, sessionEndCallback=None):
        super().__init__(parent=parent)

        logDir = os.path.join(get_log_root(), "SessionLogs", sessionConfig.trainingName.replace(' ', '_'))
        os.makedirs(logDir, exist_ok=True)
        logFilePath = os.path.join(logDir, str(datetime.now()).replace(' ', '_').replace(':', '-') + ".csv")

        self.logger = logging.getLogger(logFilePath)
        self.logger.setLevel(logging.INFO)
        self._logFile = open(logFilePath, 'a', buffering=1)
        handler = logging.StreamHandler(self._logFile)
        handler.setFormatter(logging.Formatter('%(asctime)s, %(message)s'))
        self.logger.addHandler(handler)

        self.sessionConfig = sessionConfig
        self.trialNr = 0
        self.sessionEndCallback = sessionEndCallback

        self.successSound = QSoundEffect(self)
        if sessionConfig.successSoundFilePath:
            self.successSound.setSource(QUrl.fromLocalFile(sessionConfig.successSoundFilePath))
            self.successSound.setVolume(1)

        self.failureSound = QSoundEffect(self)
        if sessionConfig.failureSoundFilePath:
            self.failureSound.setSource(QUrl.fromLocalFile(sessionConfig.failureSoundFilePath))
            self.failureSound.setVolume(1)

        self.viewLayout = QHBoxLayout()
        self.viewLayout.setSpacing(0)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.view = QWidget()
        self.view.setAutoFillBackground(True)
        self.viewLayout.addWidget(self.view)
        self.setLayout(self.viewLayout)

        if not sessionConfig.cursorVisible:
            self.view.setCursor(Qt.BlankCursor)

        self.setBackgroundColor(self.sessionConfig.backgroundColor)

        containerLayout = QHBoxLayout(self.view)
        containerLayout.setSpacing(0)
        containerLayout.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget()
        containerLayout.addWidget(self.container)

        self.logSessionStart()

    def stimulusSelected(self, trainingStimulus: TrainingStimulus):
        if trainingStimulus.stimulusCategory == StimulusCategory.CORRECT:
            self.trialCompletedSuccessful()
        elif trainingStimulus.stimulusCategory == StimulusCategory.WRONG:
            self.trialCompletedUnsuccessful()
        self.logStimulusSelected(trainingStimulus)

    def startFirstTrial(self):
        raise NotImplementedError("Please Implement this method")

    def startNextTrial(self):
        raise NotImplementedError("Please Implement this method")

    def startCorrectionTrial(self):
        raise NotImplementedError("Please Implement this method")

    def endSession(self):
        self.container.hide()
        palette = self.view.palette()
        palette.setColor(self.view.backgroundRole(), QColor(0, 0, 0, 255))
        self.view.setPalette(palette)

        if self.sessionEndCallback is not None:
            self.sessionEndCallback()

        self.logSessionEnd()

    def trialCompletedSuccessful(self):
        self.successSound.play()
        self.logTrialEnd(True)

        self.trialNr += 1
        if self.trialNr < self.sessionConfig.numberOfTrials:
            self.startInterTrialInterval()
        else:
            self.endSession()

    def trialCompletedUnsuccessful(self):
        self.failureSound.play()
        self.logTrialEnd(False)
        self.showErrorScreen()

    def showErrorScreen(self):
        self.container.hide()
        self.setBackgroundColor(self.sessionConfig.errorScreenColor)
        self.startFunctionTimer(self.sessionConfig.errorScreenDuration, self.hideErrorScreen)

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
        timer.timeout.connect(function)
        timer.start(interval)
        return timer

    def logSessionStart(self):
        self.logger.info("Session Start")

    def logSessionEnd(self):
        self.logger.info("Session End")

    def logTrialStart(self):
        self.logger.info("Trial Start")

    def logTrialEnd(self, successful):
        self.logger.info(f"Trial End, trial success: {successful}")

    def logStimulusSelected(self, trainingStimulus: TrainingStimulus):
        self.logger.info(f"Stimulus selected, file path: {trainingStimulus.filePath}, stimulus category: {trainingStimulus.stimulusCategory}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Q:
            self.closeApp()
        super().keyPressEvent(event)

    def closeApp(self):
        QTimer.singleShot(0, QCoreApplication.instance().quit)
