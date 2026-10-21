/** Synthetic browser rechecks. Run through the supported CUA tab in cua_repl.
 * No network calls or application-state injection are used here.
 */
export async function runCase(tab, item, base = 'http://127.0.0.1:3002') {
  const record = {id:item.id, input:item.input, snapshots:[], answers:[]};
  const snapshot=async()=>{const value=await tab.getAXState({emit:false,disableDiffing:true});if(record.snapshots.at(-1)!==value)record.snapshots.push(value);return value;};
  const button=(name)=>tab.playwright.getByRole('button',{name,exact:true});
  const visible=async(locator, timeout=45000)=>{
    const deadline=Date.now()+timeout;
    while(Date.now()<deadline){
      if(await locator.count() && await locator.first().isVisible())return;
      await snapshot();
    }
    throw new Error('Expected control did not appear within '+timeout+'ms');
  };
  const route=async(suffix)=>{
    const deadline=Date.now()+45000;
    while(Date.now()<deadline){
      const state=await snapshot();
      if(state.split('\n')[0].includes(base+suffix+'"'))return;
    }
    throw new Error('Page navigation did not complete: '+suffix);
  };
  try {
    await tab.goto(base+'/');await snapshot();
    const input=tab.playwright.getByLabel('Explain your situation',{exact:true});
    await input.fill(item.input);await snapshot();
    await button('Understand My Situation').click();
    await route('/understand');await snapshot();
    if(item.issue==='OUT_OF_SCOPE') {
      await button('Outside motor-vehicle law / none of these').click();
      await tab.playwright.getByText('Outside supported scope',{exact:true}).waitFor({state:'visible'});
      const state=await snapshot();
      if(state.includes('link Description: Review My Situation'))throw new Error('Outside-scope case can proceed to legal review');
      record.result='SAFE_OUTSIDE_SCOPE';return record;
    }
    if(await button(item.issueLabel).count()) {await button(item.issueLabel).click();await snapshot();}
    else if(await button('Another motor-vehicle issue').count()) {
      await button('Another motor-vehicle issue').click();await snapshot();
      await button(item.domain).click();await snapshot();
      await button(item.issueLabel).click();await snapshot();
    }
    for(const supplied of item.answers) {
      await tab.playwright.getByRole('heading',{level:2,name:supplied.question.question,exact:true}).waitFor({state:'visible'});
      await tab.playwright.getByLabel('Type your answer',{exact:true}).fill(supplied.answer);await snapshot();
      await button('Send').click();await snapshot();
      record.answers.push({slot:supplied.question.slot,answer:supplied.answer});
    }
    const review=tab.playwright.getByRole('link',{name:'Review My Situation',exact:true});
    await review.waitFor({state:'visible'});await review.click();
    await route('/verify');await snapshot();
    for(let n=0;n<25;n++) {
      const confirms=button('Confirm');if(!await confirms.count())break;
      await confirms.first().click();await snapshot();
    }
    const unknown=tab.playwright.getByRole('checkbox',{name:'I acknowledge that required facts remain unknown.',exact:true});
    if(await unknown.count()){await unknown.check();await snapshot();}
    await button('Confirm Structured Situation').click();
    await route('/guidance');await snapshot();
    await visible(button('Continue to Summary'));
    record.guidance=await snapshot();
    await button('Continue to Summary').click();await route('/summary');
    await visible(tab.playwright.getByRole('heading',{name:/^(Your Guidance Summary|Structured Situation & Guidance Summary)$/}));
    record.summary=await snapshot();
    if(!record.summary.includes('Deterministic guidance.'))throw new Error('Missing deterministic provenance');
    if(!record.summary.includes('What Is Still Uncertain'))throw new Error('Missing uncertainty section');
    record.result='DETERMINISTIC_BROWSER_JOURNEY_COMPLETED';
  } catch(error) {record.result='FAIL';record.error=String(error);record.lastState=await snapshot();}
  return record;
}
