"""
Second-order rule learning (port of ariane/rule.learning.10.py).

Two rules, each cued by the background colour:
  RuleA (lightgrey bg) — the TARGET COLOUR stimulus is rewarded.
  RuleB (purple bg)    — the TARGET SHAPE  stimulus is rewarded.

Phases:  RuleA → RuleB → Alternate → Mixed  (or B→A→… depending on counterbalance).
Each phase runs sessions of N_TRIALS until the session criterion is met.
"""

import csv
import os
import random
import sys

from Framework.ShapeButton import ShapeButton
from Framework.TrainingWindow import TrainingWindow
from Framework.SessionConfig import SessionConfig
from Framework.paths import get_app_root, get_log_root

from PySide6.QtWidgets import (QApplication, QDialog, QFormLayout, QFrame,
                                QGroupBox, QGridLayout, QHBoxLayout, QLabel,
                                QPushButton, QStackedWidget, QVBoxLayout, QWidget)
from PySide6.QtCore import Qt, QDateTime, QTimer, Signal
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
# Setup dialog
# ---------------------------------------------------------------------------

_BG_COLORS = {
    'lightgrey': QColor(180, 180, 180),
    'purple':    QColor(128,   0, 128),
}

_BTN_H   = 64
_FONT_MD = 14
_FONT_LG = 18


def _individuals_csv_path():
    return os.path.join(get_log_root(), 'individuals.csv')


def generate_individuals_csv():
    """Create individuals.csv with 10 balanced individuals if it does not exist."""
    path = _individuals_csv_path()
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rules = ['RuleA'] * 5 + ['RuleB'] * 5
    bgs   = ['lightgrey', 'purple'] * 5
    stims = ['black triangle', 'white triangle', 'black circle', 'white circle',
             'black triangle', 'white circle',   'white triangle','black circle',
             'black triangle', 'white triangle']
    random.shuffle(rules); random.shuffle(bgs)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['individual_id', 'first_rule', 'bg_rule_a', 'target_stim', 'notes'])
        for i in range(10):
            writer.writerow([f'S{i+1:02d}', rules[i], bgs[i], stims[i], ''])


def _read_individuals():
    path = _individuals_csv_path()
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


