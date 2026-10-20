/** Run against an isolated QA deployment with the supported browser tab API.
 * This is a browser regression helper, not evidence of real LLM inference.
 */
export async function runIntake(tab, baseURL, text) {
  await tab.goto(baseURL);
  await tab.playwright.getByLabel('Explain your situation', { exact: true }).fill(text);
  await tab.playwright.getByRole('button', { name: 'Understand My Situation', exact: true }).click();
  await tab.playwright.waitForURL(`${baseURL.replace(/\/$/, '')}/understand`);
  await tab.playwright.getByRole('heading', { name: 'Understand Your Situation', exact: true }).waitFor({ state: 'visible' });
  return await tab.playwright.domSnapshot();
}
export async function assertEmptyHome(tab, baseURL) {
  await tab.goto(baseURL);
  await tab.playwright.getByRole('button', { name: 'Understand My Situation', exact: true }).click();
  await tab.playwright.getByText('Please describe your situation or select an example before continuing.', {exact:true}).waitFor({state:'visible'});
  return await tab.playwright.domSnapshot();
}
export async function confirmVisibleFacts(tab) {
  while (await tab.playwright.getByRole('button', { name: 'Confirm', exact: true }).count()) {
    await tab.playwright.getByRole('button', { name: 'Confirm', exact: true }).first().click();
    await tab.playwright.domSnapshot();
  }
}
