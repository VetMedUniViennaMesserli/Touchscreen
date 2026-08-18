/**
 * Test-group / counterbalance assignment tracker for the Rule Learning
 * website (docs/index.html). Deployed separately from the existing CSV
 * upload script — this one only hands out and records assignments.
 *
 * Sheet layout (create a sheet named "Assignments" with this header row):
 *   timestamp | id_code | test_group | condition_nr
 *
 * Deploy as a Web App (Execute as: Me, Who has access: Anyone), then paste
 * the deployment URL into ASSIGN_URL in docs/index.html.
 *
 * Behaviour:
 *  - Same id_code requested twice returns the SAME assignment (idempotent),
 *    so reloading the page mid-session doesn't draw a new one.
 *  - test_group alternates toward whichever group has fewer assignments so far.
 *  - condition_nr cycles through all 64 counterbalance conditions per test
 *    group before any condition repeats for that group.
 */

const SHEET_NAME = 'Assignments';
const N_CONDITIONS = 64;

function doGet(e) {
  const action = e.parameter.action;
  const id = (e.parameter.id || '').trim();

  if (action !== 'assign' || !id) {
    return jsonResponse({ error: 'bad request' });
  }

  const sheet = getSheet_();
  const rows = sheet.getDataRange().getValues().slice(1); // drop header

  const existing = rows.find(r => String(r[1]) === id);
  if (existing) {
    return jsonResponse({ test_group: existing[2], nr: existing[3] });
  }

  const g1Count = rows.filter(r => r[2] === 'group1').length;
  const g2Count = rows.filter(r => r[2] === 'group2').length;
  const testGroup = g1Count <= g2Count ? 'group1' : 'group2';

  const usedForGroup = rows.filter(r => r[2] === testGroup).map(r => Number(r[3]));
  let remaining = [];
  for (let n = 1; n <= N_CONDITIONS; n++) if (!usedForGroup.includes(n)) remaining.push(n);
  if (remaining.length === 0) {
    // every condition used at least once for this group — start a new cycle
    for (let n = 1; n <= N_CONDITIONS; n++) remaining.push(n);
  }
  const nr = remaining[Math.floor(Math.random() * remaining.length)];

  sheet.appendRow([new Date(), id, testGroup, nr]);

  return jsonResponse({ test_group: testGroup, nr: nr });
}

function getSheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(['timestamp', 'id_code', 'test_group', 'condition_nr']);
  }
  return sheet;
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
