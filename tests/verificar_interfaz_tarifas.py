from playwright.sync_api import sync_playwright
from pathlib import Path
import json,re
root=Path(__file__).resolve().parents[1]
html=(root/'index.html').read_text()
html=re.sub(r'<script[^>]*src=[^>]+></script>','',html)
html=re.sub(r'<link[^>]*>', '',html)
lib=json.loads((root/'data/biblioteca_ratios.json').read_text())
cal=json.loads((root/'data/calibracion.json').read_text())
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=b.new_page(viewport={'width':1440,'height':980},accept_downloads=True)
 errs=[];page.on('pageerror',lambda e:errs.append(str(e)))
 page.goto('about:blank');page.set_content(html)
 page.evaluate('''d=>{window._saved={};Object.defineProperty(window,'localStorage',{configurable:true,value:{setItem(k,v){window._saved[k]=v},getItem(k){return window._saved[k]||null}}});window.fetch=async url=>({ok:true,json:async()=>url.includes('calibracion')?d.cal:d.lib});}''',{'lib':lib,'cal':cal})
 for css in ['base.css','hydra.css','simple.css','responsive.css']: page.add_style_tag(content=(root/'css'/css).read_text())
 for js in ['config.js','estimacion.js','interfaz.js','exportacion.js','app.js','simple.js']:page.add_script_tag(content=(root/'js'/js).read_text())
 page.wait_for_function('!!window.__ultimaEstimacion',timeout=12000)
 prior=page.evaluate('calculate()')
 page.locator('[data-select="tariffMode"]').select_option('disciplina')
 assert page.locator('[data-key="tariff:CIV"]').is_visible()
 assert page.evaluate('state.tariffMode')=='disciplina'
 init=page.evaluate('calculate()')
 assert round(init["budget"],4)==round(prior["budget"],4)
 page.locator('[data-key="tariff:CIV"]').fill('125')
 changed=page.evaluate('calculate()')
 assert changed["total"]==prior["total"]
 assert abs(changed["budget"]-prior["budget"]-90*changed['byDisc']['CIV'])<1e-6
 assert 'Tarifas por disciplina' in page.locator('.simpleKpiAccent').inner_text()
 page.locator('[data-key="tariff:CIV"]').press('Tab')
 assert page.locator('[data-key="tariff:CIV"]').input_value()=='125'
 page.locator('[data-key="tariff:INS"]').fill('47')
 page.locator('[data-key="tariff:INS"]').press('Tab')
 page.locator('[data-simple-tab="resumen"]').first.click()
 assert page.get_by_text('Presupuesto por disciplina').is_visible()
 page.screenshot(path='/mnt/data/ESTIMA_V5_2_Captura_Tarifas.png',full_page=False)
 with page.expect_download() as d:page.locator('.topbar [data-action="save"]').click()
 obj=json.loads(d.value.path().read_text())
 assert obj['state']['tariffMode']=='disciplina' and obj['state']['disciplineRates']['CIV']==125
 with page.expect_download() as d:
  page.evaluate('exportCSV()')
 csv=d.value.path().read_text(encoding='utf-8-sig')
 assert 'Tarifa H/H disciplina' in csv and 'Costo del trabajo' in csv
 page.evaluate('window.print=()=>{window._printed=true}')
 page.locator('.simpleResultActions [data-action="print"]').click()
 assert page.evaluate('window._printed')
 assert 'Horas y costos por disciplina' in page.locator('#printReport').inner_text()
 # as button is inside sidebar when mode discipline
 page.on('dialog',lambda dia:dia.accept()) if False else None
 assert not errs,errs
 print('✓ V5.2 browser: tarifa disciplina, coste, horas constantes, input, JSON, CSV, PDF')
 b.close()
