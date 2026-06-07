<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rewise CRM</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--umbra:#6B4F3A;--umbra2:#8a6548;--linen:#F5F0EA;--graphite:#2C2C2C;--muted:#8a7f78;--border:#e0d9d3;--border2:#cfc5bc;--bg:#faf8f6;--card:#ffffff;--surface:#f5f0ea;--approx:#9a6c1a}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--graphite);min-height:100vh}

.login-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center}
.login-card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:40px;width:340px;text-align:center;box-shadow:0 2px 24px rgba(107,79,58,.08)}
.login-logo{width:52px;height:52px;background:var(--umbra);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:500;color:var(--linen);margin:0 auto 16px;letter-spacing:.5px}
.login-title{font-size:20px;font-weight:500;margin-bottom:4px}
.login-sub{font-size:13px;color:var(--muted);margin-bottom:24px}
.login-input{width:100%;padding:11px 14px;font-size:14px;border:1px solid var(--border);border-radius:10px;font-family:inherit;margin-bottom:12px;background:var(--bg);color:var(--graphite)}
.login-input:focus{outline:none;border-color:var(--umbra)}
.login-btn{width:100%;padding:12px;background:var(--umbra);color:var(--linen);border:none;border-radius:10px;font-size:14px;cursor:pointer;font-family:inherit;font-weight:500}
.login-btn:hover{background:var(--umbra2)}
.login-err{font-size:12px;color:#a33030;margin-top:8px}

.app{display:none;flex-direction:column;min-height:100vh}
.topnav{background:var(--umbra);padding:0 20px;display:flex;align-items:center;height:52px}
.topnav-brand{display:flex;align-items:center;gap:10px;margin-right:28px}
.topnav-mark{width:30px;height:30px;background:rgba(245,240,234,.2);border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:500;color:var(--linen);letter-spacing:.3px}
.topnav-name{font-size:13px;font-weight:500;color:var(--linen)}
.nav-tab{padding:0 14px;height:52px;display:flex;align-items:center;font-size:13px;color:rgba(245,240,234,.6);cursor:pointer;border-bottom:2px solid transparent;transition:all .15s}
.nav-tab:hover{color:var(--linen)}
.nav-tab.active{color:var(--linen);border-bottom-color:var(--linen)}
.nav-right{margin-left:auto}
.logout-btn{font-size:12px;color:rgba(245,240,234,.5);cursor:pointer;padding:5px 10px;border-radius:6px;border:1px solid rgba(245,240,234,.2)}
.logout-btn:hover{color:var(--linen);border-color:rgba(245,240,234,.4)}

.page{display:none;padding:20px;max-width:1200px;margin:0 auto;width:100%}
.page.active{display:block}

.stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px 18px}
.stat-label{font-size:11px;color:var(--muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:.7px}
.stat-val{font-size:26px;font-weight:500;color:var(--graphite);line-height:1}
.stat-sub{font-size:12px;color:var(--muted);margin-top:4px}
.stat-accent{color:var(--umbra)}

.toolbar{display:flex;gap:8px;align-items:center;margin-bottom:14px;flex-wrap:wrap}
.filter-btn{padding:6px 14px;border-radius:20px;border:1px solid var(--border);font-size:12px;color:var(--muted);cursor:pointer;background:transparent;font-family:inherit;transition:all .12s}
.filter-btn:hover{border-color:var(--umbra);color:var(--graphite)}
.filter-btn.active{background:var(--umbra);color:var(--linen);border-color:var(--umbra)}
.search-wrap{position:relative;margin-left:auto}
.search-ico{position:absolute;left:10px;top:50%;transform:translateY(-50%);font-size:14px;color:var(--muted);pointer-events:none}
.search-wrap input{padding:7px 12px 7px 32px;font-size:13px;border:1px solid var(--border);border-radius:10px;font-family:inherit;background:var(--card);width:220px}
.search-wrap input:focus{outline:none;border-color:var(--umbra)}

.orders-wrap{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.order-row{display:grid;grid-template-columns:110px 1fr 130px 110px 100px 140px;border-bottom:1px solid var(--border);cursor:pointer;transition:background .1s}
.order-row:last-child{border-bottom:none}
.order-row:hover{background:var(--bg)}
.order-row.hdr{background:var(--surface);cursor:default}
.order-row.hdr:hover{background:var(--surface)}
.cell{padding:12px 14px;font-size:13px;display:flex;align-items:center}
.cell.hdr{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px}
.order-num-text{font-weight:500;color:var(--umbra)}
.badge{font-size:11px;padding:3px 9px;border-radius:20px;white-space:nowrap}
.b-new{background:#E6F1FB;color:#185FA5}
.b-work{background:#FAEEDA;color:#854F0B}
.b-ready{background:#EAF3DE;color:#3B6D11}
.b-issued{background:#F1EFE8;color:#5F5E5A}
.b-urgent{background:#FCEBEB;color:#A32D2D}
.b-postponed{background:#F1EFE8;color:#888}

.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:100;align-items:center;justify-content:center}
.modal-bg.open{display:flex}
.modal{background:var(--card);border:1px solid var(--border);border-radius:16px;width:640px;max-height:88vh;display:flex;flex-direction:column;overflow:hidden}
.modal-header{padding:18px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.modal-title{font-size:15px;font-weight:500}
.modal-close{cursor:pointer;font-size:22px;color:var(--muted);line-height:1;padding:0 6px;border-radius:4px}
.modal-close:hover{background:var(--bg)}
.modal-body{overflow-y:auto;padding:20px;flex:1}
.modal-footer{padding:14px 20px;border-top:1px solid var(--border);display:flex;gap:8px;justify-content:flex-end}
.btn{padding:9px 18px;border-radius:8px;font-size:13px;cursor:pointer;font-family:inherit;border:1px solid var(--border);background:var(--card);color:var(--graphite);transition:background .1s}
.btn:hover{background:var(--bg)}
.btn-primary{background:var(--umbra);color:var(--linen);border-color:var(--umbra)}
.btn-primary:hover{background:var(--umbra2);border-color:var(--umbra2)}

.m-head{display:flex;gap:20px;margin-bottom:20px;flex-wrap:wrap;align-items:flex-start}
.m-order-num{font-size:12px;font-weight:500;color:var(--umbra);margin-bottom:4px}
.m-client-name{font-size:18px;font-weight:500;margin-bottom:3px}
.m-client-phone{font-size:13px;color:var(--muted)}
.m-meta{display:flex;flex-direction:column;gap:5px;font-size:12px;text-align:right;margin-left:auto}
.m-meta-row{color:var(--muted)}
.m-meta-row strong{color:var(--graphite);font-weight:400}
.m-section-title{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.7px;margin-bottom:10px}
.item-card{background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:12px 14px;margin-bottom:8px}
.item-card-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}
.item-num-badge{font-size:11px;font-weight:500;color:var(--umbra);background:var(--linen);padding:2px 8px;border-radius:20px}
.item-type{font-size:13px;font-weight:500;margin-bottom:3px}
.item-svcs{font-size:12px;color:var(--muted);line-height:1.6}
.item-footer{display:flex;align-items:flex-end;justify-content:space-between;margin-top:8px}
.item-dates{font-size:11px;color:var(--muted);line-height:1.7}
.item-price{font-size:13px;font-weight:500}
.info-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:4px}
.info-cell{background:var(--bg);border-radius:8px;padding:10px 12px}
.info-cell-label{font-size:11px;color:var(--muted);margin-bottom:4px}
.info-cell-val{font-size:13px}

.clients-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.client-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;cursor:pointer;transition:border-color .12s}
.client-card:hover{border-color:var(--umbra)}
.client-avatar{width:40px;height:40px;border-radius:50%;background:var(--linen);display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:500;color:var(--umbra);margin-bottom:10px}
.client-name{font-size:14px;font-weight:500;margin-bottom:2px}
.client-phone{font-size:12px;color:var(--muted);margin-bottom:6px}
.client-stats{font-size:11px;color:var(--muted)}

.analytics-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:20px}
.chart-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px}
.chart-title{font-size:13px;font-weight:500;margin-bottom:16px}
.bar-row{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.bar-label{font-size:12px;color:var(--muted);width:150px;text-align:right;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bar-track{flex:1;background:var(--bg);border-radius:4px;height:6px;overflow:hidden;border:1px solid var(--border)}
.bar-fill{height:100%;border-radius:4px;background:var(--umbra)}
.bar-val{font-size:12px;color:var(--muted);width:60px;flex-shrink:0}
.period-btns{display:flex;gap:6px;margin-bottom:16px}
.period-btn{padding:4px 12px;border-radius:20px;border:1px solid var(--border);font-size:12px;color:var(--muted);cursor:pointer;background:transparent;font-family:inherit}
.period-btn.active{background:var(--umbra);color:var(--linen);border-color:var(--umbra)}
.revenue-big{font-size:32px;font-weight:500;color:var(--umbra);margin-bottom:4px}
.revenue-sub{font-size:13px;color:var(--muted)}
.revenue-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:12px}
.rev-cell{background:var(--bg);border-radius:8px;padding:10px 12px}
.rev-cell-label{font-size:11px;color:var(--muted);margin-bottom:4px}
.rev-cell-val{font-size:15px;font-weight:500}

@media(max-width:768px){
  .stats-row{grid-template-columns:repeat(2,1fr)}
  .order-row{grid-template-columns:90px 1fr 100px}
  .cell:nth-child(4),.cell:nth-child(5),.cell:nth-child(6){display:none}
  .analytics-grid{grid-template-columns:1fr}
  .modal{width:95vw}
  .page{padding:12px}
}
</style>
</head>
<body>

<div class="login-wrap" id="login-wrap">
  <div class="login-card">
    <div class="login-logo">RW</div>
    <div style="font-size:20px;font-weight:500;margin-bottom:4px">Rewise CRM</div>
    <div style="font-size:13px;color:var(--muted);margin-bottom:24px">Введіть пароль для входу</div>
    <input type="password" class="login-input" id="pwd-input" placeholder="Пароль" onkeydown="if(event.key==='Enter')doLogin()">
    <button class="login-btn" onclick="doLogin()">Увійти</button>
    <div class="login-err" id="login-err"></div>
  </div>
</div>

<div class="app" id="app">
  <nav class="topnav">
    <div class="topnav-brand">
      <div class="topnav-mark">RW</div>
      <div class="topnav-name">Rewise CRM</div>
    </div>
    <div class="nav-tab active" onclick="showPage('orders',this)">Замовлення</div>
    <div class="nav-tab" onclick="showPage('clients',this)">Клієнти</div>
    <div class="nav-tab" onclick="showPage('analytics',this)">Аналітика</div>
    <div class="nav-right">
      <div class="logout-btn" onclick="logout()">Вийти</div>
    </div>
  </nav>

  <div class="page active" id="page-orders">
    <div class="stats-row" id="stats-row"></div>
    <div class="toolbar">
      <button class="filter-btn active" onclick="setFilter('all',this)">Усі</button>
      <button class="filter-btn" onclick="setFilter('new',this)">🆕 Нові</button>
      <button class="filter-btn" onclick="setFilter('work',this)">⚙️ В роботі</button>
      <button class="filter-btn" onclick="setFilter('ready',this)">✅ Готові</button>
      <button class="filter-btn" onclick="setFilter('issued',this)">📦 Видані</button>
      <div class="search-wrap">
        <span class="search-ico">⌕</span>
        <input type="text" id="search-input" placeholder="Пошук..." oninput="renderOrders()">
      </div>
      <button class="btn" onclick="printPlan()" style="white-space:nowrap">🖨 Роздрукувати план</button>
      <button class="btn btn-primary" onclick="openNewOrder()" style="white-space:nowrap">+ Нове замовлення</button>
    </div>
    <div class="toolbar" id="manager-filters" style="margin-top:-6px;margin-bottom:14px"></div>
    <div class="orders-wrap">
      <div class="order-row hdr">
        <div class="cell hdr">Номер</div>
        <div class="cell hdr">Клієнт</div>
        <div class="cell hdr">Статус</div>
        <div class="cell hdr">Приймальник</div>
        <div class="cell hdr">Термін</div>
        <div class="cell hdr">Оплата</div>
      </div>
      <div id="orders-body"></div>
    </div>
  </div>

  <div class="page" id="page-clients">
    <div class="toolbar">
      <div class="search-wrap" style="margin-left:0">
        <span class="search-ico">⌕</span>
        <input type="text" id="client-search" placeholder="Пошук клієнта..." oninput="renderClients()">
      </div>
    </div>
    <div class="clients-grid" id="clients-grid"></div>
  </div>

  <div class="page" id="page-analytics">
    <div class="stats-row" id="analytics-stats"></div>
    <div class="period-btns">
      <button class="period-btn active" onclick="setPeriod('week',this)">Тиждень</button>
      <button class="period-btn" onclick="setPeriod('month',this)">Місяць</button>
      <button class="period-btn" onclick="setPeriod('all',this)">Весь час</button>
    </div>
    <div class="chart-card" style="margin-bottom:16px">
      <div class="chart-title">Оборот</div>
      <div id="revenue-block"></div>
    </div>
    <div class="analytics-grid" id="analytics-grid"></div>
  </div>
</div>

<div class="modal-bg" id="modal-bg" onclick="closeBg(event)">
  <div class="modal">
    <div class="modal-header">
      <div class="modal-title" id="modal-title"></div>
      <div class="modal-close" onclick="closeModal()">×</div>
    </div>
    <div class="modal-body" id="modal-body"></div>
    <div class="modal-footer" id="modal-footer"></div>
  </div>
</div>

<script>
const PWD_HASH="70775e2a6abd151f90d68ec1cc3b5bad65e57f7c545b6790e744de1e4b7db78a";
const SHEET_ID="1kDJ893PFa_DTNKt-r8wQES_JFXbJSDNU8niRLz70Aao";
const API_URL="https://script.google.com/macros/s/AKfycbw_hvy2c6xpmFFEMFjiJ51iQoNb0s3MGnGs6gz3nkyqzYGanntufTkdbQ5Ah5L7k2hPag/exec";

async function hashStr(s){
  const buf=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s));
  return Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,"0")).join("");
}

