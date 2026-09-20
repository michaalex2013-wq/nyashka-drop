import io

with io.open('index.html', 'r', encoding='utf-8') as f:
    c = f.read()

print("[START] размер:", len(c))


def find_closing_brace(text, start_idx):
    """Находит закрывающую } для функции. start_idx — позиция открывающей {."""
    depth = 0
    i = start_idx
    n = len(text)
    while i < n:
        ch = text[i]
        # Однострочный комментарий
        if ch == '/' and i+1 < n and text[i+1] == '/':
            while i < n and text[i] != '\n':
                i += 1
            continue
        # Многострочный комментарий
        if ch == '/' and i+1 < n and text[i+1] == '*':
            i += 2
            while i < n-1 and not (text[i] == '*' and text[i+1] == '/'):
                i += 1
            i += 2
            continue
        # Строки
        if ch in ('"', "'", '`'):
            q = ch
            i += 1
            while i < n:
                if text[i] == '\\':
                    i += 2
                    continue
                if text[i] == q:
                    i += 1
                    break
                i += 1
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


# ============ 1. ЗАМЕНЯЕМ checkAdm НА SHA-256 ============
new_check = """var _cfg=null;
var _cfgPromise=fetch('config.json').then(function(r){return r.json();}).then(function(d){_cfg=d;}).catch(function(e){});
async function _sha256(str){
  var buf=new TextEncoder().encode(str);
  var h=await crypto.subtle.digest('SHA-256',buf);
  return Array.from(new Uint8Array(h)).map(function(b){return b.toString(16).padStart(2,'0');}).join('');
}
async function checkAdm(p){
  try{
    if(!_cfg) await _cfgPromise;
    if(!_cfg||!_cfg.h) return false;
    var h=await _sha256(p);
    if(h.length!==_cfg.h.length) return false;
    var d=0;
    for(var i=0;i<h.length;i++) d|=h.charCodeAt(i)^_cfg.h.charCodeAt(i);
    return d===0;
  }catch(e){return false;}
}
"""

# Ищем определение checkAdm
idx = c.find('function checkAdm(')
if idx == -1:
    print("[FAIL] checkAdm не найден")
else:
    open_idx = c.find('{', idx)
    close_idx = find_closing_brace(c, open_idx)
    if close_idx == -1:
        print("[FAIL] закрывающая } не найдена")
    else:
        c = c[:idx] + new_check + c[close_idx+1:]
        print("[OK] checkAdm -> SHA-256")

# ============ 2. ЗАМЕНЯЕМ showAdminPanel НА ASYNC ============
idx2 = c.find('function showAdminPanel(')
if idx2 == -1:
    print("[FAIL] showAdminPanel не найден")
else:
    open_idx2 = c.find('{', idx2)
    close_idx2 = find_closing_brace(c, open_idx2)
    if close_idx2 == -1:
        print("[FAIL] закрывающая } showAdminPanel не найдена")
    else:
        # Определяем уровень отступа
        line_start = c.rfind('\n', 0, idx2) + 1
        indent = ''
        for ch in c[line_start:idx2]:
            if ch in (' ', '\t'):
                indent += ch
            else:
                break

        new_sap = (
            "async function showAdminPanel(){\n"
            + indent + "  var r=_rate();\n"
            + indent + "  if(!r.ok){alert(r.msg);return;}\n"
            + indent + "  var pass=prompt('\\u041F\\u0430\\u0440\\u043E\\u043B\\u044C \\u0430\\u0434\\u043C\\u0438\\u043D\\u0438\\u0441\\u0442\\u0440\\u0430\\u0442\\u043E\\u0440\\u0430:');\n"
            + indent + "  if(pass===null) return;\n"
            + indent + "  var ok=await checkAdm(pass);\n"
            + indent + "  if(ok){\n"
            + indent + "    _ok();\n"
            + indent + "    document.getElementById('admin-panel').style.display='block';\n"
            + indent + "    if(typeof loadWithdrawals==='function') loadWithdrawals();\n"
            + indent + "  } else {\n"
            + indent + "    var locked=_fail();\n"
            + indent + "    if(locked) alert('\\uD83D\\uDEAB 3 \\u043D\\u0435\\u0432\\u0435\\u0440\\u043D\\u044B\\u0435 \\u043F\\u043E\\u043F\\u044B\\u0442\\u043A\\u0438. \\u0411\\u043B\\u043E\\u043A 60 \\u0441\\u0435\\u043A.');\n"
            + indent + "    else { var l=_getLock(); alert('\\u041D\\u0435\\u0432\\u0435\\u0440\\u043D\\u044B\\u0439 \\u043F\\u0430\\u0440\\u043E\\u043B\\u044C! \\u041E\\u0441\\u0442\\u0430\\u043B\\u043E\\u0441\\u044C: '+(3-(l.t||0))); }\n"
            + indent + "  }\n"
            + indent + "}"
        )
        c = c[:idx2] + new_sap + c[close_idx2+1:]
        print("[OK] showAdminPanel -> async")

# ============ 3. Убираем base64 пароль ============
before = c.count("MTcyNzN2NzI")
c = c.replace("const _A1='MTcy';const _A2='NzN2';const _A3='NzI=';", "")
c = c.replace("const _A1 = 'MTcy';", "")
c = c.replace("const _A2 = 'NzN2';", "")
c = c.replace("const _A3 = 'NzI=';", "")
c = c.replace("atob(_A1+_A2+_A3)", "''")
print("[OK] base64 убран, было вхождений:", before)

# ============ 4. ФИНАЛЬНАЯ ПРОВЕРКА СИНТАКСИСА ============
opens = c.count('{')
closes = c.count('}')
print("[CHECK] { :", opens, " } :", closes, " diff:", opens - closes)

# Сохраняем
with io.open('index.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("")
print("=== ГОТОВО ===")
print("17273672 в коде:", c.count("17273672"))
print("base64 new:", c.count("MTcyNzN2NzI"))
print("base64 old:", c.count("NTAwNTI5MTY"))
