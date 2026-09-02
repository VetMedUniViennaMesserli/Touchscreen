/**
 * CSV upload receiver for the Rule Learning website (docs/index.html).
 *
 * The page POSTs { filename, content } as JSON text (see uploadToGDrive()
 * in docs/index.html — it uses mode:'no-cors' with no Content-Type header
 * to avoid a CORS preflight, so the body must be read via e.postData.contents
 * rather than e.parameter).
 *
 * The page re-uploads the same filename repeatedly (after every session end,
 * and again at experiment completion) with the growing accumulated CSV, so
 * this script overwrites the existing file of that name in the folder
 * instead of creating duplicates.
 *
 * Deploy as a Web App (Execute as: Me, Who has access: Anyone), then paste
 * the deployment URL into GDRIVE_URL in docs/index.html.
 *
 * ── How to verify this script works, step by step ──
 * 1. Select "manualTest" in the function dropdown at the top of the editor
 *    (next to the Run/Debug buttons) and click Run.
 * 2. First time only: Google will ask you to authorize the script — click
 *    through "Review permissions" → pick your account → "Advanced" →
 *    "Go to ... (unsafe)" → "Allow". This grants the script Drive access.
 * 3. Check the "Execution log" at the bottom — it should print "manualTest
 *    OK". Then check the Drive folder for a file named _manual_test.csv.
 *    If this step works, Drive access and the folder ID are both correct,
 *    independent of any deployment/URL issues.
 * 4. Only after step 3 succeeds, worry about the deployed Web app URL
 *    (Deploy > Manage deployments) — open its GET link directly in your
 *    browser; it should show the plain text "Upload endpoint is running."
 */

const FOLDER_ID = '197KjpSBQWPfbQDrszbU8uj0oZjab974G';

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    saveCsv(body.filename, body.content);
    return jsonResponse({ ok: true });
  } catch (err) {
    return jsonResponse({ ok: false, error: String(err) });
  }
}

function doGet(e) {
  return ContentService.createTextOutput('Upload endpoint is running.');
}

function saveCsv(filename, content) {
  const folder = DriveApp.getFolderById(FOLDER_ID);
  const existing = folder.getFilesByName(filename);

  if (existing.hasNext()) {
    existing.next().setContent(content);
  } else {
    folder.createFile(filename, content, MimeType.CSV);
  }
}

function manualTest() {
  saveCsv('_manual_test.csv', 'a,b\n1,2\n');
  Logger.log('manualTest OK');
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