async function doLogin(){
  const pwd=document.getElementById("pwd-input").value;
  const h=await hashStr(pwd);
  if(h===PWD_HASH){
    document.getElementById("login-wrap").style.display="none";
    document.getElementById("app").style.display="flex";
    sessionStorage.setItem("rw_auth","1");
    loadData();
  } else {
    document.getElementById("login-err").textContent="Невірний пароль";
    document.getElementById("pwd-input").style.borderColor="#c45050";
  }
}

if(sessionStorage.getItem("rw_auth")==="1"){
  document.getElementById("login-wrap").style.display="none";
  document.getElementById("app").style.display="flex";
  loadData();
}

function logout(){sessionStorage.removeItem("rw_auth");location.reload();}

let ORDERS=[],ITEMS=[],PARTNERS=[],currentFilter="all",currentPeriod="month";

const DEMO_ORDERS=[
  {"Номер замовлення":"RW-0001","Дата створення":"04.06.2026 11:42","Приймальник":"Сергей","Ім'я клієнта":"Марина Коваль","Телефон":"+380 67 123 45 67","Оплата":"Передоплата: 500 ₴","Срок":"10.06","Статус":"🆕 Новий"},
  {"Номер замовлення":"RW-0002","Дата створення":"04.06.2026 14:15","Приймальник":"Олександр","Ім'я клієнта":"Олег Петренко","Телефон":"+380 50 987 65 43","Оплата":"Післяоплата","Срок":"Терміново","Статус":"✅ Підтверджено"},
  {"Номер замовлення":"RW-0003","Дата створення":"05.06.2026 09:30","Приймальник":"Сергей","Ім'я клієнта":"Анна Сидоренко","Телефон":"+380 63 456 78 90","Оплата":"Передоплата: 1000 ₴","Срок":"Без терміну","Статус":"🆕 Новий"},
  {"Номер замовлення":"RW-0004","Дата створення":"06.06.2026 10:05","Приймальник":"Магазин","Ім'я клієнта":"Віктор Ковальчук","Телефон":"+380 97 321 54 76","Оплата":"Підтверджено: 4 800 ₴","Срок":"15.06","Статус":"📦 Виданий"},
];
const DEMO_ITEMS=[
  {"Номер замовлення":"RW-0001","Номер виробу":"RW-0001-1","Тип":"Взуття","Бренд":"Gucci Horsebit","Послуги":"Чистка — низьке взуття, +200 ₴","Сума":"1 600 ₴","Статус":"⚙️ В роботі","Дата прийому":"04.06.2026 11:42","Дата в роботі":"05.06.2026 09:00","Дата готово":"","Дата видачі":""},
  {"Номер замовлення":"RW-0001","Номер виробу":"RW-0001-2","Тип":"Сумка","Бренд":"Louis Vuitton Neverfull","Послуги":"Реставрація — шкіряна сумка M","Сума":"від 2 700 ₴","Статус":"🆕 Новий","Дата прийому":"04.06.2026 11:42","Дата в роботі":"","Дата готово":"","Дата видачі":""},
  {"Номер замовлення":"RW-0002","Номер виробу":"RW-0002-1","Тип":"Взуття","Бренд":"Golden Goose Superstar","Послуги":"Набійки формовані","Сума":"850 ₴","Статус":"✅ Готово","Дата прийому":"04.06.2026 14:15","Дата в роботі":"04.06.2026 16:00","Дата готово":"05.06.2026 12:00","Дата видачі":""},
  {"Номер замовлення":"RW-0003","Номер виробу":"RW-0003-1","Тип":"Взуття","Бренд":"Loro Piana лофери","Послуги":"Фарбування — низьке взуття, Набійки листові","Сума":"2 500 ₴","Статус":"⚙️ В роботі","Дата прийому":"05.06.2026 09:30","Дата в роботі":"06.06.2026 10:00","Дата готово":"","Дата видачі":""},
  {"Номер замовлення":"RW-0004","Номер виробу":"RW-0004-1","Тип":"Взуття","Бренд":"Chanel балетки","Послуги":"Реставрація — низьке взуття","Сума":"2 000 ₴","Статус":"📦 Виданий","Дата прийому":"06.06.2026 10:05","Дата в роботі":"06.06.2026 14:00","Дата готово":"07.06.2026 11:00","Дата видачі":"07.06.2026 15:30"},
  {"Номер замовлення":"RW-0004","Номер виробу":"RW-0004-2","Тип":"Взуття","Бренд":"Chanel балетки 2","Послуги":"Чистка — низьке взуття, Набійки листові","Сума":"2 100 ₴","Статус":"📦 Виданий","Дата прийому":"06.06.2026 10:05","Дата в роботі":"06.06.2026 14:00","Дата готово":"07.06.2026 11:00","Дата видачі":"07.06.2026 15:30"},
];

