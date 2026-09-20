import io, re

with io.open('index.html', 'r', encoding='utf-8') as f:
    c = f.read()

print("Размер файла:", len(c))
print("")

# ============ 1. ХЕЛПЕРЫ БЕЗОПАСНОСТИ ============
helpers = """const _A1='MTcy';const _A2='NzN2';const _A3='NzI=';
function _getLock(){try{return JSON.parse(localStorage.getItem('nd_al_v1'))||{t:0,u:0};}catch(e){return{t:0,u:0};}}
function _setLock(v){try{localStorage.setItem('nd_al_v1',JSON.stringify(v));}catch(e){}}
function _rate(){const l=_getLock();const n=Date.now();if(l.u>n){const s=Math.ceil((l.u-n)/1000);return{ok:false,msg:'\\uD83D\\uDEAB \\u0411\\u043B\\u043E\\u043A! \\u041F\\u043E\\u0434\\u043E\\u0436\\u0434\\u0438 '+s+' \\u0441\\u0435\\u043A.'};}return{ok:true};}
function _fail(){const l=_getLock();l.t=(l.t||0)+1;if(l.t>=3){l.u=Date.now()+60000;l.t=0;_setLock(l);return true;}_setLock(l);return false;}
function _ok(){_setLock({t:0,u:0});}
function checkAdm(p){
  try{
    const c=atob(_A1+_A2+_A3);
    if(!p||p.length!==c.length) return false;
    let d=0;
    for(let i=0;i<p.length;i++) d|=p.charCodeAt(i)^c.charCodeAt(i);
    return d===0;
  }catch(e){return false;}
}
"""

# Вставим хелперы в начало первого <script>
idx = c.find('<script>')
if idx != -1:
    # пропускаем комментарии/пустые строки до первой строки кода
    insert_point = idx + len('<script>')
    c = c[:insert_point] + "\n" + helpers + c[insert_point:]
    print("[OK] Хелперы добавлены в <script>")
else:
    print("[FAIL] Не найден <script>")

# ============ 2. ЗАМЕНА СТАРОЙ ПРОВЕРКИ ПАРОЛЯ ============
# Заменяем ВСЕ проверки вида pass === atob('NTAwNTI5MTY=') на checkAdm(pass)

# 2a. Стрелочная функция (v3)
c, n = re.subn(
    r"const\s+checkAdm\s*=\s*p\s*=>\s*\{[^}]*atob\('NTAwNTI5MTY='\)[^}]*\}\s*;",
    "// checkAdm определяется выше",
    c
)
print(f"[OK] Заменено checkAdm: {n}")

# 2b. Обычная функция checkAdminPass
c, n = re.subn(
    r"function\s+checkAdminPass\s*\([^)]*\)\s*\{[^}]*atob\('NTAwNTI5MTY='\)[^}]*\}",
    "// checkAdminPass (заменён на checkAdm)",
    c
)
print(f"[OK] Заменено checkAdminPass: {n}")

# 2c. Все прямые вызовы atob('NTAwNTI5MTY=') в проверках
c = c.replace("pass === atob('NTAwNTI5MTY=')", "checkAdm(pass)")
c = c.replace("p === atob('NTAwNTI5MTY=')", "checkAdm(p)")
c = c.replace("pass==atob('NTAwNTI5MTY=')", "checkAdm(pass)")
print("[OK] Прямые вызовы atob заменены")

# 2d. Проверим, не остался ли где-то сам пароль в открытом виде как строка
c = c.replace("atob('NTAwNTI5MTY=')", "atob(_A1+_A2+_A3)")
c = c.replace('atob("NTAwNTI5MTY=")', "atob(_A1+_A2+_A3)")
print("[OK] Все atob переписаны на сборку из 3 частей")

# ============ 3. ЗАЩИТА showAdminPanel ОТ БРУТФОРСА ============
# Ищем любую функцию с именем showAdminPanel и заменяем целиком
pattern = r"function\s+showAdminPanel\s*\(\s*\)\s*\{[\s\S]*?\n(\s{0,8})\}"
new_sap = """function showAdminPanel(){
            const r=_rate();
            if(!r.ok){alert(r.msg);return;}
            const pass=prompt('\\u041F\\u0430\\u0440\\u043E\\u043B\\u044C \\u0430\\u0434\\u043C\\u0438\\u043D\\u0438\\u0441\\u0442\\u0440\\u0430\\u0442\\u043E\\u0440\\u0430:');
            if(pass===null) return;
            if(checkAdm(pass)){
                _ok();
                document.getElementById('admin-panel').style.display='block';
                if(typeof loadWithdrawals==='function') loadWithdrawals();
            } else {
                const locked=_fail();
                if(locked) alert('\\uD83D\\uDEAB 3 \\u043D\\u0435\\u0432\\u0435\\u0440\\u043D\\u044B\\u0435 \\u043F\\u043E\\u043F\\u044B\\u0442\\u043A\\u0438. \\u0411\\u043B\\u043E\\u043A\\u0438\\u0440\\u043E\\u0432\\u043A\\u0430 \\u043D\\u0430 60 \\u0441\\u0435\\u043A.');
                else { const l=_getLock(); alert('\\u041D\\u0435\\u0432\\u0435\\u0440\\u043D\\u044B\\u0439 \\u043F\\u0430\\u0440\\u043E\\u043B\\u044C! \\u041E\\u0441\\u0442\\u0430\\u043B\\u043E\\u0441\\u044C: '+(3-(l.t||0))); }
            }
        }"""

