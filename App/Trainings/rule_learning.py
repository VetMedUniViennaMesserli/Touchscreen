"""
Second-order rule learning (rule_learning.py).

Two geometric shapes are shown side by side.  The background signals the active rule:
  RuleA (lightgrey bg) — the TARGET COLOUR stimulus is rewarded.
  RuleB (striped bg)   — the TARGET SHAPE  stimulus is rewarded.

Phases: PreTraining → RuleA → RuleB → Alternate → Mixed → AlternatingTransfer → MixedTransfer
"""

import csv
import os
import random
import sys
from datetime import datetime

from Framework.ShapeButton import ShapeButton
from Framework.TrainingWindow import TrainingWindow
from Framework.SessionConfig import SessionConfig
from Framework.paths import get_app_root, get_log_root

from PySide6.QtWidgets import (QApplication, QDialog, QFormLayout, QFrame,
                                QGroupBox, QGridLayout, QHBoxLayout, QLabel,
                                QPushButton, QStackedWidget, QVBoxLayout, QWidget)
from PySide6.QtCore import Qt, QDateTime, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QShortcut, QKeySequence, QPainter, QPen

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FEEDBACK_WRONG   = QColor(200,   0,   0)
FEEDBACK_TIMEOUT = QColor(220, 200,   0)
FEEDBACK_MS      = 800

TIMEOUT_MS   = 180_000   # 3 minutes
MAX_CORR     = 5
N_TRIALS     = 24
ER_REPS      = 2         # ER_REPS × 2 = 4 errorless trials per session

PRETRAIN_TRIALS    = 12
PRETRAIN_CRITERION = 10
PRETRAIN_CONSEC    = 2   # consecutive sessions meeting criterion to advance

OPPOSITE = {
    'black': 'white', 'white': 'black',
    'blue': 'yellow', 'yellow': 'blue',
    'triangle': 'circle', 'circle': 'triangle',
    'star': 'square', 'square': 'star',
}

_STRIPE_COLOR1 = QColor(100,  0, 100)
_STRIPE_COLOR2 = QColor(160, 40, 160)
_STRIPE_WIDTH  = 24
_STRIPE_STEP   = 48

_BTN_H   = 64
_FONT_MD = 14
_FONT_LG = 18


# ---------------------------------------------------------------------------
# Striped background overlay
# ---------------------------------------------------------------------------

class _StripeWidget(QWidget):
    """Full-coverage diagonal stripe overlay; transparent to mouse events."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, _STRIPE_COLOR1)
        pen = QPen(_STRIPE_COLOR2, _STRIPE_WIDTH)
        p.setPen(pen)
        for x in range(-h, w + h, _STRIPE_STEP):
            p.drawLine(x, 0, x + h, h)


# ---------------------------------------------------------------------------
# Screen helpers
# ---------------------------------------------------------------------------

def _secondary_screen():
    primary = QApplication.primaryScreen()
    for s in QApplication.screens():
        if s is not primary:
            return s
    return None


def _screen_geometry(screen=None):
    s = screen or QApplication.primaryScreen()
    return s.geometry()


# ---------------------------------------------------------------------------
# Trial builders
# ---------------------------------------------------------------------------

def _even(n):
    return n if n % 2 == 0 else n - 1


def build_ruleA(n, tgt_shape, oth_shape, tgt_color, oth_color):
    """RuleA: tgt_color side is always rewarded."""
    n = _even(n)
    sides  = ['left'] * (n // 2) + ['right'] * (n // 2)
    shapes = [tgt_shape] * (n // 2) + [oth_shape] * (n // 2)
    random.shuffle(sides); random.shuffle(shapes)
    trials = []
    for i in range(n):
        cs  = sides[i]
        ts  = shapes[i]
        os_ = oth_shape if ts == tgt_shape else tgt_shape
        if cs == 'left':
            ls, rs, lc, rc = ts, os_, tgt_color, oth_color
        else:
            ls, rs, lc, rc = os_, ts, oth_color, tgt_color
        trials.append({'rule': 'RuleA', 'left_shape': ls, 'left_color': lc,
                        'right_shape': rs, 'right_color': rc, 'correct_side': cs})
    return trials


def build_ruleB(n, tgt_shape, oth_shape, tgt_color, oth_color):
    """RuleB: tgt_shape side is always rewarded."""
    n = _even(n)
    sides  = ['left'] * (n // 2) + ['right'] * (n // 2)
    colors = [tgt_color] * (n // 2) + [oth_color] * (n // 2)
    random.shuffle(sides); random.shuffle(colors)
    trials = []
    for i in range(n):
        cs  = sides[i]
        tc  = colors[i]
        oc  = oth_color if tc == tgt_color else tgt_color
        if cs == 'left':
            ls, rs, lc, rc = tgt_shape, oth_shape, tc, oc
        else:
            ls, rs, lc, rc = oth_shape, tgt_shape, oc, tc
        trials.append({'rule': 'RuleB', 'left_shape': ls, 'left_color': lc,
                        'right_shape': rs, 'right_color': rc, 'correct_side': cs})
    return trials


def _enforce_no_repeat(trials):
    """Shuffle until no two consecutive trials have the same stimulus layout."""
    result = list(trials)
    for _ in range(1000):
        ok = all(
            not (result[i-1]['left_shape'] == result[i]['left_shape'] and
                 result[i-1]['left_color'] == result[i]['left_color'] and
                 result[i-1]['right_shape'] == result[i]['right_shape'] and
                 result[i-1]['right_color'] == result[i]['right_color'])
            for i in range(1, len(result))
        )
        if ok:
            return result
        random.shuffle(result)
    return result


def _enforce_max_side_streak(trials, max_streak=2):
    """Shuffle until S+ doesn't stay on the same side for more than max_streak trials."""
    result = list(trials)
    for _ in range(1000):
        streak = 1
        ok = True
        for i in range(1, len(result)):
            if result[i]['correct_side'] == result[i-1]['correct_side']:
                streak += 1
                if streak > max_streak:
                    ok = False
                    break
            else:
                streak = 1
        if ok:
            return result
        random.shuffle(result)
    return result