async function loadData(){
  try{
    const[r1,r2,r3]=await Promise.all([
      fetch(`https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json&sheet=Замовлення`),
      fetch(`https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json&sheet=Вироби`),
      fetch(`https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?tqx=out:json&sheet=Партнери`)
    ]);
    ORDERS=await parseSheet(r1);
    ITEMS=await parseSheet(r2);
    PARTNERS=await parsePartners(r3);
    if(!ORDERS.length) ORDERS=DEMO_ORDERS;
    if(!ITEMS.length) ITEMS=DEMO_ITEMS;
    if(!PARTNERS.length) PARTNERS=["Сергей"];
  }catch(e){ORDERS=DEMO_ORDERS;ITEMS=DEMO_ITEMS;PARTNERS=["Сергей"];}
  renderAll();
}

async function parsePartners(res){
  try{
    const text=await res.text();
    const json=JSON.parse(text.replace(/^.*?({.*}).*$/s,"$1"));
    if(!json.table||!json.table.rows) return[];
    return json.table.rows.map(row=>{
      const cell=row.c[0];
      return cell&&cell.v?String(cell.v):"";
    }).filter(v=>v&&v!=="Имя"&&v!=="Ім'я");
  }catch(e){return[];}
}

async function parseSheet(res){
  const text=await res.text();
  const json=JSON.parse(text.replace(/^.*?({.*}).*$/s,"$1"));
  if(!json.table||!json.table.rows) return[];
  // Используем фиксированные имена колонок по позиции
  const ORDERS_COLS = ["Номер замовлення","Дата створення","Приймальник","Ім'я клієнта","Телефон","Оплата","Термін","Статус"];
  const ITEMS_COLS = ["Номер замовлення","Номер виробу","Тип","Бренд","Послуги","Сума","Статус","Дата прийому","Дата в роботі","Дата готово","Дата видачі"];
  const ncols = json.table.cols.length;
  const cols = ncols >= 8 ? ORDERS_COLS : ITEMS_COLS;
  return json.table.rows.map(row=>{
    const obj={};
    cols.forEach((col,i)=>{
      const cell=row.c[i];
      if(!cell||cell.v===null){obj[col]="";return;}
      obj[col]=cell.f||String(cell.v);
    });
    return obj;
  }).filter(r=>r["Номер замовлення"]&&r["Номер замовлення"].startsWith("RW-"));
}

function getStatus(num){
  const items=ITEMS.filter(i=>i["Номер замовлення"]===num);
  if(!items.length) return"new";
  if(items.every(i=>i["Статус"]==="📦 Виданий")) return"issued";
  if(items.some(i=>i["Статус"]==="✅ Готово")) return"ready";
  if(items.some(i=>i["Статус"]==="⚙️ В роботі")) return"work";
  return"new";
}

function badgeHTML(num){
  const st=getStatus(num);
  const m={new:["🆕 Новий","b-new"],work:["⚙️ В роботі","b-work"],ready:["✅ Готово","b-ready"],issued:["📦 Виданий","b-issued"]};
  return`<span class="badge ${m[st][1]}">${m[st][0]}</span>`;
}

function itemBadge(st){
  if(st==="⚙️ В роботі") return"b-work";
  if(st==="✅ Готово") return"b-ready";
  if(st==="📦 Виданий") return"b-issued";
  if(st==="⏳ Відкладено") return"b-postponed";
  return"b-new";
}

function extractAmount(str){
  const m=str.replace(/\s/g,"").match(/(\d+)/);
  return m?parseInt(m[1]):0;
}

function renderAll(){renderStats();renderOrders();renderClients();renderAnalytics();renderManagerFilters();}

function renderStats(){
  const active=ORDERS.filter(o=>getStatus(o["Номер замовлення"])!=="issued").length;
  const inWork=ITEMS.filter(i=>i["Статус"]==="⚙️ В роботі").length;
  const readyC=ITEMS.filter(i=>i["Статус"]==="✅ Готово").length;
  const issuedC=ORDERS.filter(o=>getStatus(o["Номер замовлення"])==="issued").length;
  document.getElementById("stats-row").innerHTML=`
    <div class="stat-card"><div class="stat-label">Активних замовлень</div><div class="stat-val stat-accent">${active}</div></div>
    <div class="stat-card"><div class="stat-label">Виробів в роботі</div><div class="stat-val">${inWork}</div></div>
    <div class="stat-card"><div class="stat-label">Готові до видачі</div><div class="stat-val" style="color:#3B6D11">${readyC}</div></div>
    <div class="stat-card"><div class="stat-label">Видано замовлень</div><div class="stat-val" style="color:var(--muted)">${issuedC}</div></div>
  `;
}

let currentManager = "all";

function setFilter(f,btn){
  currentFilter=f;
  document.querySelectorAll("#page-orders > .toolbar:first-of-type .filter-btn").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");
  renderOrders();
}

function setManager(m,btn){
  currentManager=m;
  document.querySelectorAll("#manager-filters .filter-btn").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");
  renderOrders();
}

function renderManagerFilters(){
  const el=document.getElementById("manager-filters");
  if(!el) return;
  const managers=["all",...new Set(ORDERS.map(o=>o["Приймальник"]).filter(Boolean))];
  el.innerHTML=managers.map(m=>`<button class="filter-btn${m===currentManager?" active":""}" onclick="setManager('${m}',this)">${m==="all"?"Всі":m}</button>`).join("");
}