matches = list(re.finditer(pattern, c))
if matches:
    # Заменяем только последнее вхождение (обычно это определение, а не вызов)
    m = matches[-1]
    c = c[:m.start()] + new_sap + c[m.end():]
    print(f"[OK] showAdminPanel заменён ({len(matches)} найдено)")
else:
    print("[WARN] showAdminPanel не найден - возможно другая версия")

# ============ 4. СПРЯТАТЬ КНОПКУ АДМИНА ============
# Ищем кнопку "Админ-панель" и делаем её невидимой
patterns_hide = [
    (r'<button[^>]*onclick="showAdminPanel\(\)"[^>]*>Админ-панель</button>',
     '<button onclick="showAdminPanel()" style="display:none;position:absolute;left:-9999px">.</button>'),
    (r'<button[^>]*onclick="showAdminPanel\(\)"[^>]*>[^<]*[Аа]дмин[^<]*</button>',
     '<button onclick="showAdminPanel()" style="display:none;position:absolute;left:-9999px">.</button>'),
]
for pat, rep in patterns_hide:
    c, n = re.subn(pat, rep, c)
    if n:
        print(f"[OK] Кнопка админа спрятана ({n})")
        break
else:
    print("[WARN] Кнопка админа не найдена - скрываю через CSS")

# 4b. Дополнительно скрываем через CSS
css_hide = """
<style>
#admin-panel{display:none !important}
[onclick*="showAdminPanel"]{display:none !important;position:absolute !important;left:-9999px !important}
</style>
"""
last_head = c.rfind('</head>')
if last_head != -1:
    c = c[:last_head] + css_hide + c[last_head:]
    print("[OK] CSS-скрытие кнопки админа добавлено")

# ============ 5. ANTI-DEVTOOLS ============
anti = '''
<script>
(function(){
  'use strict';
  var _c=0,_t=null;
  // Секретный вход: 5 тапов по аватару
  document.addEventListener('click',function(e){
    var el=e.target;
    var isAvatar=el && (el.classList.contains('profile-btn')||el.classList.contains('avatar-btn')||el.classList.contains('user-chip'));
    if(isAvatar){
      _c++;clearTimeout(_t);
      _t=setTimeout(function(){_c=0;},1500);
      if(_c>=5){_c=0;if(typeof showAdminPanel==='function') showAdminPanel();}
    }
  },true);

  // Блок горячих клавиш
  document.addEventListener('keydown',function(e){
    var k=e.key||'';
    if(k==='F12'||
       (e.ctrlKey&&e.shiftKey&&(k==='I'||k==='i'||k==='J'||k==='j'||k==='C'||k==='c'))||
       (e.ctrlKey&&(k==='u'||k==='U'))||
       (e.metaKey&&e.altKey&&(k==='I'||k==='i'||k==='J'||k==='j'))){
      e.preventDefault();e.stopPropagation();return false;
    }
  },true);

  // Блок правого клика
  document.addEventListener('contextmenu',function(e){e.preventDefault();return false;});

  // Детект DevTools
  var _bad=false;
  function _kill(){
    document.body.innerHTML='<div style="position:fixed;inset:0;background:#07030d;color:#ef4444;display:flex;align-items:center;justify-content:center;flex-direction:column;z-index:2147483647;font-family:Arial,sans-serif;text-align:center;padding:20px"><div style="font-size:5rem">&#128683;</div><h1 style="font-size:1.6rem;margin:18px 0;color:#fff;letter-spacing:2px">DEVTOOLS</h1><p style="opacity:.7;font-size:.9rem;max-width:340px">&#1047;&#1072;&#1082;&#1088;&#1086;&#1081; &#1080;&#1085;&#1089;&#1090;&#1088;&#1091;&#1084;&#1077;&#1085;&#1090;&#1099; &#1088;&#1072;&#1079;&#1088;&#1072;&#1073;&#1086;&#1090;&#1095;&#1080;&#1082;&#1072;</p></div>';
    setTimeout(function(){location.reload();},2500);
  }
  setInterval(function(){
    var wd=window.outerWidth-window.innerWidth;
    var hd=window.outerHeight-window.innerHeight;
    if(wd>220||hd>220){_bad=true;}
  },1200);
  setInterval(function(){if(_bad){_bad=false;_kill();}},1400);

  // Debugger-ловушка
  setInterval(function(){
    var t0=performance.now();
    try{(function(){return false;}).constructor('debugger')();}catch(e){}
    if(performance.now()-t0>150){_bad=true;}
  },4500);

  // Предупреждение в консоли
  try{
    console.log('%c\u26D4 STOP!','color:#ef4444;font-size:44px;font-weight:900;');
    console.log('%c\u0417\u0430\u0449\u0438\u0449\u0451\u043d\u043d\u0430\u044f \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u0430.','color:#fbbf24;font-size:16px;');
  }catch(e){}
})();
</script>
'''
last_body = c.rfind('</body>')
if last_body != -1:
    c = c[:last_body] + anti + '\n' + c[last_body:]
    print("[OK] Anti-DevTools установлен")
else:
    print("[FAIL] Не найден </body>")

# ============ СОХРАНЕНИЕ ============
with io.open('index.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("")
print("========================================")
print(" ГОТОВО! Размер:", len(c))
print(" Пароль: 17273672")
print(" Секретный вход: 5 тапов по аватару")
print("========================================")
