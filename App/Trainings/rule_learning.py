"""
Second-order rule learning (port of ariane/rule.learning.10.py).

Two rules, each cued by the background colour:
  RuleA (lightgrey bg) — the TARGET COLOUR stimulus is rewarded.
  RuleB (purple bg)    — the TARGET SHAPE  stimulus is rewarded.

Phases:  RuleA → RuleB → Alternate → Mixed  (or B→A→… depending on counterbalance).
Each phase runs sessions of N_TRIALS until the session criterion is met.
"""

import os
import random
import sys

from Framework.ShapeButton import ShapeButton
from Framework.TrainingWindow import TrainingWindow
from Framework.SessionConfig import SessionConfig
from Framework.paths import get_app_root

from PySide6.QtWidgets import (QApplication, QHBoxLayout, QVBoxLayout,
                                QWidget, QLabel, QPushButton)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QColor, QFont, QShortcut, QKeySequence

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RULE_BG = {
    'RuleA': QColor(180, 180, 180),   # lightgrey
    'RuleB': QColor(128,   0, 128),   # purple
}

FEEDBACK_CORRECT = QColor(0,   180,   0)
FEEDBACK_WRONG   = QColor(200,   0,   0)
FEEDBACK_TIMEOUT = QColor(220, 200,   0)

FEEDBACK_MS   = 800     # feedback screen duration
TIMEOUT_MS    = 10_000  # max wait for response
MAX_CORR      = 5       # max correction attempts per trial
N_TRIALS      = 24      # trials per session
ER_REPS       = 2       # error-reduced trials = ER_REPS × 2 positions

OPPOSITE = {
    'black': 'white', 'white': 'black',
    'blue': 'yellow', 'yellow': 'blue',
    'triangle': 'circle', 'circle': 'triangle',
    'star': 'square',  'square': 'star',
}


# ---------------------------------------------------------------------------
# Trial builders (faithfully ported from PsychoPy script)
# ---------------------------------------------------------------------------

def _even(n):
    return n if n % 2 == 0 else n - 1