def _enforce_max_rule_streak(trials, max_streak=3):
    """Shuffle until no more than max_streak consecutive trials share the same rule."""
    result = list(trials)
    for _ in range(1000):
        streak = 1
        ok = True
        for i in range(1, len(result)):
            if result[i]['rule'] == result[i-1]['rule']:
                streak += 1
                if streak > max_streak:
                    ok = False
                    break
            else:
                streak = 1
        if ok:
            return result
        random.shuffle(result)
    return result


def _move_type1_first(trials, tgt_shape, tgt_color):
    """Ensure the first trial has the common S+ present (type-1 trial)."""
    def is_type1(t):
        return ((t.get('left_shape') == tgt_shape and t.get('left_color') == tgt_color) or
                (t.get('right_shape') == tgt_shape and t.get('right_color') == tgt_color))
    for i, t in enumerate(trials):
        if is_type1(t):
            if i != 0:
                trials[0], trials[i] = trials[i], trials[0]
            break
    return trials


def build_alternate(n, tgt_shape, oth_shape, tgt_color, oth_color, start='RuleA'):
    n = _even(n); half = n // 2
    a = build_ruleA(half, tgt_shape, oth_shape, tgt_color, oth_color)
    b = build_ruleB(half, tgt_shape, oth_shape, tgt_color, oth_color)
    trials = a + b if start == 'RuleA' else b + a
    trials = _enforce_no_repeat(trials)
    trials = _enforce_max_side_streak(trials, 2)
    return trials


def build_mixed(n, tgt_shape, oth_shape, tgt_color, oth_color):
    n = _even(n); half = n // 2
    trials = (build_ruleA(half, tgt_shape, oth_shape, tgt_color, oth_color) +
              build_ruleB(half, tgt_shape, oth_shape, tgt_color, oth_color))
    random.shuffle(trials)
    trials = _enforce_max_rule_streak(trials, 3)
    return trials