class _ToggleGroup(QWidget):
    """Row of mutually-exclusive checkable buttons."""
    valueChanged = Signal(str)

    def __init__(self, options, selected=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        self._buttons = {}
        self._value   = selected or options[0]
        for opt in options:
            self._addButton(opt)
        self._apply(self._value)

    def _addButton(self, opt):
        btn = QPushButton(opt)
        btn.setCheckable(True)
        btn.setMinimumHeight(_BTN_H)
        f = btn.font(); f.setPointSize(_FONT_MD); btn.setFont(f)
        btn.clicked.connect(lambda _, o=opt: self._apply(o))
        self.layout().addWidget(btn)
        self._buttons[opt] = btn

    def _apply(self, option):
        for k, b in self._buttons.items():
            b.setChecked(k == option)
        self._value = option
        self.valueChanged.emit(option)

    def value(self):
        return self._value

    def setValue(self, option):
        if option in self._buttons:
            self._apply(option)

    def setOptions(self, options, keep_value=True):
        old = self._value if keep_value else None
        for b in self._buttons.values():
            self.layout().removeWidget(b)
            b.deleteLater()
        self._buttons.clear()
        self._value = None
        for opt in options:
            self._addButton(opt)
        self._apply(old if old in options else options[0])


class _NumberStepper(QWidget):
    """Touch-friendly +/- control over a discrete value list."""

    def __init__(self, options, default=None, parent=None):
        super().__init__(parent)
        self._options = list(options)
        self._idx     = self._options.index(default) if default in self._options else 0

        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self._btnM = QPushButton("−")
        self._lbl  = QLabel()
        self._btnP = QPushButton("+")

        for b in (self._btnM, self._btnP):
            b.setMinimumSize(64, _BTN_H)
            f = b.font(); f.setPointSize(22); b.setFont(f)

        self._lbl.setAlignment(Qt.AlignCenter)
        self._lbl.setMinimumWidth(90)
        f2 = self._lbl.font(); f2.setPointSize(_FONT_MD + 2); self._lbl.setFont(f2)

        layout.addWidget(self._btnM)
        layout.addWidget(self._lbl, 1)
        layout.addWidget(self._btnP)

        self._btnM.clicked.connect(self._dec)
        self._btnP.clicked.connect(self._inc)
        self._refresh()

    def _dec(self):
        if self._idx > 0:
            self._idx -= 1
            self._refresh()

    def _inc(self):
        if self._idx < len(self._options) - 1:
            self._idx += 1
            self._refresh()

    def _refresh(self):
        self._lbl.setText(str(self._options[self._idx]))
        self._btnM.setEnabled(self._idx > 0)
        self._btnP.setEnabled(self._idx < len(self._options) - 1)

    def value(self):
        return self._options[self._idx]


class RuleLearningSetupDialog(QDialog):
    """Full-screen two-page touchscreen dialog: individual grid → session parameters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rule Learning — Setup")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setGeometry(QApplication.primaryScreen().geometry())
        self._individual = None

        f = QFont(); f.setPointSize(13); self.setFont(f)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._buildIndividualPage())
        self._stack.addWidget(self._buildSetupPage())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._stack)

    # ── Page 0: individual grid (no scrolling) ─────────────────────────────

    def _buildIndividualPage(self):
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setSpacing(0)
        vbox.setContentsMargins(32, 28, 32, 28)

        # Header row: title + Cancel
        header = QHBoxLayout()
        title = QLabel("Select Individual")
        f = title.font(); f.setPointSize(22); f.setBold(True); title.setFont(f)
        cancelBtn = QPushButton("Cancel")
        cancelBtn.setMinimumHeight(52)
        cancelBtn.setMaximumWidth(140)
        cancelBtn.clicked.connect(self.reject)
        header.addWidget(title, 1)
        header.addWidget(cancelBtn)
        vbox.addLayout(header)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        vbox.addSpacing(12)
        vbox.addWidget(sep)
        vbox.addSpacing(16)

        # Individual grid — 2 columns, fills available space
        self._gridWidget = QWidget()
        self._gridLayout = QGridLayout(self._gridWidget)
        self._gridLayout.setSpacing(10)
        vbox.addWidget(self._gridWidget, 1)

        self._populateGrid()
        return page

    def _populateGrid(self):
        while self._gridLayout.count():
            item = self._gridLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        individuals = _read_individuals()
        if not individuals:
            lbl = QLabel("individuals.csv not found or empty.\nEdit the file and restart.")
            lbl.setWordWrap(True)
            self._gridLayout.addWidget(lbl, 0, 0)
            return

        for i, s in enumerate(individuals):
            btn = QPushButton(s['individual_id'])
            btn.setMinimumHeight(72)
            f = btn.font(); f.setPointSize(18); f.setBold(True); btn.setFont(f)
            btn.clicked.connect(lambda _, ind=s: self._onIndividualSelected(ind))
            self._gridLayout.addWidget(btn, i // 2, i % 2)

    def _onIndividualSelected(self, individual):
        self._individual = individual
        self._fillSetupPage(individual)
        self._stack.setCurrentIndex(1)

    # ── Page 1: session setup ───────────────────────────────────────────────

    def _buildSetupPage(self):
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setSpacing(12)
        vbox.setContentsMargins(32, 20, 32, 24)

        # Header row: Back + individual name
        header = QHBoxLayout()
        backBtn = QPushButton("← Back")
        backBtn.setMinimumHeight(52)
        backBtn.setMaximumWidth(140)
        f = backBtn.font(); f.setPointSize(13); backBtn.setFont(f)
        backBtn.clicked.connect(lambda: self._stack.setCurrentIndex(0))

        self._individualLabel = QLabel()
        f2 = self._individualLabel.font(); f2.setPointSize(20); f2.setBold(True)
        self._individualLabel.setFont(f2)

        header.addWidget(backBtn)
        header.addWidget(self._individualLabel, 1)
        vbox.addLayout(header)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        vbox.addWidget(sep)

        # Counterbalancing
        cbGrp = QGroupBox("Counterbalancing")
        cbForm = QFormLayout(cbGrp)
        cbForm.setSpacing(8)
        cbForm.setContentsMargins(12, 8, 12, 8)

        self._firstRule  = _ToggleGroup(['RuleA', 'RuleB'])
        self._bgA        = _ToggleGroup(['lightgrey', 'purple'])
        self._targetStim = _ToggleGroup(['black triangle', 'white triangle',
                                          'black circle',  'white circle'])
        cbForm.addRow("First rule:", self._firstRule)
        cbForm.addRow("Background (Rule A):", self._bgA)
        cbForm.addRow("Target stimulus (S+):", self._targetStim)
        vbox.addWidget(cbGrp)

        # Session
        sessGrp = QGroupBox("Session")
        sessForm = QFormLayout(sessGrp)
        sessForm.setSpacing(8)
        sessForm.setContentsMargins(12, 8, 12, 8)

        self._startAt = _ToggleGroup(['Beginning', 'RuleA', 'RuleB', 'AlternateA', 'Mixed'])
        self._nTrials = _NumberStepper([8, 16, 24, 32], default=24)
        sessForm.addRow("Start at phase:", self._startAt)
        sessForm.addRow("Trials / session:", self._nTrials)
        vbox.addWidget(sessGrp)

        self._firstRule.valueChanged.connect(self._updateStartAt)

        startBtn = QPushButton("▶  Start")
        startBtn.setMinimumHeight(72)
        f3 = startBtn.font(); f3.setPointSize(_FONT_LG); f3.setBold(True)
        startBtn.setFont(f3)
        startBtn.clicked.connect(self.accept)
        vbox.addWidget(startBtn)

        return page

    def _fillSetupPage(self, individual):
        self._individualLabel.setText(f"Individual: {individual['individual_id']}")
        first = individual.get('first_rule', 'RuleA')
        self._firstRule.setValue(first)
        self._bgA.setValue(individual.get('bg_rule_a', 'lightgrey'))
        self._targetStim.setValue(individual.get('target_stim', 'black triangle'))
        self._updateStartAt(first)

    def _updateStartAt(self, first_rule):
        opts = ['Beginning'] + (
            ['RuleA', 'RuleB', 'AlternateA', 'Mixed'] if first_rule == 'RuleA'
            else ['RuleB', 'RuleA', 'AlternateB', 'Mixed']
        )
        self._startAt.setOptions(opts)

    # ── Result ──────────────────────────────────────────────────────────────

    @property
    def settings(self):
        first_rule = self._firstRule.value()
        bg_a       = self._bgA.value()
        tgt_color, tgt_shape = self._targetStim.value().split()

        full_phases = (['RuleA', 'RuleB', 'AlternateA', 'Mixed'] if first_rule == 'RuleA'
                       else ['RuleB', 'RuleA', 'AlternateB', 'Mixed'])
        start_at = self._startAt.value()
        phases   = (full_phases if start_at == 'Beginning' or start_at not in full_phases
                    else full_phases[full_phases.index(start_at):])

        return {
            'individual_id': self._individual['individual_id'],
            'tgt_color':  tgt_color,
            'tgt_shape':  tgt_shape,
            'oth_color':  OPPOSITE[tgt_color],
            'oth_shape':  OPPOSITE[tgt_shape],
            'bg_rule_a':  bg_a,
            'phases':     phases,
            'n_trials':   self._nTrials.value(),
        }


# ---------------------------------------------------------------------------
# Training class
# ---------------------------------------------------------------------------

class RuleLearningTraining(TrainingWindow):
    def __init__(self, sessionConfig, tgt_shape, oth_shape,
                 tgt_color, oth_color, phase_order, n_trials=N_TRIALS,
                 bg_rule_a='lightgrey', individual_id='',
                 parent=None, sessionEndCallback=None):
        super().__init__(sessionConfig, parent, sessionEndCallback)

        self._individual_id  = individual_id
        self._rule_bg     = {
            'RuleA': _BG_COLORS[bg_rule_a],
            'RuleB': _BG_COLORS['purple' if bg_rule_a == 'lightgrey' else 'lightgrey'],
        }
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

        # Hide until ready — gives the audio backend time to warm up before
        # the first ER trial appears (animals respond very fast to the obvious stimulus).
        self.container.hide()
        QTimer.singleShot(500, self._beginPhase)

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

        if self._phase_idx == 0:
            self.logger.info(
                f"setup, individual={self._individual_id}, "
                f"tgt_shape={self._tgt_shape}, tgt_color={self._tgt_color}, "
                f"phases={self._phase_order}"
            )
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
        self.setBackgroundColor(self._rule_bg[first_rule])

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
        self.setBackgroundColor(self._rule_bg[tr['rule']])

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
    dlg = RuleLearningSetupDialog()
    if not dlg.exec():
        return None

    s = dlg.settings

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
        trainingName=f"Rule_Learning_{s['individual_id']}",
    )

    w = RuleLearningTraining(
        sessionConfig,
        tgt_shape=s['tgt_shape'], oth_shape=s['oth_shape'],
        tgt_color=s['tgt_color'], oth_color=s['oth_color'],
        phase_order=s['phases'],
        n_trials=s['n_trials'],
        bg_rule_a=s['bg_rule_a'],
        individual_id=s['individual_id'],
        sessionEndCallback=sessionEndCallback,
    )
    w.startFirstTrial()
    return w


def startApp():
    app = QApplication([])
    generate_individuals_csv()   # create individuals.csv with 10 individuals on first run
    w = createTouchscreenWindow()
    if w is None:
        sys.exit(0)
    w.showFullScreen()
    sys.exit(app.exec())


if __name__ == "__main__":
    startApp()
