from PySide6.QtCore import QCoreApplication, Signal
from Framework.TrainingStimulus import TrainingStimulus
from Framework.ImageStimulusDisplay import ImageStimulusDisplay
from pynput.keyboard import Listener

class KeyboardInputImage(ImageStimulusDisplay):
    keyPressed = Signal()

    def __init__(self, trainingImage: TrainingStimulus, selected, shortcut, imageSize=None, parent=None):
        super().__init__(trainingImage, imageSize, parent)
        self.selected = selected
        self.shortcut = shortcut
        self.keyPressed.connect(self.stimulusSelected)

        self._listener = Listener(on_press=self._on_press)
        self._listener.start()
        QCoreApplication.instance().aboutToQuit.connect(self._listener.stop)

    def _on_press(self, key):
        try:
            if key.char == self.shortcut:
                self.keyPressed.emit()
        except AttributeError:
            return

    def stimulusSelected(self):
        if self.trainingImage is not None:
            self.selected(self.trainingImage)