def build_pretrain(n):
    """Pre-training: cross symbol shown on one side, semirandom L/R, max 2 consecutive same side."""
    n = _even(n)
    sides = ['left'] * (n // 2) + ['right'] * (n // 2)
    random.shuffle(sides)
    trials = [{'rule': 'PreTraining', 'correct_side': s,
               'left_shape': 'cross', 'left_color': 'white',
               'right_shape': 'cross', 'right_color': 'white'} for s in sides]
    return _enforce_max_side_streak(trials, 2)


def build_phase(phase, n, tgt_shape, oth_shape, tgt_color, oth_color,
                first_rule='RuleA',
                xfr_tgt_shape=None, xfr_oth_shape=None,
                xfr_tgt_color=None, xfr_oth_color=None):
    xts = xfr_tgt_shape or tgt_shape
    xos = xfr_oth_shape or oth_shape
    xtc = xfr_tgt_color or tgt_color
    xoc = xfr_oth_color or oth_color

    if phase == 'RuleA':               return build_ruleA(n, tgt_shape, oth_shape, tgt_color, oth_color)
    if phase == 'RuleB':               return build_ruleB(n, tgt_shape, oth_shape, tgt_color, oth_color)
    if phase == 'Alternate':           return build_alternate(n, tgt_shape, oth_shape, tgt_color, oth_color, first_rule)
    if phase == 'Mixed':               return build_mixed(n, tgt_shape, oth_shape, tgt_color, oth_color)
    if phase == 'AlternatingTransfer': return build_alternate(n, xts, xos, xtc, xoc, first_rule)
    if phase == 'MixedTransfer':       return build_mixed(n, xts, xos, xtc, xoc)
    return []


# ---------------------------------------------------------------------------
# individuals.csv helpers
# ---------------------------------------------------------------------------

def _individuals_csv_path():
    return os.path.join(get_log_root(), 'individuals.csv')


def generate_individuals_csv():
    path = _individuals_csv_path()
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rules = ['RuleA'] * 5 + ['RuleB'] * 5
    bgs   = ['lightgrey', 'striped'] * 5
    stims = ['black triangle', 'white triangle', 'black circle', 'white circle',
             'black triangle', 'white circle',   'white triangle', 'black circle',
             'black triangle', 'white triangle']
    xfrs  = ['blue star', 'yellow square'] * 5
    random.shuffle(rules); random.shuffle(bgs)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['individual_id', 'first_rule', 'bg_rule_a', 'target_stim', 'transfer_stim', 'notes'])
        for i in range(10):
            writer.writerow([f'S{i+1:02d}', rules[i], bgs[i], stims[i], xfrs[i % 2], ''])


def _read_individuals():
    path = _individuals_csv_path()
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Setup dialog widgets
# ---------------------------------------------------------------------------

class _ToggleGroup(QWidget):
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
            self._idx -= 1; self._refresh()

    def _inc(self):
        if self._idx < len(self._options) - 1:
            self._idx += 1; self._refresh()

    def _refresh(self):
        self._lbl.setText(str(self._options[self._idx]))
        self._btnM.setEnabled(self._idx > 0)
        self._btnP.setEnabled(self._idx < len(self._options) - 1)

    def value(self):
        return self._options[self._idx]


# ---------------------------------------------------------------------------
# Setup dialog
# ---------------------------------------------------------------------------