function renderOrders(){
  const q=(document.getElementById("search-input")?.value||"").toLowerCase();
  const filtered=ORDERS.filter(o=>{
    const st=getStatus(o["Номер замовлення"]);
    const mf=currentFilter==="all"||st===currentFilter;
    const mm=currentManager==="all"||o["Приймальник"]===currentManager;
    const mq=!q||o["Ім'я клієнта"].toLowerCase().includes(q)||o["Номер замовлення"].toLowerCase().includes(q)||o["Телефон"].includes(q);
    return mf&&mm&&mq;
  });
  const el=document.getElementById("orders-body");
  if(!filtered.length){el.innerHTML=`<div style="padding:28px;text-align:center;color:var(--muted);font-size:13px">Замовлень не знайдено</div>`;return;}
  el.innerHTML=filtered.map(o=>{
    const urgent=o["Термін"]==="Терміново"||o["Термін"]==="⚡ Терміново";
    return`<div class="order-row" onclick="openOrder('${o["Номер замовлення"]}')">
      <div class="cell"><span class="order-num-text">${o["Номер замовлення"]}</span></div>
      <div class="cell" style="flex-direction:column;align-items:flex-start;gap:2px">
        <span style="font-weight:500">${o["Ім'я клієнта"]}</span>
        <span style="font-size:11px;color:var(--muted)">${o["Телефон"]}</span>
      </div>
      <div class="cell" style="gap:6px">${badgeHTML(o["Номер замовлення"])}${urgent?'<span class="badge b-urgent">⚡</span>':""}</div>
      <div class="cell" style="color:var(--muted)">${o["Приймальник"]}</div>
      <div class="cell" style="color:${urgent?"#A32D2D":"var(--muted)"}">${o["Термін"]}</div>
      <div class="cell" style="color:var(--muted);font-size:12px">${o["Оплата"]}</div>
    </div>`;
  }).join("");
}

function openOrder(num){
  const order=ORDERS.find(o=>o["Номер замовлення"]===num);
  if(!order) return;
  const items=ITEMS.filter(i=>i["Номер замовлення"]===num);
  document.getElementById("modal-title").textContent=`Замовлення ${num}`;
  document.getElementById("modal-body").innerHTML=`
    <div class="m-head">
      <div>
        <div class="m-order-num">${order["Номер замовлення"]}</div>
        <div class="m-client-name">${order["Ім'я клієнта"]}</div>
        <div class="m-client-phone">${order["Телефон"]}</div>
      </div>
      <div class="m-meta">
        <div class="m-meta-row">Приймальник: <strong>${order["Приёмщик"]}</strong></div>
        <div class="m-meta-row">Дата: <strong>${order["Дата создания"]}</strong></div>
        <div class="m-meta-row">Статус: <strong>${order["Статус заказа"]}</strong></div>
      </div>
    </div>
    <div style="margin-bottom:20px">
      <div class="m-section-title">Вироби</div>
      ${items.map(item=>`
        <div class="item-card">
          <div class="item-card-head">
            <span class="item-num-badge">${item["Номер изделия"]}</span>
            <span class="badge ${itemBadge(item["Статус"])}">${item["Статус"]}</span>
          </div>
          <div class="item-type">${item["Тип"]} — ${item["Бренд"]}</div>
          <div class="item-svcs">${item["Услуги"]}</div>
          <div class="item-footer">
            <div class="item-dates">
              ${item["Дата приёма"]?`Прийнято: ${item["Дата приёма"]}`:""}
              ${item["Дата в работе"]?`<br>В роботі: ${item["Дата в работе"]}`:""}
              ${item["Дата готово"]?`<br>Готово: ${item["Дата готово"]}`:""}
              ${item["Дата выдачи"]?`<br>Видано: ${item["Дата выдачи"]}`:""}
            </div>
            <div class="item-price">${item["Сумма"]}</div>
          </div>
        </div>
      `).join("")}
    </div>
    <div>
      <div class="m-section-title">Деталі замовлення</div>
      <div class="info-grid">
        <div class="info-cell"><div class="info-cell-label">Оплата</div><div class="info-cell-val">${order["Оплата"]}</div></div>
        <div class="info-cell"><div class="info-cell-label">Термін</div><div class="info-cell-val">${order["Срок"]}</div></div>
      </div>
    </div>
  `;
  document.getElementById("modal-footer").innerHTML=`
    <button class="btn" onclick="printOrder('${num}')">Роздрукувати квитанцію</button>
    <button class="btn btn-primary" onclick="closeModal()">Закрити</button>
  `;
  document.getElementById("modal-bg").classList.add("open");
}

function closeBg(e){if(e.target===document.getElementById("modal-bg"))closeModal();}
function closeModal(){document.getElementById("modal-bg").classList.remove("open");}

function printOrder(num){
  const order=ORDERS.find(o=>o["Номер замовлення"]===num);
  const items=ITEMS.filter(i=>i["Номер замовлення"]===num);
  const total=items.reduce((s,i)=>s+extractAmount(i["Сума"]),0);
  const w=window.open("","_blank");
  w.document.write(`<html><head><title>Квитанція ${num}</title>
  <style>body{font-family:Arial,sans-serif;padding:20px;font-size:13px;color:#111;max-width:320px}
  h2{font-size:16px;margin-bottom:2px}.sub{color:#888;font-size:11px;margin-bottom:14px}
  hr{border:none;border-top:1px dashed #ccc;margin:10px 0}
  .row{display:flex;justify-content:space-between;margin-bottom:4px;font-size:12px}
  .label{color:#888}.total{font-size:15px;font-weight:bold;margin-top:8px}
  table{width:100%;border-collapse:collapse;margin-top:8px}
  td{padding:4px 0;font-size:12px;vertical-align:top}td:last-child{text-align:right}
  .footer{margin-top:14px;font-size:10px;color:#aaa;text-align:center}
  .sig{margin-top:20px;display:flex;justify-content:space-between;font-size:11px;color:#888}
  </style></head><body>
  <h2>Rewise Studio</h2>
  <div class="sub">Одеса · @rewise.studio · +380 XX XXX XX XX</div>
  <hr>
  <div class="row"><span class="label">Замовлення</span><span><b>${num}</b></span></div>
  <div class="row"><span class="label">Дата</span><span>${order["Дата создания"]}</span></div>
  <div class="row"><span class="label">Клієнт</span><span>${order["Ім'я клієнта"]}</span></div>
  <div class="row"><span class="label">Телефон</span><span>${order["Телефон"]}</span></div>
  <div class="row"><span class="label">Термін</span><span>${order["Срок"]}</span></div>
  <hr>
  <table>${items.map(i=>`<tr><td>${i["Номер виробу"]}<br><span style="color:#888;font-size:11px">${i["Тип"]} — ${i["Бренд"]}</span><br><span style="color:#888;font-size:11px">${i["Послуги"]}</span></td><td><b>${i["Сума"]}</b></td></tr>`).join("")}</table>
  <hr>
  <div class="row total"><span>Разом</span><span>${total.toLocaleString("uk-UA")} ₴</span></div>
  <div class="row"><span class="label">Оплата</span><span>${order["Оплата"]}</span></div>
  <div class="sig"><span>Підпис майстра: _______</span><span>Підпис клієнта: _______</span></div>
  <div class="footer">Дякуємо за довіру · Rewise Studio</div>
  <script>window.onload=()=>window.print()<\/script></body></html>`);
}

function setPeriod(p,btn){
  currentPeriod=p;
  document.querySelectorAll(".period-btn").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");
  renderAnalytics();
}

function renderClients(){
  const q=(document.getElementById("client-search")?.value||"").toLowerCase();
  const map={};
  ORDERS.forEach(o=>{
    const k=o["Телефон"];
    if(!map[k]) map[k]={name:o["Ім'я клієнта"],phone:o["Телефон"],orders:[],total:0};
    map[k].orders.push(o["Номер замовлення"]);
    const items=ITEMS.filter(i=>i["Номер замовлення"]===o["Номер замовлення"]);
    map[k].total+=items.reduce((s,i)=>s+extractAmount(i["Сума"]),0);
  });
  const clients=Object.values(map).filter(c=>!q||c.name.toLowerCase().includes(q)||c.phone.includes(q));
  document.getElementById("clients-grid").innerHTML=clients.map(c=>{
    const initials=c.name.split(" ").map(w=>w[0]).join("").slice(0,2).toUpperCase();
    return`<div class="client-card">
      <div class="client-avatar">${initials}</div>
      <div class="client-name">${c.name}</div>
      <div class="client-phone">${c.phone}</div>
      <div class="client-stats">Замовлень: ${c.orders.length} · Сума: ${c.total.toLocaleString("uk-UA")} ₴</div>
    </div>`;
  }).join("");
}

