const { test, expect } = require('@playwright/test');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),net=require('node:net'),cp=require('node:child_process');
let folder, server, url, archive, log;
test.beforeAll(async()=>{
    folder=fs.mkdtempSync(path.join(os.tmpdir(),'dlfilter-setup-browser-'));
    archive=path.join(folder,'serving.zip');
    const python=path.resolve(process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python');
    cp.execFileSync(python,['tests/setup_fixture.py',archive]);
    const socket=net.createServer();await new Promise(r=>socket.listen(0,'127.0.0.1',r));const port=socket.address().port;await new Promise(r=>socket.close(r));
    url=`http://127.0.0.1:${port}`;
    log=fs.openSync(path.join(folder,'server.log'),'w');
    server=cp.spawn(path.resolve(process.platform==='win32'?'target/release/dlfilter.exe':'target/release/dlfilter'),['serve'],{env:{...process.env,DLFILTER_HOST:'127.0.0.1',DLFILTER_PORT:String(port),DLFILTER_DATA_DIR:path.join(folder,'data'),DLFILTER_CACHE_DIR:path.join(folder,'cache'),DLFILTER_PRESETS_DIR:path.join(folder,'presets')},stdio:['ignore',log,log]});
    for(let i=0;i<200;i++){try{if((await fetch(url+'/api/setup/status')).ok)return;}catch(_){}await new Promise(r=>setTimeout(r,50));}
    throw new Error(fs.readFileSync(path.join(folder,'server.log'),'utf8'));
});
test.afterAll(async()=>{if(server){server.kill();await new Promise(r=>server.once('exit',r));}if(log)fs.closeSync(log);fs.rmSync(folder,{recursive:true,force:true});});

test('first-time setup languages, themes, import and background settings',async({page})=>{
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(url);
    await expect(page).toHaveURL(/\/setup$/);
    await expect(page.locator('#setup-destination')).toContainText('data');
    for(const width of [1280,390]){
        await page.setViewportSize({width,height:900});
        for(const locale of ['en_US','ja_JP','zh_TW','zh_CN']){
            await page.locator('#setup-language').selectOption(locale);
            await expect(page.locator('html')).toHaveAttribute('lang',locale.replace('_','-'));
            await page.locator('#setup-theme').click();
            expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
        }
    }
    await page.locator('#setup-language').selectOption('en_US');
    await page.locator('[name=title-language][value=ENG]').check();
    await page.locator('#setup-titles-start').click();
    await expect(page.locator('#setup-title-status')).toContainText('Preferences saved');
    await page.screenshot({path:'/tmp/dlfilter-setup-mobile.png',fullPage:true});
    await page.locator('#setup-file').setInputFiles(archive);
    await expect(page.locator('#setup-search')).toBeVisible({timeout:20000});
    await expect(page.locator('#setup-title-status')).toContainText('up to date');
    await page.locator('#setup-search').click();
    await expect(page.locator('#copy-tags-btn')).toBeEnabled();
    await expect(page.locator('#catalogue-settings-link')).toContainText('Catalogue settings');
    await page.locator('#catalog-query').fill('magic');await page.locator('#search-btn').click();
    await expect(page.locator('#catalog-card-container .catalog-card').first()).toBeVisible();
    await page.locator('#catalogue-settings-link').click();
    await expect(page.locator('[name=title-language][value=ENG]')).toBeChecked();
    expect(errors).toEqual([]);
});