class RuleLearningSetupDialog(QDialog):
    """Full-screen two-page touchscreen setup dialog, shown on secondary screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rule Learning — Setup")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setGeometry(_screen_geometry(_secondary_screen()))
        self._individual = None

        f = QFont(); f.setPointSize(13); self.setFont(f)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._buildIndividualPage())
        self._stack.addWidget(self._buildSetupPage())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._stack)

    # ── Page 0: individual grid ────────────────────────────────────────────

    def _buildIndividualPage(self):
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setSpacing(0)
        vbox.setContentsMargins(32, 28, 32, 28)

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
        vbox.addSpacing(12); vbox.addWidget(sep); vbox.addSpacing(16)

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

    # ── Page 1: session setup ──────────────────────────────────────────────

    def _buildSetupPage(self):
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setSpacing(12)
        vbox.setContentsMargins(32, 20, 32, 24)

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

        cbGrp = QGroupBox("Counterbalancing")
        cbForm = QFormLayout(cbGrp)
        cbForm.setSpacing(8); cbForm.setContentsMargins(12, 8, 12, 8)

        self._firstRule    = _ToggleGroup(['RuleA', 'RuleB'])
        self._bgA          = _ToggleGroup(['lightgrey', 'striped'])
        self._targetStim   = _ToggleGroup(['black triangle', 'white triangle',
                                           'black circle',  'white circle'])
        self._transferStim = _ToggleGroup(['blue star', 'yellow square',
                                           'blue square', 'yellow star'])
        cbForm.addRow("First rule:", self._firstRule)
        cbForm.addRow("Background (Rule A):", self._bgA)
        cbForm.addRow("Target stimulus (S+):", self._targetStim)
        cbForm.addRow("Transfer target (S+):", self._transferStim)
        vbox.addWidget(cbGrp)

        sessGrp = QGroupBox("Session")
        sessForm = QFormLayout(sessGrp)
        sessForm.setSpacing(8); sessForm.setContentsMargins(12, 8, 12, 8)

        self._startAt = _ToggleGroup(['Beginning', 'PreTraining', 'RuleA', 'RuleB',
                                      'Alternate', 'Mixed', 'AlternatingTransfer', 'MixedTransfer'])
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
        bg = individual.get('bg_rule_a', 'lightgrey')
        if bg == 'purple':
            bg = 'striped'    # legacy value
        self._bgA.setValue(bg)
        self._targetStim.setValue(individual.get('target_stim', 'black triangle'))
        xfr = individual.get('transfer_stim', 'blue star')
        self._transferStim.setValue(xfr)
        self._updateStartAt(first)

    def _updateStartAt(self, first_rule):
        rule_seq = (['RuleA', 'RuleB'] if first_rule == 'RuleA' else ['RuleB', 'RuleA'])
        opts = ['Beginning', 'PreTraining'] + rule_seq + ['Alternate', 'Mixed',
                                                           'AlternatingTransfer', 'MixedTransfer']
        self._startAt.setOptions(opts)

    # ── Result ─────────────────────────────────────────────────────────────

    @property
    def settings(self):
        first_rule = self._firstRule.value()
        bg_a       = self._bgA.value()
        tgt_color, tgt_shape = self._targetStim.value().split()
        xfr_color, xfr_shape = self._transferStim.value().split()

        rule_seq   = ['RuleA', 'RuleB'] if first_rule == 'RuleA' else ['RuleB', 'RuleA']
        full_phases = ['PreTraining'] + rule_seq + ['Alternate', 'Mixed',
                                                     'AlternatingTransfer', 'MixedTransfer']
        start_at = self._startAt.value()
        if start_at in ('Beginning', 'PreTraining') or start_at not in full_phases:
            phases = full_phases
        else:
            phases = full_phases[full_phases.index(start_at):]

        return {
            'individual_id':  self._individual['individual_id'],
            'first_rule':     first_rule,
            'tgt_color':      tgt_color,
            'tgt_shape':      tgt_shape,
            'oth_color':      OPPOSITE[tgt_color],
            'oth_shape':      OPPOSITE[tgt_shape],
            'xfr_tgt_color':  xfr_color,
            'xfr_tgt_shape':  xfr_shape,
            'xfr_oth_color':  OPPOSITE[xfr_color],
            'xfr_oth_shape':  OPPOSITE[xfr_shape],
            'bg_rule_a':      bg_a,
            'phases':         phases,
            'n_trials':       self._nTrials.value(),
        }


# ---------------------------------------------------------------------------
# Session-end dialog (shown on secondary screen so pigs can't interact)
# ---------------------------------------------------------------------------

class _SessionEndDialog(QDialog):
    def __init__(self, message, criterion_met, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setGeometry(_screen_geometry(_secondary_screen()))
        self._exit_requested = False

        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(0, 0, 0))
        self.setAutoFillBackground(True)
        self.setPalette(pal)

        vbox = QVBoxLayout(self)
        vbox.setAlignment(Qt.AlignCenter)
        vbox.setSpacing(40)

        lbl = QLabel(message)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        f = QFont(); f.setPointSize(22); lbl.setFont(f)
        lbl.setStyleSheet("color: white;")
        vbox.addWidget(lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(30)

        contBtn = QPushButton("Continue" if criterion_met else "Repeat")
        contBtn.setMinimumSize(220, 80)
        f2 = QFont(); f2.setPointSize(20); contBtn.setFont(f2)
        contBtn.clicked.connect(self.accept)
        btn_row.addWidget(contBtn)

        exitBtn = QPushButton("Exit")
        exitBtn.setMinimumSize(220, 80)
        f3 = QFont(); f3.setPointSize(20); exitBtn.setFont(f3)
        exitBtn.setStyleSheet("background: #880000; color: white;")
        exitBtn.clicked.connect(self._onExit)
        btn_row.addWidget(exitBtn)

        vbox.addLayout(btn_row)

    def _onExit(self):
        self._exit_requested = True
        self.accept()

    @property
    def exit_requested(self):
        return self._exit_requested


# ---------------------------------------------------------------------------
# CSV session log
# ---------------------------------------------------------------------------

_CSV_COLUMNS = [
    'subjectID', 'date', 'time', 'phase', 'phase_count', 'session_count',
    'trial_count', 'target_color', 'target_shape', 'bg_shown', 'rule',
    'left_shape', 'left_color', 'right_shape', 'right_color',
    'commonSp', 'left_stim', 'right_stim', 'trial_type',
    'target_side', 'choice_side', 'reward_score',
    'choice_shape', 'choice_color', 'choice_latency', 'correction_trial',
]


class _CsvLog:
    def __init__(self, individual_id):
        now = datetime.now()
        fname = (f"Rule_Learning_{individual_id}_"
                 f"{now.strftime('%Y-%m-%d')}_{now.strftime('%H-%M-%S')}.csv")
        log_dir = os.path.join(get_log_root(), 'SessionLogs',
                               f'Rule_Learning_{individual_id}')
        os.makedirs(log_dir, exist_ok=True)
        self._f = open(os.path.join(log_dir, fname), 'w', newline='', encoding='utf-8')
        self._w = csv.DictWriter(self._f, fieldnames=_CSV_COLUMNS)
        self._w.writeheader()
        self._f.flush()

    def write(self, **kwargs):
        self._w.writerow({k: kwargs.get(k, '') for k in _CSV_COLUMNS})
        self._f.flush()

    def close(self):
        self._f.close()


# ---------------------------------------------------------------------------
# Training class
# ---------------------------------------------------------------------------

class RuleLearningTraining(TrainingWindow):
    def __init__(self, sessionConfig,
                 tgt_shape, oth_shape, tgt_color, oth_color,
                 xfr_tgt_shape, xfr_oth_shape, xfr_tgt_color, xfr_oth_color,
                 first_rule, phase_order, n_trials=N_TRIALS,
                 bg_rule_a='lightgrey', individual_id='',
                 parent=None, sessionEndCallback=None):
        super().__init__(sessionConfig, parent, sessionEndCallback)

        self._individual_id  = individual_id
        self._first_rule     = first_rule
        self._tgt_shape      = tgt_shape
        self._oth_shape      = oth_shape
        self._tgt_color      = tgt_color
        self._oth_color      = oth_color
        self._xfr_tgt_shape  = xfr_tgt_shape
        self._xfr_oth_shape  = xfr_oth_shape
        self._xfr_tgt_color  = xfr_tgt_color
        self._xfr_oth_color  = xfr_oth_color
        self._phase_order    = phase_order
        self._n_trials       = n_trials

        bg_b = 'striped' if bg_rule_a == 'lightgrey' else 'lightgrey'
        self._rule_bg = {'RuleA': bg_rule_a, 'RuleB': bg_b}

        # Phase/session state
        self._phase_idx          = 0
        self._phase_session_count = 0    # sessions within current phase
        self._total_session_count = 0    # across all phases
        self._pretrain_consec    = 0     # consecutive pre-training sessions meeting criterion

        # Trial state
        self._trials       = []
        self._trial_idx    = 0
        self._trial_count  = 0    # 1-based within session; corrections don't increment
        self._correction   = 0
        self._correct_t1   = 0
        self._correct_t2   = 0
        self._pretrain_correct = 0
        self._current      = None
        self._timeout_timer = None
        self._resp_start_ms = 0

        # ER trials
        self._er_trials = []
        self._er_idx    = 0
        self._in_er     = False

        self._csv       = _CsvLog(individual_id)
        self._stripe_bg = None    # created in startFirstTrial

    # ── layout ──────────────────────────────────────────────────────────────

    def startFirstTrial(self):
        layout = QHBoxLayout(self.container)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self._btnL = ShapeButton('circle', 'black', 300, self._onLeft)
        self._btnR = ShapeButton('circle', 'black', 300, self._onRight)
        layout.addWidget(self._btnL, alignment=Qt.AlignCenter)
        layout.addWidget(self._btnR, alignment=Qt.AlignCenter)

        self._stripe_bg = _StripeWidget(self.view)
        self._stripe_bg.setGeometry(self.view.rect())
        self._stripe_bg.lower()

        scA = QShortcut(QKeySequence(Qt.Key_A), self)
        scA.activated.connect(lambda: self._keySelect('left'))
        scD = QShortcut(QKeySequence(Qt.Key_D), self)
        scD.activated.connect(lambda: self._keySelect('right'))

        self.container.hide()
        QTimer.singleShot(500, self._beginPhase)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._stripe_bg:
            self._stripe_bg.setGeometry(self.view.rect())

    # ── background ──────────────────────────────────────────────────────────

    def _setRuleBg(self, name):
        """Set background by name: 'lightgrey', 'striped', or 'black'."""
        if name == 'striped':
            self.setBackgroundColor(QColor(100, 0, 100))
            if self._stripe_bg:
                self._stripe_bg.setGeometry(self.view.rect())
                self._stripe_bg.show()
                self._stripe_bg.lower()  # must stay behind the container
        else:
            if self._stripe_bg:
                self._stripe_bg.hide()
            if name == 'lightgrey':
                self.setBackgroundColor(QColor(180, 180, 180))
            else:
                self.setBackgroundColor(QColor(0, 0, 0))

    def _clearFeedbackBg(self):
        if self._stripe_bg:
            self._stripe_bg.hide()

    # ── phase / session management ───────────────────────────────────────────

    def _currentPhase(self):
        if self._phase_idx < len(self._phase_order):
            return self._phase_order[self._phase_idx]
        return None

    def _isTransferPhase(self, phase=None):
        return 'Transfer' in (phase or self._currentPhase() or '')

    def _currentStimuli(self):
        """(tgt_shape, oth_shape, tgt_color, oth_color) for the active phase."""
        if self._isTransferPhase():
            return self._xfr_tgt_shape, self._xfr_oth_shape, self._xfr_tgt_color, self._xfr_oth_color
        return self._tgt_shape, self._oth_shape, self._tgt_color, self._oth_color

    def _beginPhase(self):
        phase = self._currentPhase()
        if phase is None:
            self.endSession()
            return

        self._phase_session_count += 1
        self._total_session_count += 1
        self._trial_idx            = 0
        self._trial_count          = 0
        self._correction           = 0
        self._correct_t1           = 0
        self._correct_t2           = 0
        self._pretrain_correct     = 0

        if phase == 'PreTraining':
            self._trials  = build_pretrain(PRETRAIN_TRIALS)
            self._in_er   = False
            self._er_trials = []
        else:
            ts, os_, tc, oc = self._currentStimuli()
            self._trials = build_phase(
                phase, self._n_trials, ts, os_, tc, oc,
                first_rule=self._first_rule,
                xfr_tgt_shape=self._xfr_tgt_shape, xfr_oth_shape=self._xfr_oth_shape,
                xfr_tgt_color=self._xfr_tgt_color, xfr_oth_color=self._xfr_oth_color,
            )
            # Alternate/Mixed: first regular trial must have common S+ (type-1)
            if phase in ('Alternate', 'AlternatingTransfer', 'Mixed', 'MixedTransfer'):
                ts2, _, tc2, _ = self._currentStimuli()
                self._trials = _move_type1_first(self._trials, ts2, tc2)
            self._in_er     = True
            self._er_trials = self._buildERTrials()

        self._er_idx = 0
        self._nextTrial()

    def _buildERTrials(self):
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

        self._current    = self._trials[self._trial_idx]
        self._correction = 0
        self._trial_count += 1
        self._showTrial()

    # ── error-reduced trials ─────────────────────────────────────────────────

    def _showERTrial(self):
        er  = self._er_trials[self._er_idx]
        cs  = er['correct_side']
        phase = self._currentPhase()

        # Transfer ER → black bg; training ER → rule bg of first trial
        if self._isTransferPhase(phase):
            self._setRuleBg('black')
            tgt_s = self._xfr_tgt_shape
            tgt_c = self._xfr_tgt_color
        else:
            first_rule = self._trials[0]['rule'] if self._trials else 'RuleA'
            self._setRuleBg(self._rule_bg[first_rule])
            tgt_s = self._tgt_shape
            tgt_c = self._tgt_color

        visible = self._btnL if cs == 'left' else self._btnR
        hidden  = self._btnR if cs == 'left' else self._btnL
        visible.shape = tgt_s; visible.color = tgt_c; visible.setStimVisible(True)
        hidden.setStimVisible(False)
        self._btnL.update(); self._btnR.update()

        rule = self._trials[0]['rule'] if self._trials else 'RuleA'
        self._current = {
            'rule': rule, 'correct_side': cs, 'trial_type': 0,
            'left_shape':  tgt_s if cs == 'left'  else None,
            'left_color':  tgt_c if cs == 'left'  else None,
            'right_shape': tgt_s if cs == 'right' else None,
            'right_color': tgt_c if cs == 'right' else None,
        }
        self._correction = 0
        self.container.show()
        self._startTimer()

    # ── regular trials ───────────────────────────────────────────────────────

    def _showTrial(self):
        tr    = self._current
        phase = self._currentPhase()

        if phase == 'PreTraining':
            self._clearFeedbackBg()
            self.setBackgroundColor(QColor(0, 0, 0))
            cs = tr['correct_side']
            self._btnL.shape = 'cross'; self._btnL.color = 'white'
            self._btnR.shape = 'cross'; self._btnR.color = 'white'
            self._btnL.setStimVisible(cs == 'left')
            self._btnR.setStimVisible(cs == 'right')
        else:
            self._setRuleBg(self._rule_bg[tr['rule']])
            self._btnL.shape = tr['left_shape'];  self._btnL.color = tr['left_color']
            self._btnR.shape = tr['right_shape']; self._btnR.color = tr['right_color']
            self._btnL.setStimVisible(True); self._btnR.setStimVisible(True)

        self._btnL.update(); self._btnR.update()
        self.container.show()
        self._startTimer()

    def _startTimer(self):
        self._resp_start_ms = QDateTime.currentMSecsSinceEpoch()
        if self._timeout_timer:
            self._timeout_timer.stop()
        self._timeout_timer = self.startFunctionTimer(TIMEOUT_MS, self._onTimeout)

    # ── response handling ────────────────────────────────────────────────────

    def _onLeft(self, shape, color):  self._respond('left', shape, color)
    def _onRight(self, shape, color): self._respond('right', shape, color)

    def _keySelect(self, side):
        if not self.container.isVisible():
            return
        btn = self._btnL if side == 'left' else self._btnR
        if btn.stim_visible:
            self._respond(side, btn.shape, btn.color)

    def _onTimeout(self): self._respond(None, None, None)

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
        phase   = self._currentPhase()

        # Determine trial type
        if self._in_er or tr.get('trial_type') == 0:
            trial_type = 0
        else:
            ts_cur, _, tc_cur, _ = self._currentStimuli()
            tgt_s, tgt_c = self._propsFor(tr, tgt)
            trial_type = 1 if (tgt_s == ts_cur and tgt_c == tc_cur) else 2

        # Score first attempt only (not corrections, not ER)
        if not self._in_er and self._correction == 0:
            if phase == 'PreTraining':
                if correct:
                    self._pretrain_correct += 1
            else:
                if correct:
                    if trial_type == 1: self._correct_t1 += 1
                    else:               self._correct_t2 += 1

        # Write CSV row for non-ER trials
        if not self._in_er:
            ts_cur, _, tc_cur, _ = self._currentStimuli()
            common_sp = f"{tc_cur} {ts_cur}"
            rule_key  = tr.get('rule', 'RuleA')
            bg_name   = self._rule_bg.get(rule_key, 'lightgrey') if phase != 'PreTraining' else 'black'
            bg_shown  = 'grey' if bg_name == 'lightgrey' else bg_name
            ls = f"{tr.get('left_color','none')} {tr.get('left_shape','none')}"
            rs = f"{tr.get('right_color','none')} {tr.get('right_shape','none')}"
            now = datetime.now()
            self._csv.write(
                subjectID=self._individual_id,
                date=now.strftime('%Y-%m-%d'),
                time=now.strftime('%H:%M:%S'),
                phase=phase,
                phase_count=self._phase_idx + 1,
                session_count=self._phase_session_count,
                trial_count=self._trial_count,
                target_color=self._tgt_color,
                target_shape=self._tgt_shape,
                bg_shown=bg_shown,
                rule=rule_key,
                left_shape=tr.get('left_shape', 'none'),
                left_color=tr.get('left_color', 'none'),
                right_shape=tr.get('right_shape', 'none'),
                right_color=tr.get('right_color', 'none'),
                commonSp=common_sp,
                left_stim=ls,
                right_stim=rs,
                trial_type=trial_type,
                target_side=tgt,
                choice_side=choice_side if choice_side else 'NA',
                reward_score=1 if correct else 0,
                choice_shape=choice_shape or 'NA',
                choice_color=choice_color or 'NA',
                choice_latency=f"{latency:.3f}",
                correction_trial=self._correction,
            )

        # Feedback
        self._clearFeedbackBg()
        if timeout:
            self.failureSound.play()
            self.setBackgroundColor(FEEDBACK_TIMEOUT)
            # Timeout always triggers correction (for both ER and regular trials)
            self._correction += 1
            self.startFunctionTimer(FEEDBACK_MS, self._afterFeedback_correct)
        elif correct:
            self.successSound.play()
            # No green screen — proceed immediately after a brief ITI
            self.startFunctionTimer(200, self._afterFeedback_advance)
        else:
            self.failureSound.play()
            self.setBackgroundColor(FEEDBACK_WRONG)
            if self._correction < MAX_CORR - 1:
                self._correction += 1
                self.startFunctionTimer(FEEDBACK_MS, self._afterFeedback_correct)
            else:
                self.startFunctionTimer(FEEDBACK_MS, self._afterFeedback_advance)

    def _afterFeedback_advance(self):
        if self._in_er:
            self._er_idx += 1
        else:
            self._trial_idx += 1
        self._nextTrial()

    def _afterFeedback_correct(self):
        if self._in_er:
            self._showERTrial()
        else:
            self._showTrial()

    # ── session end / criterion ──────────────────────────────────────────────

    def _evaluateSession(self):
        phase = self._currentPhase()

        if phase == 'PreTraining':
            met = self._pretrain_correct >= PRETRAIN_CRITERION
            if met:
                self._pretrain_consec += 1
            else:
                self._pretrain_consec = 0
            advance = self._pretrain_consec >= PRETRAIN_CONSEC
            total   = self._pretrain_correct
            n       = PRETRAIN_TRIALS
        else:
            criterion = self._n_trials // 2 - 1
            met = self._correct_t1 >= criterion and self._correct_t2 >= criterion
            advance = met
            total   = self._correct_t1 + self._correct_t2
            n       = self._n_trials

        if advance:
            self._phase_idx += 1
            self._phase_session_count = 0

        next_phase = (self._phase_order[self._phase_idx]
                      if self._phase_idx < len(self._phase_order) else 'Done')
        status  = "Criterion reached!" if met else "Criterion not reached."
        outcome = f"Next: {next_phase}" if advance else "Repeating session…"
        if phase == 'PreTraining' and met and not advance:
            outcome = f"({self._pretrain_consec}/{PRETRAIN_CONSEC} consecutive) — keep going!"
        msg = f"Score: {total} / {n}\n\n{status}\n\n{outcome}"

        self._showSessionScreen(msg, advance)

    def _showSessionScreen(self, message, criterion_met):
        dlg = _SessionEndDialog(message, criterion_met, parent=self)
        dlg.exec()
        if dlg.exit_requested:
            self._csv.close()
            self.endSession()
        elif self._phase_idx >= len(self._phase_order):
            self._csv.close()
            self.endSession()
        else:
            self._beginPhase()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _propsFor(self, trial, side):
        if side == 'left':
            return trial.get('left_shape'), trial.get('left_color')
        return trial.get('right_shape'), trial.get('right_color')

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
        numberOfTrials=99999,
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
        tgt_shape=s['tgt_shape'],     oth_shape=s['oth_shape'],
        tgt_color=s['tgt_color'],     oth_color=s['oth_color'],
        xfr_tgt_shape=s['xfr_tgt_shape'], xfr_oth_shape=s['xfr_oth_shape'],
        xfr_tgt_color=s['xfr_tgt_color'], xfr_oth_color=s['xfr_oth_color'],
        first_rule=s['first_rule'],
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
    generate_individuals_csv()
    w = createTouchscreenWindow()
    if w is None:
        sys.exit(0)
    w.showFullScreen()
    sys.exit(app.exec())


if __name__ == "__main__":
    startApp()