function renderAnalytics(){
  const issuedOrders=ORDERS.filter(o=>getStatus(o["Номер замовлення"])==="issued");
  const allItems=ITEMS.filter(i=>i["Статус"]==="📦 Виданий");
  const totalRevenue=allItems.reduce((s,i)=>s+extractAmount(i["Сума"]),0);
  const avgCheck=issuedOrders.length?Math.round(totalRevenue/issuedOrders.length):0;
  const clients=new Set(ORDERS.map(o=>o["Телефон"])).size;
  document.getElementById("analytics-stats").innerHTML=`
    <div class="stat-card"><div class="stat-label">Загальний обіг</div><div class="stat-val stat-accent">${totalRevenue.toLocaleString("uk-UA")} ₴</div></div>
    <div class="stat-card"><div class="stat-label">Середній чек</div><div class="stat-val">${avgCheck.toLocaleString("uk-UA")} ₴</div></div>
    <div class="stat-card"><div class="stat-label">Клієнтів</div><div class="stat-val">${clients}</div></div>
    <div class="stat-card"><div class="stat-label">Виробів оброблено</div><div class="stat-val">${allItems.length}</div></div>
  `;

  const mgrMap={};
  ORDERS.forEach(o=>{
    const mgr=o["Приймальник"]||"—";
    if(!mgrMap[mgr]) mgrMap[mgr]={orders:0,revenue:0};
    mgrMap[mgr].orders++;
    const items=ITEMS.filter(i=>i["Номер замовлення"]===o["Номер замовлення"]&&i["Статус"]==="📦 Виданий");
    mgrMap[mgr].revenue+=items.reduce((s,i)=>s+extractAmount(i["Сума"]),0);
  });
  const mgrs=Object.entries(mgrMap).sort((a,b)=>b[1].revenue-a[1].revenue);
  const maxMgr=mgrs[0]?mgrs[0][1].revenue:1;

  const svcCount={};
  ITEMS.forEach(i=>{
    (i["Послуги"]||"").split(",").forEach(s=>{
      const k=s.trim().split("—")[0].trim().slice(0,22);
      if(k) svcCount[k]=(svcCount[k]||0)+1;
    });
  });
  const top=Object.entries(svcCount).sort((a,b)=>b[1]-a[1]).slice(0,6);
  const maxSvc=top[0]?top[0][1]:1;

  document.getElementById("revenue-block").innerHTML=`
    <div class="revenue-big">${totalRevenue.toLocaleString("uk-UA")} ₴</div>
    <div class="revenue-sub">Загальний підтверджений обіг</div>
    <div class="revenue-grid">
      <div class="rev-cell"><div class="rev-cell-label">Виданих замовлень</div><div class="rev-cell-val">${issuedOrders.length}</div></div>
      <div class="rev-cell"><div class="rev-cell-label">Середній чек</div><div class="rev-cell-val">${avgCheck.toLocaleString("uk-UA")} ₴</div></div>
      <div class="rev-cell"><div class="rev-cell-label">Виробів</div><div class="rev-cell-val">${allItems.length}</div></div>
    </div>
  `;

  document.getElementById("analytics-grid").innerHTML=`
    <div class="chart-card">
      <div class="chart-title">Топ послуг</div>
      ${top.map(([n,c])=>`<div class="bar-row"><div class="bar-label">${n}</div><div class="bar-track"><div class="bar-fill" style="width:${Math.round(c/maxSvc*100)}%"></div></div><div class="bar-val">${c} шт.</div></div>`).join("")}
    </div>
    <div class="chart-card">
      <div class="chart-title">По приймальниках</div>
      ${mgrs.map(([n,d])=>`<div class="bar-row"><div class="bar-label">${n}</div><div class="bar-track"><div class="bar-fill" style="width:${Math.round(d.revenue/maxMgr*100)}%"></div></div><div class="bar-val">${d.revenue.toLocaleString("uk-UA")} ₴</div></div>`).join("")}
    </div>
  `;
}

function showPage(name,tab){
  document.querySelectorAll(".page").forEach(p=>p.classList.remove("active"));
  document.querySelectorAll(".nav-tab").forEach(t=>t.classList.remove("active"));
  document.getElementById("page-"+name).classList.add("active");
  tab.classList.add("active");
}


// ─── NEW ORDER FORM ───────────────────────────────────────────────────────────

const SERVICES = {
  shoes: {
    cleaning: [["Чистка — літнє взуття",1200],["Чистка — низьке взуття",1400],["Чистка — середнє взуття",1600],["Чистка — високі чоботи",1800],["Чистка — UGG та хутряне",1400],["Базовий догляд — низьке взуття",1400],["Базовий догляд — середнє взуття",1600],["Базовий догляд — високі чоботи",1800],["Базовий догляд — UGG та хутряне",1400]],
    painting: [["Фарбування — літнє взуття",1400],["Фарбування — низьке взуття",1800],["Фарбування — середнє взуття",2000],["Фарбування — високі чоботи",2800],["Фарбування — UGG та хутряне",1800],["Покриття / відбілювання Midsole",1100],["Відбілювання підошви Loro Piana",1100],["Фарбування каблуків",900],["Фарбування ранта",700],["Фарбування танкетки",1200],["Глясаж — полірування гладкої шкіри",600],["Реставрація — літнє взуття",1600],["Реставрація — низьке взуття",2000],["Реставрація — середнє взуття",2200],["Реставрація — високі чоботи",3200],["Реставрація — UGG та хутряне",2400],["Реставрація носочної частини",1200],["Реставрація каблуків (гладка шкіра)",900],["Реставрація каблуків (лакова шкіра)",1200],["Усунення пошкоджень",1000]],
    heels: [["Набійки листові",700],["Набійки формовані",850],["Набійки штифтові поліуретанові — шпилька",550],["Набійки металеві — шпилька",700],["Нарощування каблуків",400],["Вирівнювання каблука під набійку",250],["Демонтаж металевого штифта",250],["Заміна каблуків без обтяжки",1800],["Заміна каблуків з обтяжкою шкірою",2500],["Заміна обтяжки каблуків — нова набійка включена",2400],["Заміна обтяжки танкетки",2600],["Зміцнення каблука",400]],
    sole: [["Профілактика жіноча",1200],["Профілактика чоловіча",1200],["Профілактика жіноча комбінована",1500],["Профілактика на всю площу підошви",1400],["Профілактика повний слід спортивного взуття",1800],["Нарощування носочної частини підошви",400],["Локальна підклейка",300],["Підклейка підошви по периметру",600],["Переклейка підошви",900],["Переклейка + прошивка підошви",1400],["Прошивка підошви",800],["Заміна гумової підошви",2400],["Заміна підошви Loro Piana",4000],["Заміна підошви Golden Goose",4000]],
    zippers: [["Заміна блискавки до 20 см (без матеріалу)",700],["Заміна блискавки від 21 см (без матеріалу)",900],["Заміна бігунка блискавки",300],["Врізання блискавки в халяву (без матеріалу)",2200]],
    hardware: [["Заміна гачків + гумка",500],["Заміна пряжки (без матеріалу)",450],["Заміна блочка та люверса",200],["Заміна кнопки (без розбору)",200]],
    sewing: [["Відновлення машинної строчки",300],["Відновлення ручної строчки",500],["Виготовлення та заміна шкіряних устілок",900],["Заміна підкладки задника з сітки",1600],["Заміна підкладки задника зі шкіри",2000],["Внутрішня латка",450],["Декоративна латка",600],["Ушивка халяви — по висоті",1600],["Ушивка халяви — по ширині",2000],["Заміна гумок з обтяжкою шкірою",900],["Вшивання гумок у халяву",1400],["Заміна ліпучок",550],["Виготовлення та заміна ремінців взуття",1600]],
    stretch: [["Розтяжка взуття в підйомі / ширина",600],["Розтяжка халяви чобіт / черевиків",1000]],
  },
  bags: {
    cleaning: [["Чистка — шкіряна сумка S",1400],["Чистка — шкіряна сумка M",1600],["Чистка — шкіряна сумка L",1800],["Чистка — текстильна сумка S",1400],["Чистка — текстильна сумка M",1600],["Чистка — текстильна сумка L",1800]],
    painting: [["Фарбування — шкіряна сумка S",1800],["Фарбування — шкіряна сумка M",2200],["Фарбування — шкіряна сумка L",2600],["Фарбування — поясний ремінь",1400],["Реставрація — шкіряна сумка S",2200],["Реставрація — шкіряна сумка M",2700],["Реставрація — шкіряна сумка L",3200],["Локальна реставрація шкіри",1000],["Реставрація кутиків сумки",450],["Реставрація ручок сумки",1600],["Реставрація плечового ременя",1600]],
    handles: [["Вкорочення плечового ременя",450],["Заміна плечового ременя з підбором шкіри",2000],["Заміна ручок шопер",1600],["Заміна ручок з підбором шкіри",2800],["Заміна ручок рюкзака з наповнювачем",3200]],
    zippers: [["Заміна блискавки сумки до 25 см (без матеріалу)",1400],["Заміна блискавки сумки від 25 см (без матеріалу)",1600],["Заміна блискавки в гаманці (без матеріалу)",1800],["Заміна блискавки рюкзака (без матеріалу)",1600],["Заміна бігунка блискавки",300]],
    hardware: [["Заміна карабіна (без матеріалу)",250],["Заміна пряжки ременя (без матеріалу)",250],["Заміна кнопки / заклепки / люверса",200],["Заміна магніта (без матеріалу)",500],["Встановлення декоративної латки",900],["Встановлення внутрішньої латки",450],["Встановлення кільця (без матеріалу)",250]],
    sewing: [["Відновлення машинного шва сумки",300],["Підклейка шкіри / деталі",300],["Ремонт кріплення ручок (без заміни деталей)",450],["Виготовлення шкіряного пулера",500],["Виготовлення та заміна тренчика",500],["Виготовлення та перешивка деталей",900],["Заміна канта в гаманці / клатчі",1200],["Заміна окантовки — кедер",1200]],
    lining: [["Заміна підкладки — сумка S",1800],["Заміна підкладки — сумка M",2200],["Заміна підкладки — сумка L",2600],["Заміна підкладки — гаманець / органайзер",2600]],
    edges: [["Торцювання урізу шкіри",12],["Торцювання ручок (2 сторони)",1200],["Торцювання ручок (4 сторони)",1400],["Торцювання плечового ременя",1400],["Торцювання тренчика / пулера",400]],
    belt: [["Пробивання отворів",200],["Вкорочення шкіряного поясного ременя",450],["Вкорочення ременя з перешиванням пряжки",600],["Заміна підкладки поясного ременя",2000],["Реставрація поясного ременя",800]],
  }
};