def build_ruleA(n, tgt_shape, oth_shape, tgt_color, oth_color):
    """RuleA: stimulus with tgt_color is always correct."""
    n = _even(n)
    sides  = (['left'] * (n // 2) + ['right'] * (n // 2))
    shapes = ([tgt_shape] * (n // 2) + [oth_shape] * (n // 2))
    random.shuffle(sides);  random.shuffle(shapes)
    trials = []
    for i in range(n):
        cs  = sides[i]
        ts  = shapes[i]
        os_ = oth_shape if ts == tgt_shape else tgt_shape
        if cs == 'left':
            ls, rs, lc, rc = ts, os_, tgt_color, oth_color
        else:
            ls, rs, lc, rc = os_, ts, oth_color, tgt_color
        trials.append({'rule': 'RuleA',
                        'left_shape': ls, 'left_color': lc,
                        'right_shape': rs, 'right_color': rc,
                        'correct_side': cs})
    return trials


def build_ruleB(n, tgt_shape, oth_shape, tgt_color, oth_color):
    """RuleB: stimulus with tgt_shape is always correct."""
    n = _even(n)
    sides  = (['left'] * (n // 2) + ['right'] * (n // 2))
    colors = ([tgt_color] * (n // 2) + [oth_color] * (n // 2))
    random.shuffle(sides);  random.shuffle(colors)
    trials = []
    for i in range(n):
        cs  = sides[i]
        tc  = colors[i]
        oc  = oth_color if tc == tgt_color else tgt_color
        if cs == 'left':
            ls, rs, lc, rc = tgt_shape, oth_shape, tc, oc
        else:
            ls, rs, lc, rc = oth_shape, tgt_shape, oc, tc
        trials.append({'rule': 'RuleB',
                        'left_shape': ls, 'left_color': lc,
                        'right_shape': rs, 'right_color': rc,
                        'correct_side': cs})
    return trials


def build_alternate(n, tgt_shape, oth_shape, tgt_color, oth_color, start='RuleA'):
    n = _even(n);  half = n // 2
    a = build_ruleA(half, tgt_shape, oth_shape, tgt_color, oth_color)
    b = build_ruleB(half, tgt_shape, oth_shape, tgt_color, oth_color)
    return a + b if start == 'RuleA' else b + a


def build_mixed(n, tgt_shape, oth_shape, tgt_color, oth_color):
    n = _even(n);  half = n // 2
    trials = (build_ruleA(half, tgt_shape, oth_shape, tgt_color, oth_color) +
              build_ruleB(half, tgt_shape, oth_shape, tgt_color, oth_color))
    random.shuffle(trials)
    return trials


def build_phase(phase, n, tgt_shape, oth_shape, tgt_color, oth_color):
    if 'RuleA' in phase:
        return build_ruleA(n, tgt_shape, oth_shape, tgt_color, oth_color)
    if 'RuleB' in phase:
        return build_ruleB(n, tgt_shape, oth_shape, tgt_color, oth_color)
    if 'AlternateA' in phase:
        return build_alternate(n, tgt_shape, oth_shape, tgt_color, oth_color, 'RuleA')
    if 'AlternateB' in phase:
        return build_alternate(n, tgt_shape, oth_shape, tgt_color, oth_color, 'RuleB')
    if 'Mixed' in phase:
        return build_mixed(n, tgt_shape, oth_shape, tgt_color, oth_color)
    return []


# ---------------------------------------------------------------------------
# Training class
# ---------------------------------------------------------------------------

class RuleLearningTraining(TrainingWindow):
    def __init__(self, sessionConfig, tgt_shape, oth_shape,
                 tgt_color, oth_color, phase_order, n_trials=N_TRIALS,
                 parent=None, sessionEndCallback=None):
        super().__init__(sessionConfig, parent, sessionEndCallback)

        self._tgt_shape   = tgt_shape
        self._oth_shape   = oth_shape
        self._tgt_color   = tgt_color
        self._oth_color   = oth_color
        self._phase_order = phase_order
        self._n_trials    = n_trials

        # session/phase state
        self._phase_idx      = 0
        self._session_count  = 0
        self._trials         = []
        self._trial_idx      = 0
        self._correction     = 0       # correction attempt number (0 = first)
        self._correct_t1     = 0       # correct count trial-type 1
        self._correct_t2     = 0       # correct count trial-type 2
        self._total_count    = 0       # across all phases
        self._current        = None    # current trial dict
        self._timeout_timer  = None
        self._resp_start_ms  = 0

        # error-reduced
        self._er_trials      = []
        self._er_idx         = 0
        self._in_er          = False

        self._overlay        = None

    # --- layout setup ---

    def startFirstTrial(self):
        layout = QHBoxLayout(self.container)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self._btnL = ShapeButton('circle', 'black', 200, self._onLeft)
        self._btnR = ShapeButton('circle', 'black', 200, self._onRight)
        layout.addWidget(self._btnL, alignment=Qt.AlignCenter)
        layout.addWidget(self._btnR, alignment=Qt.AlignCenter)

        scA = QShortcut(QKeySequence(Qt.Key_A), self)
        scA.activated.connect(lambda: self._keySelect('left'))
        scD = QShortcut(QKeySequence(Qt.Key_D), self)
        scD.activated.connect(lambda: self._keySelect('right'))

        self._beginPhase()

    # --- phase / session management ---

    def _beginPhase(self):
        if self._phase_idx >= len(self._phase_order):
            self.endSession()
            return

        phase = self._phase_order[self._phase_idx]
        self._trials      = build_phase(phase, self._n_trials,
                                        self._tgt_shape, self._oth_shape,
                                        self._tgt_color, self._oth_color)
        self._trial_idx   = 0
        self._correction  = 0
        self._correct_t1  = 0
        self._correct_t2  = 0
        self._session_count += 1
        self._in_er = True
        self._er_trials = self._buildERTrials()
        self._er_idx = 0

        self.logger.info(f"phase_start, phase={phase}, session={self._session_count}")
        self._nextTrial()

    def _buildERTrials(self):
        """ER_REPS repetitions of [left, right], shuffled."""
        pool = [{'correct_side': 'left'}, {'correct_side': 'right'}] * ER_REPS
        random.shuffle(pool)
        return pool

    def _nextTrial(self):
        if self._in_er:
            if self._er_idx < len(self._er_trials):
                self._showERTrial()
            else:
                self._in_er = False
                self._nextTrial()
            return

        if self._trial_idx >= len(self._trials):
            self._evaluateSession()
            return

        self._current   = self._trials[self._trial_idx]
        self._correction = 0
        self._showTrial()

    # --- error-reduced trials ---

    def _showERTrial(self):
        er = self._er_trials[self._er_idx]
        cs = er['correct_side']

        # background = first trial's rule background
        first_rule = self._trials[0]['rule'] if self._trials else 'RuleA'
        self.setBackgroundColor(RULE_BG[first_rule])

        self._btnL.setStimVisible(cs == 'left')
        self._btnR.setStimVisible(cs == 'right')
        if cs == 'left':
            self._btnL.shape = self._tgt_shape
            self._btnL.color = self._tgt_color
        else:
            self._btnR.shape = self._tgt_shape
            self._btnR.color = self._tgt_color
        self._btnL.update();  self._btnR.update()

        self._current = {'rule': first_rule, 'correct_side': cs,
                          'trial_type': 0,
                          'left_shape':  self._tgt_shape if cs == 'left'  else None,
                          'left_color':  self._tgt_color if cs == 'left'  else None,
                          'right_shape': self._tgt_shape if cs == 'right' else None,
                          'right_color': self._tgt_color if cs == 'right' else None}
        self._correction = 0
        self.container.show()
        self._startTimer()
        self.logTrialStart()

    # --- regular trials ---

    def _showTrial(self):
        tr = self._current
        self.setBackgroundColor(RULE_BG[tr['rule']])

        self._btnL.shape = tr['left_shape'];   self._btnL.color = tr['left_color']
        self._btnR.shape = tr['right_shape'];  self._btnR.color = tr['right_color']
        self._btnL.setStimVisible(True);       self._btnR.setStimVisible(True)
        self._btnL.update();                   self._btnR.update()
        self.container.show()
        self._startTimer()
        self.logTrialStart()

    def _startTimer(self):
        self._resp_start_ms = QDateTime.currentMSecsSinceEpoch()
        if self._timeout_timer:
            self._timeout_timer.stop()
        self._timeout_timer = self.startFunctionTimer(TIMEOUT_MS, self._onTimeout)

    # --- response handling ---

    def _onLeft(self, shape, color):
        self._respond('left', shape, color)

    def _onRight(self, shape, color):
        self._respond('right', shape, color)

    def _keySelect(self, side):
        if not self.container.isVisible():
            return
        btn = self._btnL if side == 'left' else self._btnR
        if btn.stim_visible:
            self._respond(side, btn.shape, btn.color)

    def _onTimeout(self):
        self._respond(None, None, None)

    def _respond(self, choice_side, choice_shape, choice_color):
        if self._timeout_timer:
            self._timeout_timer.stop()
            self._timeout_timer = None

        self.container.hide()

        tr      = self._current
        tgt     = tr['correct_side']
        timeout = choice_side is None
        correct = (not timeout) and (choice_side == tgt)
        latency = (QDateTime.currentMSecsSinceEpoch() - self._resp_start_ms) / 1000.0

        # trial type (1 = common S+ present, 2 = novel, 0 = ER)
        if self._in_er or tr.get('trial_type') == 0:
            trial_type = 0
        else:
            ts, tc = self._propsFor(tr, tgt)
            trial_type = 1 if (ts == self._tgt_shape and tc == self._tgt_color) else 2

        # score only first attempts (not corrections)
        if not self._in_er and self._correction == 0:
            if correct:
                if trial_type == 1: self._correct_t1 += 1
                else:               self._correct_t2 += 1

        self._total_count += 1
        self.logger.info(
            f"response, phase={self._phase_order[self._phase_idx]}, "
            f"session={self._session_count}, trial={self._trial_idx}, "
            f"rule={tr['rule']}, trial_type={trial_type}, "
            f"correct_side={tgt}, choice={choice_side}, correct={correct}, "
            f"latency={latency:.3f}, correction={self._correction}"
        )

        if timeout:
            self.failureSound.play()
            self.setBackgroundColor(FEEDBACK_TIMEOUT)
        elif correct:
            self.successSound.play()
            self.setBackgroundColor(FEEDBACK_CORRECT)
        else:
            self.failureSound.play()
            self.setBackgroundColor(FEEDBACK_WRONG)

        if correct or self._correction >= MAX_CORR - 1 or self._in_er:
            self.startFunctionTimer(FEEDBACK_MS, self._afterFeedback_advance)
        else:
            self._correction += 1
            self.startFunctionTimer(FEEDBACK_MS, self._afterFeedback_correct)

    def _afterFeedback_advance(self):
        if self._in_er:
            self._er_idx += 1
            self._nextTrial()
        else:
            self._trial_idx += 1
            self._nextTrial()

    def _afterFeedback_correct(self):
        self._showTrial()

    # --- session end / criterion ---

    def _evaluateSession(self):
        criterion = self._n_trials // 2 - 1
        met = self._correct_t1 >= criterion and self._correct_t2 >= criterion
        total = self._correct_t1 + self._correct_t2

        self.logger.info(
            f"session_end, phase={self._phase_order[self._phase_idx]}, "
            f"session={self._session_count}, "
            f"correct_t1={self._correct_t1}, correct_t2={self._correct_t2}, "
            f"criterion={criterion}, met={met}"
        )

        if met:
            self._phase_idx  += 1
            self._session_count = 0

        self._showSessionScreen(met, total)

    def _showSessionScreen(self, criterion_met, total_correct):
        self.setBackgroundColor(QColor(0, 0, 0))

        next_phase = (self._phase_order[self._phase_idx]
                      if self._phase_idx < len(self._phase_order) else 'Done')
        status = "Criterion reached!" if criterion_met else "Criterion not reached."
        outcome = f"Next: {next_phase}" if criterion_met else "Repeating session…"
        msg = f"Score: {total_correct} / {self._n_trials}\n\n{status}\n\n{outcome}"

        self._overlay = QWidget(self.view)
        self._overlay.setGeometry(self.view.rect())
        pal = self._overlay.palette()
        pal.setColor(self._overlay.backgroundRole(), QColor(0, 0, 0))
        self._overlay.setAutoFillBackground(True)
        self._overlay.setPalette(pal)

        vbox = QVBoxLayout(self._overlay)
        vbox.setAlignment(Qt.AlignCenter)

        lbl = QLabel(msg)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        f = QFont();  f.setPointSize(22)
        lbl.setFont(f)
        lbl.setStyleSheet("color: white;")

        btn = QPushButton("Continue" if criterion_met else "Repeat")
        btn.setMinimumSize(220, 80)
        f2 = QFont();  f2.setPointSize(20)
        btn.setFont(f2)
        btn.clicked.connect(self._dismissSessionScreen)

        vbox.addWidget(lbl)
        vbox.addSpacing(40)
        vbox.addWidget(btn, alignment=Qt.AlignCenter)

        self._overlay.show()
        self._overlay.raise_()

    def _dismissSessionScreen(self):
        self._overlay.hide()
        self._overlay.deleteLater()
        self._overlay = None

        if self._phase_idx >= len(self._phase_order):
            self.endSession()
        else:
            self._beginPhase()

    # --- helpers ---

    def _propsFor(self, trial, side):
        if side == 'left':
            return trial['left_shape'], trial['left_color']
        return trial['right_shape'], trial['right_color']

    # stub overrides required by TrainingWindow (our flow never calls these)
    def startNextTrial(self):
        self._nextTrial()

    def startCorrectionTrial(self):
        self._showTrial()


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def createTouchscreenWindow(sessionEndCallback=None):
    # Random counterbalancing
    tgt_color = random.choice(['black', 'white'])
    tgt_shape = random.choice(['triangle', 'circle'])
    oth_color = OPPOSITE[tgt_color]
    oth_shape = OPPOSITE[tgt_shape]
    first     = random.choice(['RuleA', 'RuleB'])

    phases = (['RuleA', 'RuleB', 'AlternateA', 'Mixed'] if first == 'RuleA'
              else ['RuleB', 'RuleA', 'AlternateB', 'Mixed'])

    sessionConfig = SessionConfig(
        interTrialInterval=500,
        errorScreenDuration=FEEDBACK_MS,
        correctionTrialInterTrialInterval=0,
        numberOfTrials=99999,       # managed internally
        correctionTrialsActive=False,
        backgroundColor=QColor(0, 0, 0),
        errorScreenColor=QColor(200, 0, 0),
        successSoundFilePath=os.path.join(get_app_root(), "SoundEffects", "600hz.wav"),
        failureSoundFilePath=os.path.join(get_app_root(), "SoundEffects", "200hz.wav"),
        cursorVisible=True,
        trainingName="Rule Learning",
    )

    w = RuleLearningTraining(
        sessionConfig,
        tgt_shape=tgt_shape, oth_shape=oth_shape,
        tgt_color=tgt_color, oth_color=oth_color,
        phase_order=phases,
        n_trials=N_TRIALS,
        sessionEndCallback=sessionEndCallback,
    )
    w.startFirstTrial()
    return w


def startApp():
    app = QApplication([])
    w = createTouchscreenWindow()
    w.showFullScreen()
    sys.exit(app.exec())


if __name__ == "__main__":
    startApp()