const DEPT_LABELS = {
  shoes: {cleaning:"Чистка / Базовий догляд",painting:"Фарбування / Реставрація",heels:"Каблуки та набійки",sole:"Підошва",zippers:"Блискавки",hardware:"Фурнітура",sewing:"Швейні роботи та деталі",stretch:"Розтяжка"},
  bags: {cleaning:"Чистка / Базовий догляд",painting:"Фарбування / Реставрація",handles:"Ручки та ремінь",zippers:"Блискавки",hardware:"Фурнітура",sewing:"Швейні роботи та деталі",lining:"Підкладка",edges:"Реставрація урізів",belt:"Поясний ремінь"}
};

let newOrder = {manager:"",client:"",phone:"",items:[],payment:"",deadline:""};
let currentItemIndex = -1;

function openNewOrder(){
  newOrder = {manager:"",client:"",phone:"",items:[],payment:"",deadline:""};
  document.getElementById("modal-title").textContent = "Нове замовлення";
  renderOrderStep1();
  document.getElementById("modal-bg").classList.add("open");
}

function renderOrderStep1(){
  const partners = [...new Set(PARTNERS.filter(Boolean))];
  if(!partners.length) partners.push("Сергей");
  document.getElementById("modal-body").innerHTML = `
    <div style="display:flex;flex-direction:column;gap:14px">
      <div>
        <div class="m-section-title" style="margin-bottom:6px">Хто приймає замовлення</div>
        <div style="display:flex;flex-wrap:wrap;gap:8px" id="mgr-btns">
          ${partners.map(p=>`<button class="filter-btn" onclick="selectManager('${p}',this)">${p}</button>`).join("")}
        </div>
      </div>
      <div>
        <div class="m-section-title" style="margin-bottom:6px">Ім'я клієнта</div>
        <input type="text" id="no-client" placeholder="Ім'я або назва магазину" style="width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:8px;font-size:13px;font-family:inherit;background:var(--bg)">
      </div>
      <div>
        <div class="m-section-title" style="margin-bottom:6px">Номер телефону</div>
        <input type="text" id="no-phone" placeholder="+380..." style="width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:8px;font-size:13px;font-family:inherit;background:var(--bg)">
      </div>
    </div>
  `;
  document.getElementById("modal-footer").innerHTML = `
    <button class="btn" onclick="closeModal()">Скасувати</button>
    <button class="btn btn-primary" onclick="goStep2()">Далі →</button>
  `;
}

function selectManager(name, btn){
  newOrder.manager = name;
  document.querySelectorAll("#mgr-btns .filter-btn").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");
}

function goStep2(){
  newOrder.client = document.getElementById("no-client").value.trim();
  newOrder.phone = document.getElementById("no-phone").value.trim();
  if(!newOrder.manager){alert("Оберіть приймальника");return;}
  if(!newOrder.client){alert("Введіть ім'я клієнта");return;}
  if(!newOrder.phone){alert("Введіть номер телефону");return;}
  renderItemsList();
}

function renderItemsList(){
  document.getElementById("modal-title").textContent = `Замовлення — ${newOrder.client}`;
  document.getElementById("modal-body").innerHTML = `
    <div style="margin-bottom:14px">
      <div class="m-section-title" style="margin-bottom:8px">Вироби</div>
      <div id="items-list">
        ${newOrder.items.length === 0 ? '<div style="color:var(--muted);font-size:13px;padding:8px 0">Ще немає виробів</div>' :
          newOrder.items.map((item,i)=>`
            <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px 12px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center">
              <div>
                <div style="font-size:13px;font-weight:500">${item.typeLabel} — ${item.brand}</div>
                <div style="font-size:11px;color:var(--muted);margin-top:2px">${item.services} · ${item.total}</div>
              </div>
              <button onclick="removeItem(${i})" style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:16px;padding:4px 8px">×</button>
            </div>
          `).join("")
        }
      </div>
      <button class="btn" onclick="addItem()" style="margin-top:8px;width:100%">+ Ще один виріб</button>
    </div>
  `;
  document.getElementById("modal-footer").innerHTML = `
    <button class="btn" onclick="renderOrderStep1()">← Назад</button>
    <button class="btn btn-primary" onclick="${newOrder.items.length > 0 ? 'goStep3()' : 'addItem()'}">${newOrder.items.length > 0 ? 'Далі →' : 'Додати виріб'}</button>
  `;
}

function addItem(){
  currentItemIndex = newOrder.items.length;
  newOrder.items.push({type:"",typeLabel:"",brand:"",dept:"",services:"",total:"",extra200:false});
  renderSelectType();
}

function removeItem(i){
  newOrder.items.splice(i,1);
  renderItemsList();
}

function renderSelectType(){
  document.getElementById("modal-body").innerHTML = `
    <div style="margin-bottom:16px">
      <div class="m-section-title" style="margin-bottom:10px">Тип виробу</div>
      <div style="display:flex;gap:10px">
        <button class="filter-btn" style="flex:1;padding:14px;font-size:14px" onclick="selectType('shoes','Взуття',this)">👟 Взуття</button>
        <button class="filter-btn" style="flex:1;padding:14px;font-size:14px" onclick="selectType('bags','Сумка / Аксесуар',this)">👜 Сумка / Аксесуар</button>
      </div>
    </div>
  `;
  document.getElementById("modal-footer").innerHTML = `
    <button class="btn" onclick="renderItemsList()">← Назад</button>
    <button class="btn btn-primary" onclick="goToBrand()">Далі →</button>
  `;
}

function selectType(type, label, btn){
  newOrder.items[currentItemIndex].type = type;
  newOrder.items[currentItemIndex].typeLabel = label;
  document.querySelectorAll("#modal-body .filter-btn").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");
}

function goToBrand(){
  if(!newOrder.items[currentItemIndex].type){alert("Оберіть тип виробу");return;}
  document.getElementById("modal-body").innerHTML = `
    <div>
      <div class="m-section-title" style="margin-bottom:6px">Бренд та модель</div>
      <input type="text" id="no-brand" placeholder="Gucci, LV, без бренду..." style="width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:8px;font-size:13px;font-family:inherit;background:var(--bg)" value="${newOrder.items[currentItemIndex].brand}">
    </div>
  `;
  document.getElementById("modal-footer").innerHTML = `
    <button class="btn" onclick="renderSelectType()">← Назад</button>
    <button class="btn btn-primary" onclick="goToDept()">Далі →</button>
  `;
}

function goToDept(){
  const brand = document.getElementById("no-brand").value.trim();
  if(!brand){alert("Введіть бренд або «без бренду»");return;}
  newOrder.items[currentItemIndex].brand = brand;
  const type = newOrder.items[currentItemIndex].type;
  const depts = DEPT_LABELS[type];
  document.getElementById("modal-body").innerHTML = `
    <div>
      <div class="m-section-title" style="margin-bottom:8px">${newOrder.items[currentItemIndex].typeLabel} — ${brand}<br>Відділ</div>
      <div style="display:flex;flex-direction:column;gap:6px" id="dept-btns">
        ${Object.entries(depts).map(([id,label])=>`<button class="filter-btn" style="text-align:left;padding:9px 14px" onclick="selectDept('${id}',this)">${label}</button>`).join("")}
      </div>
    </div>
  `;
  document.getElementById("modal-footer").innerHTML = `
    <button class="btn" onclick="goToBrand()">← Назад</button>
    <button class="btn btn-primary" onclick="goToService()">Далі →</button>
  `;
}

function selectDept(id, btn){
  newOrder.items[currentItemIndex].dept = id;
  document.querySelectorAll("#dept-btns .filter-btn").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");
}

function goToService(){
  if(!newOrder.items[currentItemIndex].dept){alert("Оберіть відділ");return;}
  const type = newOrder.items[currentItemIndex].type;
  const dept = newOrder.items[currentItemIndex].dept;
  const svcs = SERVICES[type][dept];
  const svcContainer = document.createElement("div");
  svcContainer.id = "svc-btns";
  svcContainer.style.cssText = "display:flex;flex-direction:column;gap:6px;max-height:300px;overflow-y:auto";
  svcs.forEach(function(s){
    const sname = s[0].replace(/'/g, "&#39;");
    const sprice = s[1];
    const priceStr = sprice.toLocaleString("uk-UA") + " ₴";
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.style.cssText = "text-align:left;padding:9px 14px;display:flex;justify-content:space-between";
    btn.innerHTML = "<span>" + s[0] + "</span><span style='color:var(--umbra);flex-shrink:0;margin-left:8px'>" + priceStr + "</span>";
    btn.addEventListener("click", (function(name, price){ return function(){ selectSvc(name, price, this); }; })(s[0], sprice));
    svcContainer.appendChild(btn);
  });
  const manualBtn = document.createElement("button");
  manualBtn.className = "filter-btn";
  manualBtn.style.cssText = "text-align:left;padding:9px 14px;color:var(--umbra)";
  manualBtn.textContent = "✏️ Ввести вручну";
  manualBtn.onclick = manualSvc;
  svcContainer.appendChild(manualBtn);
  const body = document.getElementById("modal-body");
  body.innerHTML = "<div><div class='m-section-title' style='margin-bottom:8px'>Послуга</div></div>";
  body.querySelector("div").appendChild(svcContainer);
  document.getElementById("modal-footer").innerHTML = "<button class='btn' onclick='goToDept()'>← Назад</button><button class='btn btn-primary' onclick='goToPrice()'>Далі →</button>";
}

function selectSvc(name, price, btn){
  newOrder.items[currentItemIndex].services = name;
  newOrder.items[currentItemIndex]._autoPrice = price;
  document.querySelectorAll("#svc-btns .filter-btn").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");
}

function manualSvc(){
  document.getElementById("modal-body").innerHTML = `
    <div style="display:flex;flex-direction:column;gap:12px">
      <div>
        <div class="m-section-title" style="margin-bottom:6px">Назва послуги</div>
        <input type="text" id="manual-svc" placeholder="Введіть назву..." style="width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:8px;font-size:13px;font-family:inherit;background:var(--bg)">
      </div>
      <div>
        <div class="m-section-title" style="margin-bottom:6px">Ціна (тільки цифри)</div>
        <input type="number" id="manual-price" placeholder="500" style="width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:8px;font-size:13px;font-family:inherit;background:var(--bg)">
      </div>
    </div>
  `;
  document.getElementById("modal-footer").innerHTML = `
    <button class="btn" onclick="goToService()">← Назад</button>
    <button class="btn btn-primary" onclick="confirmManualSvc()">Далі →</button>
  `;
}

function confirmManualSvc(){
  const name = document.getElementById("manual-svc").value.trim();
  const price = document.getElementById("manual-price").value.trim();
  if(!name||!price){alert("Заповніть всі поля");return;}
  newOrder.items[currentItemIndex].services = "📝 " + name;
  newOrder.items[currentItemIndex].total = parseInt(price).toLocaleString("uk-UA") + " ₴";
  renderItemsList();
}

function goToPrice(){
  if(!newOrder.items[currentItemIndex].services){alert("Оберіть послугу");return;}
  const dept = newOrder.items[currentItemIndex].dept;
  const showExtra = dept==="cleaning"||dept==="painting";
  document.getElementById("modal-body").innerHTML = `
    <div style="display:flex;flex-direction:column;gap:14px">
      <div>
        <div class="m-section-title" style="margin-bottom:6px">Кількість (${newOrder.items[currentItemIndex].typeLabel==="Взуття"?"пар":"шт."})</div>
        <div style="display:flex;gap:8px" id="qty-btns">
          ${[1,2,3].map(n=>`<button class="filter-btn" style="flex:1;padding:10px;font-size:16px" onclick="selectQty(${n},this)">${n}</button>`).join("")}
          <button class="filter-btn" style="flex:1;padding:10px" onclick="selectQty(0,this)">Інше</button>
        </div>
      </div>
      <div id="manual-qty-wrap" style="display:none">
        <div class="m-section-title" style="margin-bottom:6px">Введіть кількість</div>
        <input type="number" id="manual-qty" placeholder="4" style="width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:8px;font-size:13px;font-family:inherit;background:var(--bg)">
      </div>
      <div>
        <div class="m-section-title" style="margin-bottom:6px">Вартість (₴)</div>
        <input type="number" id="no-price" placeholder="1400" style="width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:8px;font-size:13px;font-family:inherit;background:var(--bg)">
      </div>
      ${showExtra ? `<div>
        <div class="m-section-title" style="margin-bottom:6px">Додатковий колір або матеріал?</div>
        <div style="display:flex;gap:8px">
          <button class="filter-btn" id="extra-yes" onclick="toggleExtra(true)" style="flex:1;padding:9px">Так — +200 ₴</button>
          <button class="filter-btn active" id="extra-no" onclick="toggleExtra(false)" style="flex:1;padding:9px">Ні</button>
        </div>
      </div>` : ""}
    </div>
  `;
  newOrder.items[currentItemIndex].extra200 = false;
  document.getElementById("modal-footer").innerHTML = `
    <button class="btn" onclick="goToService()">← Назад</button>
    <button class="btn btn-primary" onclick="confirmItem()">Додати виріб</button>
  `;
  const autoPrice = newOrder.items[currentItemIndex]._autoPrice;
  if(autoPrice){
    const priceInput = document.getElementById("no-price");
    if(priceInput) priceInput.value = autoPrice;
  }
}

function selectQty(n, btn){
  document.querySelectorAll("#qty-btns .filter-btn").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById("manual-qty-wrap").style.display = n===0?"block":"none";
  if(n>0) newOrder.items[currentItemIndex]._qty = n;
}

function toggleExtra(yes){
  newOrder.items[currentItemIndex].extra200 = yes;
  document.getElementById("extra-yes").classList.toggle("active",yes);
  document.getElementById("extra-no").classList.toggle("active",!yes);
}

function confirmItem(){
  const price = parseInt(document.getElementById("no-price").value||"0");
  if(!price){alert("Введіть вартість");return;}
  const extra = newOrder.items[currentItemIndex].extra200 ? 200 : 0;
  const total = price + extra;
  newOrder.items[currentItemIndex].total = total.toLocaleString("uk-UA") + " ₴";
  renderItemsList();
}

function goStep3(){
  document.getElementById("modal-body").innerHTML = `
    <div style="display:flex;flex-direction:column;gap:14px">
      <div>
        <div class="m-section-title" style="margin-bottom:8px">Тип оплати</div>
        <div style="display:flex;gap:8px" id="pay-btns">
          <button class="filter-btn" style="flex:1;padding:10px" onclick="selectPay('Передоплата',this)">💳 Передоплата</button>
          <button class="filter-btn" style="flex:1;padding:10px" onclick="selectPay('Післяоплата',this)">📦 Післяоплата</button>
        </div>
      </div>
      <div id="prepay-wrap" style="display:none">
        <div class="m-section-title" style="margin-bottom:6px">Сума передоплати</div>
        <input type="number" id="prepay-amount" placeholder="500" style="width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:8px;font-size:13px;font-family:inherit;background:var(--bg)">
      </div>
      <div>
        <div class="m-section-title" style="margin-bottom:8px">Термін виконання</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap" id="deadline-btns">
          <button class="filter-btn" onclick="selectDeadline('⚡ Терміново',this)">⚡ Терміново</button>
          <button class="filter-btn" onclick="selectDeadline('Без терміну',this)">🕐 Без терміну</button>
          <button class="filter-btn" onclick="selectDeadline('date',this)">📅 Вказати дату</button>
        </div>
        <input type="text" id="deadline-date" placeholder="10.06 або п'ятниця" style="display:none;width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:8px;font-size:13px;font-family:inherit;background:var(--bg);margin-top:8px">
      </div>
    </div>
  `;
  document.getElementById("modal-footer").innerHTML = `
    <button class="btn" onclick="renderItemsList()">← Назад</button>
    <button class="btn btn-primary" onclick="submitOrder()">Оформити замовлення</button>
  `;
}

function selectPay(type, btn){
  newOrder.payment = type;
  document.querySelectorAll("#pay-btns .filter-btn").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById("prepay-wrap").style.display = type==="Передоплата"?"block":"none";
}

function selectDeadline(val, btn){
  document.querySelectorAll("#deadline-btns .filter-btn").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");
  const dateInput = document.getElementById("deadline-date");
  if(val==="date"){
    dateInput.style.display="block";
    newOrder.deadline = "";
  } else {
    dateInput.style.display="none";
    newOrder.deadline = val;
  }
}

async function submitOrder(){
  if(!newOrder.payment){alert("Оберіть тип оплати");return;}
  if(!newOrder.deadline){
    const dateVal = document.getElementById("deadline-date")?.value.trim();
    if(!dateVal){alert("Вкажіть термін виконання");return;}
    newOrder.deadline = dateVal;
  }
  if(newOrder.payment==="Передоплата"){
    const amount = document.getElementById("prepay-amount")?.value;
    if(amount) newOrder.payment = "Передоплата: " + parseInt(amount).toLocaleString("uk-UA") + " ₴";
  }

  const now = new Date();
  const pad = n=>String(n).padStart(2,"0");
  const dateStr = `${pad(now.getDate())}.${pad(now.getMonth()+1)}.${now.getFullYear()} ${pad(now.getHours())}:${pad(now.getMinutes())}`;

  const counter = ORDERS.length + 1;
  const orderNum = "RW-" + String(counter).padStart(4,"0");

  const payload = {
    order_num: orderNum,
    date: dateStr,
    manager: newOrder.manager,
    client: newOrder.client,
    phone: newOrder.phone,
    payment: newOrder.payment,
    deadline: newOrder.deadline,
    items: newOrder.items.map((item,i) => ({
      num: orderNum + "-" + (i+1),
      type: item.typeLabel,
      brand: item.brand,
      services: item.services,
      total: item.total
    }))
  };

  document.getElementById("modal-body").innerHTML = `<div style="text-align:center;padding:32px;color:var(--muted);font-size:13px">Збереження...</div>`;
  document.getElementById("modal-footer").innerHTML = "";

  try {
    await fetch(API_URL, {
      method: "POST",
      mode: "no-cors",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });
    setTimeout(()=>{
      closeModal();
      loadData();
    }, 1500);
  } catch(e) {
    document.getElementById("modal-body").innerHTML = `<div style="text-align:center;padding:32px;color:#a33030;font-size:13px">Помилка збереження. Перевірте підключення.</div>`;
  }
}


function printPlan(){
  const q=(document.getElementById("search-input")?.value||"").toLowerCase();
  const filtered=ORDERS.filter(o=>{
    const st=getStatus(o["Номер замовлення"]);
    const mf=currentFilter==="all"||st===currentFilter;
    const mm=currentManager==="all"||o["Приймальник"]===currentManager;
    const mq=!q||o["Ім'я клієнта"].toLowerCase().includes(q)||o["Номер замовлення"].toLowerCase().includes(q)||o["Телефон"].includes(q);
    return mf&&mm&&mq;
  });
  if(!filtered.length){alert("Немає замовлень для друку");return;}
  const now = new Date();
  const pad = n=>String(n).padStart(2,"0");
  const dateStr = `${pad(now.getDate())}.${pad(now.getMonth()+1)}.${now.getFullYear()}`;
  const filterLabel = {all:"Усі замовлення",new:"Нові",work:"В роботі",ready:"Готові до видачі",issued:"Видані"}[currentFilter]||"";

  const w=window.open("","_blank");
  w.document.write(`<html><head><title>План — ${dateStr}</title>
  <style>
    body{font-family:Arial,sans-serif;padding:20px;font-size:13px;color:#111;max-width:700px}
    h2{font-size:16px;margin-bottom:2px}
    .sub{color:#888;font-size:12px;margin-bottom:20px}
    .order-block{margin-bottom:16px;border:1px solid #e0d9d3;border-radius:8px;overflow:hidden}
    .order-head{background:#f5f0ea;padding:8px 12px;display:flex;justify-content:space-between;align-items:center}
    .order-num{font-weight:bold;color:#6B4F3A;font-size:13px}
    .order-client{font-size:13px}
    .order-deadline{font-size:11px;color:#888}
    .item-row{padding:8px 12px;border-top:1px solid #e0d9d3}
    .item-num{font-size:11px;color:#6B4F3A;font-weight:bold;margin-bottom:2px}
    .item-name{font-size:12px;font-weight:500;margin-bottom:2px}
    .item-svcs{font-size:11px;color:#888;line-height:1.6}
    .item-status{font-size:11px;color:#888;margin-top:2px}
    .footer{margin-top:20px;font-size:11px;color:#aaa;border-top:1px solid #eee;padding-top:10px;text-align:center}
    @media print{body{padding:10px}}
  </style></head><body>
  <h2>Rewise Studio — ${filterLabel}</h2>
  <div class="sub">Дата друку: ${dateStr} · Замовлень: ${filtered.length}</div>
  ${filtered.map(o=>{
    const items=ITEMS.filter(i=>i["Номер замовлення"]===o["Номер замовлення"]);
    const urgent=o["Термін"]==="Терміново"||o["Термін"]==="⚡ Терміново";
    return`<div class="order-block">
      <div class="order-head">
        <div>
          <span class="order-num">${o["Номер замовлення"]}</span>
          <span class="order-client" style="margin-left:10px">${o["Ім'я клієнта"]} · ${o["Телефон"]}</span>
        </div>
        <div class="order-deadline">${urgent?"⚡ ТЕРМІНОВО":o["Термін"]}</div>
      </div>
      ${items.map(item=>`<div class="item-row">
        <div class="item-num">${item["Номер изделия"]}</div>
        <div class="item-name">${item["Тип"]} — ${item["Бренд"]}</div>
        <div class="item-svcs">${item["Услуги"]}</div>
        <div class="item-status">${item["Статус"]} · ${item["Сумма"]}</div>
      </div>`).join("")}
    </div>`;
  }).join("")}
  <div class="footer">Rewise Studio · Одеса · @rewise.studio</div>
  <script>window.onload=()=>window.print()<\/script>
  </body></html>`);
}

</script>
</body>
</html>
